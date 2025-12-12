# Touchless Media Controller

Touchless Media Controller is a desktop application that allows users to control
media playback using hand gestures captured via a webcam. The system performs
real-time hand tracking and gesture recognition to trigger media actions without
any physical interaction.

The application is designed as a lightweight utility tool focusing on
responsiveness, stability, and real-time performance.

---

## Demo Video

The following video demonstrates the core functionality of the application,
including camera initialization, gesture-based command mode toggling, and media
control actions.

[![Touchless Media Controller Demo](https://img.youtube.com/vi/cJxzags02jY/0.jpg)](https://youtu.be/cJxzags02jY)

---

## Command Mode

The application operates using a two-state command mode system to prevent
unintended media actions.

- **LOCKED Mode**  
  Gesture-based media controls are disabled. This is the default and safe state.

- **ACTIVE Mode**  
  Gesture-based media controls are enabled and executed in real time.

The command mode is toggled using a two-hand OK gesture.

---

## Supported Gestures

- Two-Hand OK Gesture  
  Toggles the command mode between LOCKED and ACTIVE states.

- Gun Gesture (Thumb + Index Extended)  
  Play / Pause media.

- Two Fingers Gesture  
  Skip to the next track.

- Three Fingers Gesture  
  Return to the previous track.

- Open Hand Gesture (Vertical Position Based)  
  Increases the system volume when the hand is positioned near the top of the
  camera frame, and decreases the volume when the hand is positioned near the
  bottom of the frame.

---

## Automatic Safety Lock

To ensure safe and predictable behavior, the system automatically switches back
to LOCKED mode when no hands are detected in the camera frame for a short period
of time.

This prevents unintended media actions when the user moves away from the camera
or leaves the camera field of view.

---

## How It Works

1. The webcam stream is captured using OpenCV.
2. Hand landmarks are detected using MediaPipe Hands.
3. Gestures are classified based on finger angles and spatial relationships.
4. Recognized gestures are mapped to media control commands.
5. Media actions are executed via simulated keyboard events.
6. The system automatically locks command execution when hand presence is lost.

---

## Project Structure

```text
touchless-media-controller/
│
├── main.py
├── README.md
├── requirements.txt
│
├── assets/
│   └── icon.ico
│
└── src/
    ├── config.py
    ├── hand_detector.py
    ├── media_interface.py
    └── utils.py

```
---
## Known Issues

- When running the application from the terminal, MediaPipe may emit warning
  messages related to deprecated protobuf APIs (for example
  `SymbolDatabase.GetPrototype`). These warnings originate from internal library
  dependencies and do not affect application functionality or runtime behavior.

- During camera initialization or camera start/stop cycles, CustomTkinter may
  display a warning indicating that a non-CTkImage object was temporarily passed
  to a `CTkLabel`. This is a known limitation related to Tkinter image lifecycle
  management and does not impact the correctness or stability of the application.

---

## Releases

A standalone Windows executable (.exe) version of the application is provided
for users who do not wish to run the project from source.

See the
[Releases](https://github.com/mstfcen/touchless-media-controller/releases)
section of this repository for the latest executable build.
