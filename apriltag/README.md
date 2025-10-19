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

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make the script executable:
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

Display detections in real-time (requires display):
```bash
python detect_apriltags.py --mode continuous --display
```

Save all detections:
```bash
python detect_apriltags.py --mode continuous --save
```

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
