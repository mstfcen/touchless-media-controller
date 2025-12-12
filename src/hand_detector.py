from src.utils import calculate_distance, get_finger_curl_angle

class GestureRecognizer:
    """Handles logic for recognizing specific hand gestures."""

    @staticmethod
    def is_ok_gesture(landmarks):
        """
        Checks for the 'OK' sign (Thumb and Index touching, others open).
        Used for toggling the command mode.
        """
        lm = landmarks
        # 1. Distance check: Thumb tip (4) close to Index tip (8)
        if calculate_distance(lm[4], lm[8]) > 0.045:
            return False
            
        # 2. Curl check: Middle finger should not be fully curled
        if get_finger_curl_angle(lm, 9, 10, 12) > 70:
            return False
            
        # 3. Thumb check: Should not be folded inside
        if get_finger_curl_angle(lm, 2, 3, 4) > 80:
            return False
            
        return True

    @staticmethod
    def is_gun_gesture(landmarks):
        """
        Checks for 'Gun' gesture (Thumb & Index extended, others closed).
        Used for Play/Pause.
        """
        lm = landmarks
        # Calculate curl for all fingers
        curls = {
            "thumb": get_finger_curl_angle(lm, 2, 3, 4),
            "index": get_finger_curl_angle(lm, 5, 6, 8),
            "middle": get_finger_curl_angle(lm, 9, 10, 12),
            "ring":   get_finger_curl_angle(lm, 13, 14, 16),
            "pinky":  get_finger_curl_angle(lm, 17, 18, 20),
        }
        
        # Thresholds: Low angle = Open, High angle = Closed
        open_fingers = {f: (v < 60) for f, v in curls.items()}
        closed_fingers = {f: (v > 115) for f, v in curls.items()}
        
        return (open_fingers["thumb"] and 
                open_fingers["index"] and 
                closed_fingers["middle"] and 
                closed_fingers["ring"] and 
                closed_fingers["pinky"])

    @staticmethod
    def classify_static_pose(landmarks):
        """
        Classifies static poses like Open Hand, Two Fingers, Three Fingers.
        """
        lm = landmarks
        curls = {
            "thumb": get_finger_curl_angle(lm, 2, 3, 4),
            "index": get_finger_curl_angle(lm, 5, 6, 8),
            "middle": get_finger_curl_angle(lm, 9, 10, 12),
            "ring":   get_finger_curl_angle(lm, 13, 14, 16),
            "pinky":  get_finger_curl_angle(lm, 17, 18, 20),
        }
        
        is_open = {f: (v < 75) for f, v in curls.items()}
        is_closed = {f: (v > 115) for f, v in curls.items()}

        if all(is_open.values()):
            return "OPEN_HAND"
        
        # Two Fingers (Victory Sign) -> Next Track
        if (is_open["index"] and is_open["middle"] and 
            is_closed["ring"] and is_closed["pinky"]):
            return "TWO_FINGERS"
        
        # Three Fingers -> Previous Track
        if (is_open["index"] and is_open["middle"] and 
            is_open["ring"] and is_closed["pinky"]):
            return "THREE_FINGERS"
            
        return "UNKNOWN"