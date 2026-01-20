from flask import Flask, Response, jsonify
from flask_cors import CORS
from camera import generate_frames, latest_feedback

app = Flask(__name__)
CORS(app)   # ✅ THIS LINE FIXES IT

@app.route("/")
def index():
    return "Yoga AI Backend Running"

@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/feedback")
def feedback():
    return jsonify(latest_feedback)

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
