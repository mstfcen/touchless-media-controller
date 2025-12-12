import customtkinter as ctk
import cv2
import threading
import time
from PIL import Image
import pystray
from pystray import MenuItem as item
from pynput.keyboard import Key

# Project Modules
from src import config
from src.hand_detector import GestureRecognizer
from src.media_interface import MediaInterface


# --------------------------------------------------
# UI CONFIGURATION
# --------------------------------------------------
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class GestureApp(ctk.CTk):
    """
    Main application class for the Touchless Media Controller.
    Handles GUI, camera lifecycle, frame loop and gesture orchestration.
    """

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("Touchless Media Controller")
        self.geometry("950x650")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        # Camera state
        self.running = False
        self.camera_index = 0
        self.cap = None
        self.is_camera_loading = False

        # Media control interface
        self.media_ctrl = MediaInterface()

        # Gesture and mode state
        self.lock_mode = True
        self.volume_state = "IDLE"

        # Image reference (prevents Tkinter GC issues)
        self.current_image = None

        # Gesture temporal state
        self.prev_ok_state = False
        self.last_toggle_ts = 0
        self.last_cmd_ts = 0
        self.gun_frames = 0
        self.stable_frames = 0
        self.prev_gesture = None
        self.last_seen_ts = time.time()

        # MediaPipe initialization
        import mediapipe as mp
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.55
        )

        self.setup_ui()

    # --------------------------------------------------
    # UI SETUP
    # --------------------------------------------------

    def setup_ui(self):
        """Initializes all UI components."""

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="GESTURE\nCONTROLLER",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.pack(padx=20, pady=(30, 20))

        self.cam_label = ctk.CTkLabel(self.sidebar, text="Select Camera:", anchor="w")
        self.cam_label.pack(padx=20, pady=(10, 0))

        self.cam_option = ctk.CTkComboBox(
            self.sidebar,
            values=["Camera 0", "Camera 1", "Camera 2"],
            command=self.change_camera
        )
        self.cam_option.set("Camera 0")
        self.cam_option.pack(padx=20, pady=(5, 20))

        self.btn_start = ctk.CTkButton(
            self.sidebar,
            text="START CAMERA",
            fg_color="green",
            command=self.toggle_camera
        )
        self.btn_start.pack(padx=20, pady=10)

        self.status_label = ctk.CTkLabel(
            self.sidebar,
            text="STATUS: STOPPED",
            text_color="gray"
        )
        self.status_label.pack(padx=20, pady=10)

        self.info_box = ctk.CTkTextbox(self.sidebar, height=200)
        self.info_box.insert("0.0", "LOGS:\n")
        self.info_box.pack(padx=10, pady=10, fill="x")

        self.btn_quit = ctk.CTkButton(
            self.sidebar,
            text="QUIT APP",
            fg_color="darkred",
            hover_color="red",
            command=self.quit_app_fully
        )
        self.btn_quit.pack(padx=20, pady=(20, 20), side="bottom")

        self.video_frame = ctk.CTkFrame(
            self,
            fg_color="black",
            width=640,
            height=480
        )
        self.video_frame.pack(
            side="right",
            padx=10,
            pady=10
        )
        self.video_frame.pack_propagate(False)


        self.video_label = ctk.CTkLabel(
            self.video_frame,
            text="Camera is OFF",
            text_color="white",
            font=("Arial", 16)
        )
        self.video_label.pack()


    # --------------------------------------------------
    # SYSTEM TRAY
    # --------------------------------------------------

    def hide_to_tray(self):
        """Minimizes application to system tray."""

        self.withdraw()

        def show_action(icon, item):
            icon.stop()
            self.after(0, self.deiconify)

        def quit_action(icon, item):
            icon.stop()
            self.quit_app_fully()

        image = Image.new("RGB", (64, 64), (255, 0, 0))
        self.tray_icon = pystray.Icon(
            "GestureApp",
            image,
            "Touchless Controller",
            menu=pystray.Menu(
                item("Show", show_action),
                item("Quit", quit_action)
            )
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def quit_app_fully(self):
        """Fully shuts down the application."""
        self.stop_camera()
        self.destroy()

    def log(self, msg):
        """Writes a message to the log panel."""
        try:
            self.info_box.insert("end", f"> {msg}\n")
            self.info_box.see("end")
        except:
            pass
    # --------------------------------------------------
    # CAMERA CONTROL
    # --------------------------------------------------

    def change_camera(self, choice):
        """
        Changes the active camera index.
        If the camera is currently running, it is restarted safely.
        """
        self.camera_index = int(choice.split(" ")[1])

        if self.running:
            self.stop_camera()
            self.after(500, self.start_camera_thread)

    def toggle_camera(self):
        """
        Starts or stops the camera depending on current state.
        Prevents multiple concurrent camera open attempts.
        """
        if self.is_camera_loading:
            return

        if self.running:
            self.stop_camera()
        else:
            self.start_camera_thread()

    def start_camera_thread(self):
        """
        Starts the camera opening process in a background thread
        to avoid blocking the UI thread.
        """
        self.is_camera_loading = True
        self.btn_start.configure(state="disabled", text="LOADING...")
        self.status_label.configure(text="CONNECTING...", text_color="orange")

        threading.Thread(target=self._open_camera, daemon=True).start()

    def _open_camera(self):
        """
        Attempts to open the selected camera.
        Executed in a background thread.
        """
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not cap.isOpened():
            cap = None

        self.after(0, lambda: self._on_camera_opened(cap))

    def _on_camera_opened(self, cap):
        """
        Finalizes camera opening on the main UI thread.
        """
        self.is_camera_loading = False
        self.btn_start.configure(state="normal")

        if cap:
            self.cap = cap
            self.running = True

            self.btn_start.configure(text="STOP CAMERA", fg_color="red")
            self.status_label.configure(text="STATUS: RUNNING", text_color="green")
            self.video_label.configure(text="")

            self.log(f"Camera {self.camera_index} Active")

            # Start frame update loop
            self.after(50, self.update_frame)
        else:
            self.status_label.configure(text="STATUS: FAILED", text_color="red")
            self.btn_start.configure(text="START CAMERA", fg_color="green")
            self.log("Camera open failed")

    def stop_camera(self):
        """
        Safely stops the camera and terminates the frame loop.
        """
        self.running = False

        if self.cap:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None

        # Clear image reference to avoid Tkinter image errors
        self.current_image = None

        # UI reset is deferred to the main thread
        self.after(0, self._reset_video_label)

        self.btn_start.configure(text="START CAMERA", fg_color="green")
        self.status_label.configure(text="STATUS: STOPPED", text_color="gray")
        self.volume_state = "IDLE"

        self.log("Camera Stopped")

    def _reset_video_label(self):
        """
        Resets the video label to a safe default state.
        """
        try:
            self.video_label.configure(image="", text="Camera is OFF")
        except:
            pass

    # --------------------------------------------------
    # FRAME LOOP
    # --------------------------------------------------

    def update_frame(self):
        """
        Main frame processing loop.
        Reads camera frames, processes gestures and updates UI.
        """
        if not self.running or self.cap is None or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            self.stop_camera()
            return

        # Mirror image for natural interaction
        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        now = time.time()

        # Gesture processing
        self.process_gestures(results, now)

        # Visual feedback overlay
        color = (0, 255, 0) if not self.lock_mode else (0, 0, 255)
        cv2.putText(
            frame,
            "ACTIVE" if not self.lock_mode else "LOCKED",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )

        # Convert frame to Tkinter-compatible image
        img = Image.fromarray(rgb)
        # Get available size of the video frame
        frame_w = self.video_frame.winfo_width()
        frame_h = self.video_frame.winfo_height()

        # Prevent zero-size issues during initial render
        if frame_w < 10 or frame_h < 10:
            return

        # Original camera aspect ratio (640x480 = 4:3)
        cam_aspect = 640 / 480
        frame_aspect = frame_w / frame_h

        if frame_aspect > cam_aspect:
            # Frame is wider → fit by height
            new_h = frame_h
            new_w = int(frame_h * cam_aspect)
        else:
            # Frame is taller → fit by width
            new_w = frame_w
            new_h = int(frame_w / cam_aspect)

        self.current_image = ctk.CTkImage(
            light_image=img,
            dark_image=img,
            size=(new_w, new_h)
        )


        try:
            self.video_label.configure(image=self.current_image, text="")
        except:
            return

        if self.running:
            self.after(10, self.update_frame)

    # --------------------------------------------------
    # GESTURE PROCESSING
    # --------------------------------------------------

    def process_gestures(self, results, now):
        """
        Interprets hand landmarks and maps gestures to media actions.
        """

        # -------- Mode Toggle (Two-Hand OK) --------
        is_two_hand_ok = False

        if results.multi_hand_landmarks and len(results.multi_hand_landmarks) == 2:
            h1 = results.multi_hand_landmarks[0].landmark
            h2 = results.multi_hand_landmarks[1].landmark
            is_two_hand_ok = (
                GestureRecognizer.is_ok_gesture(h1) and
                GestureRecognizer.is_ok_gesture(h2)
            )

        if (
            is_two_hand_ok and
            not self.prev_ok_state and
            (now - self.last_toggle_ts > config.TOGGLE_COOLDOWN)
        ):
            self.lock_mode = not self.lock_mode
            self.last_toggle_ts = now

            self.log(f"Mode: {'LOCKED' if self.lock_mode else 'ACTIVE'}")

            # Reset gesture counters on mode change
            self.gun_frames = 0
            self.stable_frames = 0

        self.prev_ok_state = is_two_hand_ok

        # -------- Locked State --------
        if self.lock_mode:
            self.volume_state = "IDLE"
            return

        # -------- Hand Presence Check --------
        if not results.multi_hand_landmarks:
            if now - self.last_seen_ts > config.AUTO_LOCK_TIMEOUT:
                self.lock_mode = True
                self.volume_state = "IDLE"
                self.log("Auto-Locked")
            return

        lm = results.multi_hand_landmarks[0].landmark
        self.last_seen_ts = now

        # -------- Volume Control --------
        pose = GestureRecognizer.classify_static_pose(lm)

        if pose == "OPEN_HAND":
            y = lm[9].y

            if y < config.VOLUME_TOP_THRESH:
                self.media_ctrl.execute_command(
                    Key.media_volume_up, "up", config.VOLUME_COOLDOWN
                )
                if self.volume_state != "INCREASING":
                    self.log("Volume Increasing...")
                    self.volume_state = "INCREASING"

            elif y > config.VOLUME_BOTTOM_THRESH:
                self.media_ctrl.execute_command(
                    Key.media_volume_down, "down", config.VOLUME_COOLDOWN
                )
                if self.volume_state != "DECREASING":
                    self.log("Volume Decreasing...")
                    self.volume_state = "DECREASING"
            else:
                self.volume_state = "IDLE"
        else:
            self.volume_state = "IDLE"

        # -------- Global Command Cooldown --------
        if now - self.last_cmd_ts < 1.2:
            return

        # -------- Play / Pause (Gun Gesture) --------
        if GestureRecognizer.is_gun_gesture(lm):
            self.gun_frames += 1

            if self.gun_frames >= config.GUN_FRAME_REQ:
                self.media_ctrl.execute_command(
                    Key.media_play_pause, "pp", 0.1
                )
                self.log("Action: Play / Pause")
                self.gun_frames = 0
                self.last_cmd_ts = now
        else:
            self.gun_frames = 0

            # -------- Next / Previous Track --------
            if pose in ["TWO_FINGERS", "THREE_FINGERS"]:
                if pose == self.prev_gesture:
                    self.stable_frames += 1
                else:
                    self.stable_frames = 0
                    self.prev_gesture = pose

                if self.stable_frames >= config.GESTURE_STABLE_REQ:
                    if pose == "TWO_FINGERS":
                        self.media_ctrl.execute_command(
                            Key.media_next, "next", 0.1
                        )
                        self.log("Action: Next Track")
                    else:
                        self.media_ctrl.execute_command(
                            Key.media_previous, "prev", 0.1
                        )
                        self.log("Action: Previous Track")

                    self.stable_frames = 0
                    self.last_cmd_ts = now


# --------------------------------------------------
# APPLICATION ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    app = GestureApp()
    app.mainloop()
