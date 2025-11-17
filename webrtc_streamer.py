"""
WebRTC Video Streamer for Raspberry Pi
=====================================

Provides ultra-low-latency video streaming (100-300ms) using WebRTC.

Features:
- Support for USB cameras and PiCamera2
- H.264 encoding for browser compatibility
- Multiple simultaneous viewers (configurable via config.json)
- Efficient media relay (single camera → multiple viewers)
- Automatic ICE candidate exchange for NAT traversal
- Graceful connection management and cleanup

Architecture:
- CameraVideoTrack: Captures frames from camera and provides to WebRTC
- WebRTCStreamer: Manages peer connections for all viewers
- MediaRelay: Efficiently shares single camera stream with multiple viewers

Configuration (config.json):
{
  "video": {
    "enabled": true,
    "width": 1280,
    "height": 720,
    "fps": 30,
    "bitrate": 1500000,
    "camera_type": "usb"  // or "picamera2"
  },
  "webrtc": {
    "stun_servers": [...],
    "max_viewers": 5
  }
}
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Callable
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, VideoStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaRelay
from av import VideoFrame
import cv2
import time
from fractions import Fraction

logger = logging.getLogger(__name__)


class CameraVideoTrack(VideoStreamTrack):
    """
    Video track that captures frames from a camera (USB or PiCamera2).
    Provides H.264 encoded video stream for WebRTC.

    This class extends aiortc's VideoStreamTrack to provide camera frames.
    It handles:
    - Camera initialization (USB via OpenCV or PiCamera2)
    - Asynchronous frame capture (non-blocking)
    - Frame format conversion (BGR→RGB for OpenCV)
    - Timestamp management for smooth playback
    - Graceful fallback on capture failures

    Usage:
        track = CameraVideoTrack(camera_type="usb", width=1280, height=720, fps=30)
        # Track will be added to RTCPeerConnection
        pc.addTrack(track)
    """

    def __init__(self, camera_type: str = "usb", width: int = 1280, height: int = 720, fps: int = 30):
        super().__init__()
        self.camera_type = camera_type
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        self._timestamp = 0
        self._start = time.time()  # aiortc expects _start, not _start_time
        self._frame_count = 0

        logger.info(f"Initializing camera: type={camera_type}, resolution={width}x{height}, fps={fps}")
        self._initialize_camera()

    def _initialize_camera(self):
        """Initialize the camera based on type (USB or PiCamera2)."""
        if self.camera_type == "usb":
            self._initialize_usb_camera()
        elif self.camera_type == "picamera2":
            self._initialize_picamera2()
        else:
            raise ValueError(f"Unsupported camera type: {self.camera_type}")

    def _initialize_usb_camera(self):
        """Initialize USB camera using OpenCV."""
        print(f"📷 Opening USB camera at /dev/video0...")
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print(f"❌ Failed to open USB camera!")
            raise RuntimeError("Failed to open USB camera")

        print(f"✅ USB camera opened successfully")

        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        # Verify settings
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))

        print(f"✅ USB camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")
        logger.info(f"USB camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")

    def _initialize_picamera2(self):
        """Initialize Raspberry Pi Camera using PiCamera2."""
        try:
            from picamera2 import Picamera2
            from picamera2.configuration import CameraConfiguration

            self.cap = Picamera2()
            config = self.cap.create_video_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"}
            )
            self.cap.configure(config)
            self.cap.start()

            # Warm-up time
            time.sleep(2)
            logger.info(f"PiCamera2 initialized: {self.width}x{self.height}")

        except ImportError:
            raise RuntimeError("picamera2 library not installed. Install with: sudo apt install python3-picamera2")

    async def recv(self):
        """
        Receive the next video frame.
        Called by aiortc to get frames for the WebRTC stream.
        """
        self._frame_count += 1

        # Log every 30 frames (once per second at 30fps)
        if self._frame_count % 30 == 1:
            print(f"📹 Frame {self._frame_count} requested from camera")

        try:
            # Calculate presentation timestamp
            pts, time_base = await self.next_timestamp()

            # Capture frame from camera
            frame = await self._capture_frame()

            if frame is None:
                print(f"⚠️  Frame {self._frame_count}: Failed to capture from camera, sending blank frame")
                logger.warning("Failed to capture frame from camera")
                # Return a blank frame to keep stream alive
                frame = self._create_blank_frame()
            elif self._frame_count % 30 == 1:
                print(f"✅ Frame {self._frame_count} captured successfully")

            frame.pts = pts
            frame.time_base = time_base

            return frame
        except Exception as e:
            print(f"❌ CRITICAL ERROR in recv() at frame {self._frame_count}: {e}")
            import traceback
            traceback.print_exc()
            # Return a blank frame to prevent stream failure
            frame = self._create_blank_frame()
            pts, time_base = await self.next_timestamp()
            frame.pts = pts
            frame.time_base = time_base
            return frame

    async def _capture_frame(self) -> Optional[VideoFrame]:
        """Capture a frame from the camera asynchronously."""
        loop = asyncio.get_event_loop()

        if self.camera_type == "usb":
            # Run OpenCV capture in executor to avoid blocking
            try:
                ret, img = await loop.run_in_executor(None, self.cap.read)
                if not ret:
                    print(f"❌ cap.read() returned False - camera read failed")
                    return None

                if img is None:
                    print(f"❌ cap.read() returned None image")
                    return None

                # Convert BGR (OpenCV) to RGB (required by VideoFrame)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Create VideoFrame from numpy array
                frame = VideoFrame.from_ndarray(img, format="rgb24")
                return frame
            except Exception as e:
                print(f"❌ Error capturing frame: {e}")
                return None

        elif self.camera_type == "picamera2":
            # Capture from PiCamera2
            img = await loop.run_in_executor(None, self.cap.capture_array)

            # Create VideoFrame from numpy array
            frame = VideoFrame.from_ndarray(img, format="rgb24")
            return frame

        return None

    def _create_blank_frame(self) -> VideoFrame:
        """Create a blank frame as fallback."""
        import numpy as np
        blank = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        return VideoFrame.from_ndarray(blank, format="rgb24")

    def stop(self):
        """Stop the camera and release resources."""
        if self.cap:
            if self.camera_type == "usb":
                self.cap.release()
            elif self.camera_type == "picamera2":
                self.cap.stop()
            self.cap = None
        logger.info("Camera stopped")


class WebRTCStreamer:
    """
    Manages WebRTC peer connections for live video streaming.
    Supports multiple simultaneous viewers with a media relay for efficiency.

    This class is the main entry point for WebRTC streaming on the Pi.
    It handles:
    - Creating and managing multiple RTCPeerConnections (one per viewer)
    - SDP offer/answer negotiation
    - ICE candidate exchange for NAT traversal
    - Media relay (shares one camera track across multiple viewers)
    - Viewer limit enforcement
    - Connection state monitoring
    - Graceful cleanup

    Typical Flow:
        1. Viewer sends SDP offer → handle_offer()
        2. Pi creates answer and sends back
        3. ICE candidates exchanged → add_ice_candidate()
        4. WebRTC connection established (P2P)
        5. Video streams directly to viewer's browser
        6. On disconnect → close_peer_connection()

    Usage:
        streamer = WebRTCStreamer(
            config=config,
            on_ice_candidate=callback_function
        )
        answer = await streamer.handle_offer(viewer_id, offer_sdp)
        await streamer.add_ice_candidate(viewer_id, candidate_data)
    """

    def __init__(self, config: dict, on_ice_candidate: Optional[Callable] = None):
        """
        Initialize WebRTC streamer.

        Args:
            config: Video and WebRTC configuration dictionary
            on_ice_candidate: Callback function when ICE candidates are generated
        """
        self.config = config
        self.on_ice_candidate_callback = on_ice_candidate

        # Peer connections: viewer_id -> RTCPeerConnection
        self.peer_connections: Dict[str, RTCPeerConnection] = {}

        # Media relay for efficient multi-viewer streaming
        self.relay = MediaRelay()

        # Single camera track shared across all viewers
        self.camera_track: Optional[CameraVideoTrack] = None

        # STUN/TURN configuration
        self.ice_servers = self._get_ice_servers()

        logger.info(f"WebRTC Streamer initialized with config: {config}")

    def _get_ice_servers(self) -> list:
        """Get ICE server configuration for NAT traversal."""
        stun_servers = self.config.get("webrtc", {}).get("stun_servers", [
            "stun:stun.l.google.com:19302",
            "stun:stun1.l.google.com:19302"
        ])

        # Create RTCIceServer objects (not dicts)
        ice_servers = [RTCIceServer(urls=server) for server in stun_servers]

        # Add TURN servers if configured
        turn_servers = self.config.get("webrtc", {}).get("turn_servers", [])
        for turn in turn_servers:
            ice_servers.append(RTCIceServer(
                urls=turn["url"],
                username=turn.get("username"),
                credential=turn.get("credential")
            ))

        logger.info(f"ICE servers configured: {[str(s.urls) for s in ice_servers]}")
        return ice_servers

    def _initialize_camera(self):
        """Initialize the camera track if not already started."""
        if self.camera_track is None:
            video_config = self.config.get("video", {})
            camera_type = video_config.get("camera_type", "usb")
            width = video_config.get("width", 1280)
            height = video_config.get("height", 720)
            fps = video_config.get("fps", 30)

            print(f"📸 Initializing camera: type={camera_type}, {width}x{height}@{fps}fps")

            self.camera_track = CameraVideoTrack(
                camera_type=camera_type,
                width=width,
                height=height,
                fps=fps
            )
            print(f"✅ Camera track initialized successfully")
            logger.info("Camera track initialized")
        else:
            print(f"📸 Camera already initialized, reusing existing track")

    async def handle_offer(self, viewer_id: str, offer_sdp: dict) -> dict:
        """
        Handle an SDP offer from a viewer and create an answer.

        Args:
            viewer_id: Unique identifier for the viewer
            offer_sdp: SDP offer from the viewer's browser

        Returns:
            SDP answer dictionary
        """
        logger.info(f"Handling offer from viewer: {viewer_id}")

        # Check viewer limit
        max_viewers = self.config.get("webrtc", {}).get("max_viewers", 5)
        if len(self.peer_connections) >= max_viewers:
            logger.warning(f"Viewer limit reached ({max_viewers}). Rejecting connection from {viewer_id}")
            raise RuntimeError(f"Maximum viewers ({max_viewers}) reached")

        # Initialize camera if not started
        self._initialize_camera()

        # Create peer connection with proper RTCConfiguration object
        config = RTCConfiguration(iceServers=self.ice_servers)
        pc = RTCPeerConnection(configuration=config)
        self.peer_connections[viewer_id] = pc

        # Add video track (relayed from camera)
        relayed_track = self.relay.subscribe(self.camera_track)
        pc.addTrack(relayed_track)

        # Set up ICE candidate handler
        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            if candidate and self.on_ice_candidate_callback:
                await self.on_ice_candidate_callback(viewer_id, candidate)

        # Set up connection state change handler
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print(f"🔗 Connection state for {viewer_id}: {pc.connectionState}")
            logger.info(f"Connection state for {viewer_id}: {pc.connectionState}")
            if pc.connectionState == "failed" or pc.connectionState == "closed":
                await self.close_peer_connection(viewer_id)

        # Set remote description (the offer)
        offer = RTCSessionDescription(sdp=offer_sdp["sdp"], type=offer_sdp["type"])
        await pc.setRemoteDescription(offer)

        # Create answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        logger.info(f"Created answer for viewer: {viewer_id}")

        return {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }

    async def add_ice_candidate(self, viewer_id: str, candidate_data: dict):
        """
        Add an ICE candidate from a viewer.

        Args:
            viewer_id: Unique identifier for the viewer
            candidate_data: ICE candidate data from the viewer
        """
        pc = self.peer_connections.get(viewer_id)
        if not pc:
            logger.warning(f"No peer connection found for viewer: {viewer_id}")
            return

        try:
            candidate = RTCIceCandidate(
                sdpMid=candidate_data.get("sdpMid"),
                sdpMLineIndex=candidate_data.get("sdpMLineIndex"),
                candidate=candidate_data.get("candidate")
            )
            await pc.addIceCandidate(candidate)
            logger.debug(f"Added ICE candidate for viewer: {viewer_id}")
        except Exception as e:
            logger.error(f"Error adding ICE candidate for {viewer_id}: {e}")

    async def close_peer_connection(self, viewer_id: str):
        """
        Close a peer connection for a specific viewer.

        Args:
            viewer_id: Unique identifier for the viewer
        """
        pc = self.peer_connections.get(viewer_id)
        if pc:
            await pc.close()
            del self.peer_connections[viewer_id]
            logger.info(f"Closed peer connection for viewer: {viewer_id}")

            # Stop camera if no more viewers
            if len(self.peer_connections) == 0:
                self.stop_camera()

    def stop_camera(self):
        """Stop the camera track and release resources."""
        if self.camera_track:
            self.camera_track.stop()
            self.camera_track = None
            logger.info("Camera stopped - no active viewers")

    async def close_all_connections(self):
        """Close all peer connections and stop the camera."""
        logger.info("Closing all peer connections")

        # Close all peer connections
        for viewer_id in list(self.peer_connections.keys()):
            await self.close_peer_connection(viewer_id)

        # Stop camera
        self.stop_camera()

    def get_active_viewers(self) -> list:
        """Get list of active viewer IDs."""
        return list(self.peer_connections.keys())

    def get_connection_state(self, viewer_id: str) -> Optional[str]:
        """Get connection state for a specific viewer."""
        pc = self.peer_connections.get(viewer_id)
        return pc.connectionState if pc else None
