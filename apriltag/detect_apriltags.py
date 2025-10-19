#!/usr/bin/env python3
"""
AprilTag Detection using PiCamera
Detects AprilTag markers in real-time from Raspberry Pi Camera
"""

import cv2
import numpy as np
from picamera2 import Picamera2
from dt_apriltags import Detector
import time

class AprilTagDetector:
    def __init__(self, camera_params=None, tag_family='tag36h11'):
        """
        Initialize AprilTag detector with camera

        Args:
            camera_params: Camera intrinsic parameters (fx, fy, cx, cy)
            tag_family: AprilTag family to detect (default: tag36h11)
        """
        # Initialize camera
        self.picam = Picamera2()

        # Configure camera for still capture
        config = self.picam.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        self.picam.configure(config)
        self.picam.start()

        # Wait for camera to warm up
        time.sleep(2)

        # Initialize AprilTag detector
        self.detector = Detector(
            families=tag_family,
            nthreads=4,
            quad_decimate=2.0,
            quad_sigma=0.0,
            refine_edges=1,
            decode_sharpening=0.25,
            debug=0
        )

        # Default camera parameters (approximate for Pi Camera)
        # These should be calibrated for accurate pose estimation
        if camera_params is None:
            self.camera_params = [500, 500, 320, 240]  # fx, fy, cx, cy
        else:
            self.camera_params = camera_params

    def detect_tags(self, image):
        """
        Detect AprilTags in the given image

        Args:
            image: RGB image array

        Returns:
            List of detected tags
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Detect tags
        tags = self.detector.detect(
            gray,
            estimate_tag_pose=True,
            camera_params=self.camera_params,
            tag_size=0.05  # Tag size in meters (adjust based on your tags)
        )

        return tags

    def draw_detections(self, image, tags):
        """
        Draw detected tags on the image

        Args:
            image: RGB image array
            tags: List of detected tags

        Returns:
            Image with drawn detections
        """
        img_with_detections = image.copy()

        for tag in tags:
            # Draw bounding box
            corners = tag.corners.astype(int)
            for i in range(4):
                pt1 = tuple(corners[i])
                pt2 = tuple(corners[(i + 1) % 4])
                cv2.line(img_with_detections, pt1, pt2, (0, 255, 0), 2)

            # Draw center
            center = tuple(tag.center.astype(int))
            cv2.circle(img_with_detections, center, 5, (0, 0, 255), -1)

            # Draw tag ID
            cv2.putText(
                img_with_detections,
                f"ID: {tag.tag_id}",
                (center[0] - 10, center[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 0),
                2
            )

        return img_with_detections

    def run_continuous(self, display=False, save_detections=False):
        """
        Run continuous detection loop

        Args:
            display: If True, display the image with detections
            save_detections: If True, save images with detections
        """
        print("Starting AprilTag detection... Press Ctrl+C to stop")

        try:
            while True:
                # Capture frame
                frame = self.picam.capture_array()

                # Detect tags
                tags = self.detect_tags(frame)

                # Print detection info
                if tags:
                    print(f"\n--- Detected {len(tags)} tag(s) ---")
                    for tag in tags:
                        print(f"Tag ID: {tag.tag_id}")
                        print(f"  Center: {tag.center}")
                        print(f"  Corners: {tag.corners}")
                        if tag.pose_R is not None:
                            print(f"  Rotation: {tag.pose_R}")
                            print(f"  Translation: {tag.pose_t}")

                # Draw and display/save
                if display or save_detections:
                    if tags:
                        img_with_detections = self.draw_detections(frame, tags)
                    else:
                        img_with_detections = frame

                    if save_detections and tags:
                        filename = f"detection_{int(time.time())}.jpg"
                        cv2.imwrite(filename, cv2.cvtColor(img_with_detections, cv2.COLOR_RGB2BGR))
                        print(f"Saved detection to {filename}")

                    if display:
                        cv2.imshow('AprilTag Detection', cv2.cvtColor(img_with_detections, cv2.COLOR_RGB2BGR))
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break

                time.sleep(0.1)  # Adjust detection rate

        except KeyboardInterrupt:
            print("\nStopping detection...")
        finally:
            self.cleanup()

    def detect_single(self, save_image=True):
        """
        Capture and detect tags in a single image

        Args:
            save_image: If True, save the image with detections

        Returns:
            List of detected tags
        """
        # Capture frame
        frame = self.picam.capture_array()

        # Detect tags
        tags = self.detect_tags(frame)

        # Print detection info
        print(f"Detected {len(tags)} tag(s)")
        for tag in tags:
            print(f"\nTag ID: {tag.tag_id}")
            print(f"  Center: {tag.center}")
            print(f"  Corners:\n{tag.corners}")

        # Save image with detections
        if save_image and tags:
            img_with_detections = self.draw_detections(frame, tags)
            filename = f"apriltag_detection_{int(time.time())}.jpg"
            cv2.imwrite(filename, cv2.cvtColor(img_with_detections, cv2.COLOR_RGB2BGR))
            print(f"\nSaved detection to {filename}")

        return tags

    def cleanup(self):
        """Clean up resources"""
        self.picam.stop()
        cv2.destroyAllWindows()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='AprilTag Detection with PiCamera')
    parser.add_argument('--mode', choices=['single', 'continuous'], default='single',
                        help='Detection mode: single shot or continuous')
    parser.add_argument('--display', action='store_true',
                        help='Display detections (continuous mode only)')
    parser.add_argument('--save', action='store_true',
                        help='Save images with detections')
    parser.add_argument('--family', default='tag36h11',
                        help='AprilTag family (default: tag36h11)')

    args = parser.parse_args()

    # Create detector
    detector = AprilTagDetector(tag_family=args.family)

    # Run detection
    if args.mode == 'single':
        detector.detect_single(save_image=args.save)
        detector.cleanup()
    else:
        detector.run_continuous(display=args.display, save_detections=args.save)


if __name__ == '__main__':
    main()
