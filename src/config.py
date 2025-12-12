# ==========================================
# CONFIGURATION SETTINGS
# ==========================================

# Camera Settings
FRAME_WIDTH = 640
FRAME_HEIGHT = 360
SHOW_PREVIEW = True

# Gesture Constraints
TOGGLE_COOLDOWN = 1.0       # Seconds between mode toggles
GUN_FRAME_REQ = 3           # Frames to confirm 'Gun' gesture
GESTURE_STABLE_REQ = 4      # Frames to confirm 'Next/Prev' gestures

# Volume Control (Screen Position Normalized 0.0 - 1.0)
VOLUME_TOP_THRESH = 0.35    # Above this line -> Volume Up
VOLUME_BOTTOM_THRESH = 0.65 # Below this line -> Volume Down
VOLUME_COOLDOWN = 0.05      # Speed of volume change

# Auto-Lock
AUTO_LOCK_TIMEOUT = 1.2     # Seconds before locking if hand is lost