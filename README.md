# Eye-Controlled Mouse & Accessibility System

Control your computer cursor and perform mouse actions using only your eyes and facial gestures.

This project uses MediaPipe Face Mesh, OpenCV, and PyAutoGUI to track eye movements, detect blink patterns, and translate them into mouse interactions such as clicking, dragging, scrolling, and opening an on-screen keyboard.

## Features

### Cursor Control

- Real-time eye tracking
- Smooth cursor movement
- 4-point calibration for improved accuracy
- Perspective transformation for full-screen coverage

### Blink-Based Commands

| Gesture | Action |
|----------|----------|
| Left Eye Double Blink | Left Click |
| Right Eye Double Blink | Right Click |
| Both Eyes Double Blink | Double Click |
| Left Eye Triple Blink | Toggle Scroll Mode |
| Right Eye Triple Blink | Toggle Drag Mode |
| Both Eyes Triple Blink | Toggle On-Screen Keyboard |

### Scroll Mode

When scroll mode is enabled:

- Tilt head up → Scroll Up
- Tilt head down → Scroll Down
- Keep head straight → Stop Scrolling

### Drag Mode

- Triple blink right eye to start dragging.
- Triple blink right eye again to release.

### Accessibility Keyboard

- Triple blink both eyes to open/close the on-screen keyboard.
- Long blink (1.5 seconds) also toggles keyboard mode.

### Exit Gesture

- Keep both eyes closed for 3 seconds to safely exit the application.

## Technologies Used

- Python
- OpenCV
- MediaPipe Face Mesh
- NumPy
- PyAutoGUI

## Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/eye-controlled-mouse.git
cd eye-controlled-mouse
```

### Install Dependencies

```bash
pip install opencv-python mediapipe numpy pyautogui
```

## Running the Project

```bash
python main.py
```

Make sure your webcam is connected and accessible.

## Calibration Process

The system uses a 4-point calibration process for accurate cursor mapping.

Follow the instructions displayed on the screen:

1. Look at the top-left corner and press `1`
2. Look at the top-right corner and press `2`
3. Look at the bottom-right corner and press `3`
4. Look at the bottom-left corner and press `4`
5. Press `Enter` to complete calibration

### Calibration Tips

- Sit in your normal position
- Keep your head still
- Move only your eyes while calibrating
- Use good lighting conditions
- Stay at a consistent distance from the camera

## How It Works

### Eye Tracking

MediaPipe Face Mesh detects facial landmarks and iris positions from the webcam feed.

### Cursor Mapping

A perspective transformation maps iris coordinates to screen coordinates, enabling accurate cursor control across the display.

### Blink Detection

The system calculates the Eye Aspect Ratio (EAR) to determine whether an eye is open or closed.

### Gesture Recognition

Blink sequences are analyzed to detect:

- Double blinks
- Triple blinks
- Long blinks

Each gesture triggers a specific mouse or accessibility action.

## Controls Summary

| Gesture | Action |
|----------|----------|
| Left Eye Double Blink | Left Click |
| Right Eye Double Blink | Right Click |
| Both Eyes Double Blink | Double Click |
| Left Eye Triple Blink | Toggle Scroll Mode |
| Right Eye Triple Blink | Toggle Drag Mode |
| Both Eyes Triple Blink | Toggle Keyboard |
| Both Eyes Closed (1.5s) | Toggle Keyboard |
| Both Eyes Closed (3s) | Exit Program |
| Head Up (Scroll Mode) | Scroll Up |
| Head Down (Scroll Mode) | Scroll Down |

## Configuration

You can adjust the following parameters in `main.py`:

```python
EYE_AR_THRESH = 0.20
DOUBLE_BLINK_MAX_TIME = 1.0
TRIPLE_BLINK_MAX_TIME = 1.5
SMOOTHING = 0.85
SENSITIVITY = 0.65
LONG_BLINK_TIME = 1.5
EXIT_TIME = 3.0
```

## Requirements

### Hardware

- Webcam
- Windows or Linux computer
- Stable lighting environment

### Software

- Python 3.8+
- OpenCV
- MediaPipe
- NumPy
- PyAutoGUI

## Future Improvements

- Machine learning-based calibration
- Personalized blink sensitivity
- Multi-monitor support
- Voice command integration
- Improved head-pose estimation
- Custom gesture mapping

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature-name
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push to GitHub

```bash
git push origin feature-name
```

5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Author

Developed as a hands-free computer interaction system focused on accessibility, eye tracking, and gesture-based control.
