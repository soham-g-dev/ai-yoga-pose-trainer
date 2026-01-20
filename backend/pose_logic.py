def analyze_pose(landmarks, image_shape):
    back_angle, leg_angle, _ = process_pose(landmarks, image_shape)

    if back_angle is None:
        return None

    is_correct = (80 <= back_angle <= 100) and (150 <= leg_angle <= 180)
    accuracy = 100 if is_correct else 70

    if is_correct:
        message = "Excellent. Hold the pose."
    else:
        message = "Adjust your posture"

    return {
        "back_angle": int(back_angle),
        "leg_angle": int(leg_angle),
        "accuracy": accuracy,
        "message": message
    }
