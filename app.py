import pathlib

from flask import Flask, render_template, Response
import cv2
from deepface import DeepFace

app = Flask(__name__)
#Default training data provided by CV2 for facial recog
cascPath = pathlib.Path(cv2.__file__).parent.absolute() / 'data/haarcascade_frontalface_default.xml'
faceCascade = cv2.CascadeClassifier(str(cascPath))
video_capture = cv2.VideoCapture(0)

def camera():
    # While cam is on
    while True:
        # Capture frame-by-frame
        ret, frame = video_capture.read()
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        print(result)

@app.route('/')
def index():  # put application's code here
    return render_template('index.html')


@app.route('/emotion')
def captureEmotion():
    return Response(camera(), mimetype='multipart/x-mixed-replace; boundary=frame')



if __name__ == '__main__':
    app.run(debug=True)
