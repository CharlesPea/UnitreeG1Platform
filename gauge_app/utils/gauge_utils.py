# gauge_app/utils/gauge_utils.py
import cv2
import numpy as np
import math

def line(p1, p2):
    """Create a line from two points in the format Ax + By + C = 0."""
    A = (p1[1] - p2[1])
    B = (p2[0] - p1[0])
    C = (p1[0]*p2[1] - p2[0]*p1[1])
    return A, B, -C

def intersection(L1, L2):
    """Find the intersection point of two lines."""
    D = L1[0]*L2[1] - L1[1]*L2[0]
    Dx = L1[2]*L2[1] - L1[1]*L2[2]
    Dy = L1[0]*L2[2] - L1[2]*L2[0]
    if D != 0:
        return Dx/D, Dy/D
    return None

def create_hue_mask(image, lower, upper):
    """Create a binary mask based on HSV color range."""
    return cv2.inRange(image, np.array(lower, np.uint8), np.array(upper, np.uint8))

def findRed(img):
    """Create a mask that isolates red objects in the image."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    low1 = create_hue_mask(hsv, [0, 100, 100], [10, 255, 255])
    low2 = create_hue_mask(hsv, [170, 100, 100], [179, 255, 255])
    return cv2.GaussianBlur(cv2.bitwise_or(low1, low2), (5, 5), 0)

def findCircles(mask):
    """Detect circles in the binary mask image."""
    circles = cv2.HoughCircles(
        mask, cv2.HOUGH_GRADIENT, 1, 50,
        param1=50, param2=15,
        minRadius=30, maxRadius=200
    )
    
    if circles is None or len(circles[0]) == 0:
        return []
    
    # Sort by x-coordinate
    pts = sorted(circles[0], key=lambda c: c[0])
    # Return list of (x,y,r)
    return [(int(x), int(y), int(r)) for x, y, r in pts]

def findAngle(cut_bgr, cut_mask, center, width):
    """Find the angle of the gauge needle."""
    edges = cv2.Canny(cut_mask, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges, rho=1, theta=np.pi/180,
        threshold=30,
        minLineLength=width//3,
        maxLineGap=20
    )
    
    tip, maxd = None, 0
    if lines is None:
        return None
        
    for ln in lines:
        x1, y1, x2, y2 = ln[0]
        L1 = line((x1, y1), (x2, y2))
        for ln2 in lines:
            x3, y3, x4, y4 = ln2[0]
            if (x1, y1, x2, y2) == (x3, y3, x4, y4):
                continue
            L2 = line((x3, y3), (x4, y4))
            pt = intersection(L1, L2)
            if pt:
                dx = pt[0] - center[0]
                dy = center[1] - pt[1]
                dist = math.hypot(dx, dy)
                if 0 < dist < width/2 and dist > maxd:
                    tip, maxd = pt, dist
                    
    if tip is None:
        return None

    # Compute angle
    dx = tip[0] - center[0]
    dy = center[1] - tip[1]
    deg = math.degrees(math.atan2(dy, dx))
    
    # Normalize to 0–100%
    if deg < 0:
        pct = (90 + abs(deg)) / 360
    elif deg <= 90:
        pct = (90 - deg) / 360
    else:
        pct = (450 - deg) / 360
        
    return max(0, min(100, int(pct*100)))

def read_regular_gauge(frame):
    """Return a single 0–100 int or None representing gauge reading."""
    red = findRed(frame)
    circles = findCircles(red)
    if not circles:
        return None
        
    x, y, r = circles[0]
    # Extract a square region around the dial
    pad = int(1.2*r)
    y1, y2 = max(0, y-pad), min(frame.shape[0], y+pad)
    x1, x2 = max(0, x-pad), min(frame.shape[1], x+pad)
    cut_bgr = frame[y1:y2, x1:x2]
    cut_mask = red[y1:y2, x1:x2]
    
    return findAngle(cut_bgr, cut_mask, ((x2-x1)//2, (y2-y1)//2), x2-x1)

def getNeedleMask(img, red_thresh_ratio=0.01):
    """Get a mask highlighting the gauge needle."""
    # 1) Try red-hue mask
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    low1 = create_hue_mask(hsv, [0, 100, 100], [10, 255, 255])
    low2 = create_hue_mask(hsv, [170, 100, 100], [179, 255, 255])
    redm = cv2.GaussianBlur(cv2.bitwise_or(low1, low2), (5, 5), 0)

    # 2) If too little red, fall back to edges
    total = img.shape[0]*img.shape[1]
    if cv2.countNonZero(redm) < total * red_thresh_ratio:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        return cv2.GaussianBlur(edges, (5, 5), 0)
    return redm