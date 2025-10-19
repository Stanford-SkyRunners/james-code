# AprilTag Detection with PiCamera

Python program for detecting AprilTag markers using the Raspberry Pi Camera.

## Features

- Real-time AprilTag detection using PiCamera
- Support for multiple tag families (default: tag36h11)
- Single shot or continuous detection modes
- Pose estimation (position and orientation)
- Visual overlay of detected tags
- Save detection results to images

## Installation

1. Install system dependencies:
```bash
sudo apt-get update
sudo apt-get install libcap-dev python3-libcamera python3-picamera2
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt --break-system-packages
```

3. Make the script executable:
```bash
chmod +x detect_apriltags.py
```

## Usage

### Single Shot Detection

Capture one image and detect tags:
```bash
python detect_apriltags.py --mode single
```

Save the detection result:
```bash
python detect_apriltags.py --mode single --save
```

### Continuous Detection

Run continuous detection loop:
```bash
python detect_apriltags.py --mode continuous
```

Display detections in real-time with live video feed:
```bash
python detect_apriltags.py --mode continuous --display
```

Save all detections:
```bash
python detect_apriltags.py --mode continuous --save
```

#### Viewing Live Video Feed via SSH

To view the live video feed when SSH'd into the Raspberry Pi, you need X11 forwarding enabled:

**For Windows users:**

1. **Install MobaXterm** (recommended):
   - Download from: https://mobaxterm.mobatek.net/download.html
   - MobaXterm has built-in X server and handles X11 forwarding automatically
   - Simply connect to your Raspberry Pi using MobaXterm's SSH feature
   - The X server starts automatically

2. **Alternative - Use VcXsrv with Windows OpenSSH**:
   - Download and install VcXsrv: https://sourceforge.net/projects/vcxsrv/
   - Start VcXsrv (XLaunch) with "Multiple windows" and "Disable access control" checked
   - Edit `C:\Users\<your-username>\.ssh\config` and add:
     ```
     Host jamesraspberrypi
         ForwardX11 yes
         ForwardX11Trusted yes
     ```
   - Connect with: `ssh james@jamesraspberrypi`

**For Linux/Mac users:**

Connect with X11 forwarding enabled:
```bash
ssh -X james@jamesraspberrypi
```

Or for trusted forwarding:
```bash
ssh -Y james@jamesraspberrypi
```

**Verify X11 forwarding is working:**
```bash
echo $DISPLAY
```
You should see something like `localhost:10.0`

Test with a simple X11 app:
```bash
xclock
```
If a clock window appears on your local machine, X11 forwarding is working correctly.

**Then run the detector with display:**
```bash
cd ~/skyrunners/apriltag
python3 detect_apriltags.py --mode continuous --display
```

The live video feed window will appear on your local machine, showing the camera feed with detected AprilTags highlighted. Press 'q' in the video window to quit.

### Options

- `--mode`: Choose between `single` or `continuous` detection
- `--display`: Show detections in a window (continuous mode only)
- `--save`: Save images with detected tags drawn
- `--family`: Specify AprilTag family (default: tag36h11)

## AprilTag Families

Supported families:
- tag36h11 (default, recommended)
- tag25h9
- tag16h5
- tagCircle21h7
- tagStandard41h12

## Camera Calibration

For accurate pose estimation, you should calibrate your camera and update the camera parameters in the code:

```python
detector = AprilTagDetector(camera_params=[fx, fy, cx, cy])
```

Where:
- fx, fy: Focal lengths in pixels
- cx, cy: Principal point coordinates

## Output Information

For each detected tag, the program displays:
- Tag ID
- Center position (x, y)
- Corner positions
- Rotation matrix
- Translation vector (position in 3D space)

## Troubleshooting

- **No camera detected**: Ensure the camera is enabled in `raspi-config`
- **No tags detected**: Check tag size setting (default: 0.05m) matches your physical tags
- **Poor detection**: Ensure good lighting and the tag is clearly visible
