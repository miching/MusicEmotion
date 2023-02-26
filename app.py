from flask import Flask, render_template, Response, request, redirect
import cv2
import pathlib
from deepface import DeepFace
import time
from collections import Counter
from pymongo import MongoClient

import os
from dotenv import load_dotenv
from pathlib import Path

#Path to config.env which contains MongoDBLink (enviorment variables)
dotenv_path = Path('config.env')
load_dotenv(dotenv_path=dotenv_path)

#Get env varaibles - hide MongoDB Link
connectMongoLink = os.getenv("MONGO_LINK")
#print('info:',connectMongoLink)


app = Flask(__name__)
#Default training data provided by CV2 for facial recog
cascPath = pathlib.Path(cv2.__file__).parent.absolute() / 'data/haarcascade_frontalface_default.xml'
faceCascade = cv2.CascadeClassifier(str(cascPath))
video_capture = cv2.VideoCapture(0)

#Most shown emotion
totalEmotion = []

#MongoDB
client = MongoClient(connectMongoLink)

# Create a MongoDB database called ratingsList
db = client.MusicEmotion

# Create a collection called items on the database
# Collections store a group of documents in MongoDB, like tables in relational databases.
collectionItems = db.moods


#data = {'moods': ['sad','happy']}
#db.push(data)

def camera():

    #Run for 10 seconds
    t_end = time.time() + 10
    video_capture = cv2.VideoCapture(0)
    #Keep capturing till time over
    #while time.time() < t_end:
    # While cam is on
    while True:
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

            totalEmotion.append(result[0]['dominant_emotion'])

        #cv2.imshow('Emotion', frame)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame=buffer.tobytes()

        if frame != None:
            global_frame = frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

        yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    # When everything is done, release the capture
    video_capture.release()
    cv2.destroyAllWindows()





@app.route('/', methods = ['GET','POST'])
def index():  # put application's code here

    #if request.method == 'POST':
        #if request.form['cameraFunction'] == 'Stop':
            #return redirect('/results')
            #return render_template('results.html')

    return render_template('index.html')



@app.route('/emotion')
def captureEmotion():

    return Response(camera(), mimetype='multipart/x-mixed-replace; boundary=frame')



@app.route('/results')
def results():
    video_capture.release()
    cv2.destroyAllWindows()


    #Get most shown emotion through the recording
    occurence_count = Counter(totalEmotion)
    print(occurence_count.most_common(1)[0])


    #if request.method == 'POST':
       #if request.form['cameraFunction'] == 'Capture':
           #return redirect('/')

    return render_template('results.html')


if __name__ == '__main__':
    #app.run()
    app.run(host='127.0.0.1', port=8002, debug=True,threaded=True)
