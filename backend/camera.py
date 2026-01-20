import cv2
import mediapipe as mp
import math
from collections import deque

# =========================
# PERFORMANCE CONFIG
# =========================
FRAME_SKIP = 3
frame_count = 0

# =========================
# GLOBAL STATE
# =========================
latest_feedback = {
    "back_angle": 0,
    "leg_angle": 0,
    "accuracy": 0,
    "message": "Waiting for pose"
}

last_coords = None

# =========================
# BUFFERS (SMOOTHING)
# =========================
back_buffer = deque(maxlen=10)
leg_buffer = deque(maxlen=10)

# =========================
# MEDIAPIPE INIT
# =========================
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# =========================
# CAMERA INIT
# =========================
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# =========================
# UTILITY FUNCTIONS
# =========================
def calculate_angle(a, b, c):
    ang = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0]) -
        math.atan2(a[1] - b[1], a[0] - b[0])
    )
    ang = abs(ang)
    return 360 - ang if ang > 180 else ang

def get_coords(landmark, shape):
    h, w = shape[:2]
    return [int(landmark.x * w), int(landmark.y * h)]

def process_pose(landmarks, shape):
    try:
        shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value]
        ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]

        if min(shoulder.visibility, hip.visibility, knee.visibility, ankle.visibility) < 0.5:
            return None, None, None

        s = get_coords(shoulder, shape)
        h = get_coords(hip, shape)
        k = get_coords(knee, shape)
        a = get_coords(ankle, shape)

        back_angle = calculate_angle(s, h, k)
        leg_angle = calculate_angle(h, k, a)

        return back_angle, leg_angle, (s, h, k, a)
    except:
        return None, None, None

def draw_angle(img, p1, p2, p3, angle, label, color):
    cv2.line(img, p1, p2, color, 2)
    cv2.line(img, p2, p3, color, 2)
    mid = ((p1[0] + p3[0]) // 2, (p1[1] + p3[1]) // 2)
    cv2.putText(
        img, f"{label}: {int(angle)}°", mid,
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
    )

# =========================
# MAIN STREAM FUNCTION
# =========================
def generate_frames():
    global frame_count, last_coords, latest_feedback

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame_count += 1
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if frame_count % FRAME_SKIP == 0:
            results = pose.process(image_rgb)

            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )

                back_angle, leg_angle, coords = process_pose(
                    results.pose_landmarks.landmark,
                    frame.shape
                )

                if back_angle is not None:
                    back_buffer.append(back_angle)
                    leg_buffer.append(leg_angle)

                    smooth_back = sum(back_buffer) / len(back_buffer)
                    smooth_leg = sum(leg_buffer) / len(leg_buffer)

                    last_coords = coords

                    is_correct = (80 <= smooth_back <= 100) and (150 <= smooth_leg <= 180)

                    latest_feedback = {
                        "back_angle": int(smooth_back),
                        "leg_angle": int(smooth_leg),
                        "accuracy": 100 if is_correct else 70,
                        "message": "Excellent. Hold the pose."
                                   if is_correct else "Adjust posture"
                    }

        if last_coords:
            s, h, k, a = last_coords
            draw_angle(frame, s, h, k, latest_feedback["back_angle"], "Back", (0, 255, 255))
            draw_angle(frame, h, k, a, latest_feedback["leg_angle"], "Leg", (255, 255, 0))

            cv2.putText(
                frame,
                latest_feedback["message"],
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0) if latest_feedback["accuracy"] == 100 else (0, 0, 255),
                2
            )

        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
