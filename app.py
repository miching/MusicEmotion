from flask import Flask, render_template, Response, request
import cv2
import pathlib
from deepface import DeepFace
import time

app = Flask(__name__)
#Default training data provided by CV2 for facial recog
cascPath = pathlib.Path(cv2.__file__).parent.absolute() / 'data/haarcascade_frontalface_default.xml'
faceCascade = cv2.CascadeClassifier(str(cascPath))
video_capture = cv2.VideoCapture(0)

def camera():

    #Run for 10 seconds
    t_end = time.time() + 20

    #Keep capturing till time over
    while time.time() < t_end:
    # While cam is on
    #while True:
        # Capture frame-by-frame
        ret, frame = video_capture.read()
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        #print(result)

        # Color scale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,  # Things not facial
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        # Draw a rectangle around the faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            cv2.putText(frame, result[0]['dominant_emotion'], (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12),
                        2)

        #cv2.imshow('Emotion', frame)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame=buffer.tobytes()

        yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    # When everything is done, release the capture
    video_capture.release()
    cv2.destroyAllWindows()



@app.route('/')
def index():  # put application's code here
    return render_template('index.html')


@app.route('/emotion', methods = ['GET','POST'])
def captureEmotion():

    if request.method == 'POST':
        return Response(camera(), mimetype='multipart/x-mixed-replace; boundary=frame')

    else:
        return Response(camera(), mimetype='multipart/x-mixed-replace; boundary=frame')



if __name__ == '__main__':
    app.run(debug=True)
