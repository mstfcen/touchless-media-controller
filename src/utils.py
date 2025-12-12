import math

def calculate_distance(p1, p2):
    """Calculates Euclidean distance between two 3D points."""
    return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2) ** 0.5

def calculate_angle(v1, v2):
    """Calculates the angle in degrees between two vectors."""
    dot = sum(a*b for a, b in zip(v1, v2))
    m1 = math.sqrt(sum(a*a for a in v1))
    m2 = math.sqrt(sum(a*a for a in v2))
    
    if m1 * m2 == 0:
        return 180.0
        
    cos_val = max(-1, min(1, dot / (m1 * m2)))
    return math.degrees(math.acos(cos_val))

def get_finger_curl_angle(landmarks, mcp_idx, pip_idx, tip_idx):
    """
    Calculates the bending angle of a finger.
    Args:
        landmarks: List of hand landmarks.
        mcp_idx: Index of Metacarpophalangeal joint.
        pip_idx: Index of Proximal Interphalangeal joint.
        tip_idx: Index of the Finger Tip.
    """
    lm = landmarks
    # Vector 1: MCP to PIP
    v1 = (lm[pip_idx].x - lm[mcp_idx].x, 
          lm[pip_idx].y - lm[mcp_idx].y, 
          lm[pip_idx].z - lm[mcp_idx].z)
    
    # Vector 2: PIP to TIP
    v2 = (lm[tip_idx].x - lm[pip_idx].x, 
          lm[tip_idx].y - lm[pip_idx].y, 
          lm[tip_idx].z - lm[pip_idx].z)
          
    return calculate_angle(v1, v2)