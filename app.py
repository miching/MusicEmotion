import pathlib
# from deepface import DeepFace
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from flask import Flask, render_template, url_for, redirect, request, session
import cv2
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


app.secret_key = "ONealalsf23p9e"
app.config['SESSION_COOKIE_NAME'] = 'Temp Cookie'
TOKEN_INFO = "token_info"


#Default training data provided by CV2 for facial recog
cascPath = pathlib.Path(cv2.__file__).parent.absolute() / 'data/haarcascade_frontalface_default.xml'
faceCascade = cv2.CascadeClassifier(str(cascPath))
#video_capture = cv2.VideoCapture(0)

#Most shown emotion
totalEmotion = []

#MongoDB
client = MongoClient(connectMongoLink)

# Create a MongoDB database called ratingsList
db = client.MusicEmotion

# Create a collection called items on the database
# Collections store a group of documents in MongoDB, like tables in relational databases.
collectionMoods = db.moods
try:
    test = {'_id': 'mike', 'moods': []}
    collectionMoods.insert_one(test)
except:
    pass
#data = {'moods': ['sad','happy']}
#db.push(data)


@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/authorize')
def authorize():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect("/cam")


@app.route('/captureimage') #this will be our redirect page
def picturePage():  # put application's code here
    return 'Hello' #render_template('capture-image.html')


@app.route('/getTracks')
def getTracks():
    try:
        token_info = get_token()
    except:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(auth=token_info['access_token'])
    return sp.current_user_saved_tracks(limit=50, offset=0)


@app.route('/queue-display', methods=['GET', 'POST'])
def queueDisplay():
    if request.method == 'POST':
        return redirect(url_for('logout', _external=True))
    else:
        return render_template("queue-display.html")




@app.route('/', methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        return redirect(url_for('login', _external=True))
    else:
        return render_template("homepage.html")


def get_token():
    token_valid = False
    token_info = session.get("token_info", {})

    # Checking if the session already has a token stored
    if not (session.get('token_info', False)):
        token_valid = False
        return token_info, token_valid

    # Checking if token has expired
    now = int(time.time())
    is_expired = session.get('token_info').get('expires_at') - now < 60

    # Refreshing token if it has expired
    if (is_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(session.get('token_info').get('refresh_token'))

    token_valid = True
    return token_info, token_valid


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id="701d5036b2b4465eb0254db1f4d67056",
        client_secret="93d4504616194679a6ee5ab445204bed",
        redirect_uri=url_for('authorize', _external=True),
        scope="user-library-read")


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





@app.route('/cam', methods = ['GET','POST'])
def index():  # put application's code here

    if request.method == 'POST':
        return redirect('/results')


    return render_template('index.html')



@app.route('/emotion')
def captureEmotion():

    time.sleep(20)
    return Response(camera(), mimetype='multipart/x-mixed-replace; boundary=frame')



@app.route('/results', methods = ['GET','POST'])
def results():

    if request.method == 'POST':
        return(redirect('/'))

    else:


        #Get most shown emotion

        angerCount = totalEmotion.count('anger')
        fearCount = totalEmotion.count('fear')
        sadCount = totalEmotion.count('sad')
        disgustCount = totalEmotion.count('disgust')
        happyCount = totalEmotion.count('happy')
        surprisedCount = totalEmotion.count('surprised')

        emotionCount = []
        emotionCount.append(angerCount)
        emotionCount.append(fearCount)
        emotionCount.append(sadCount)
        emotionCount.append(disgustCount)
        emotionCount.append(happyCount)
        emotionCount.append(surprisedCount)

        highestCount = -1

        for i in range(len(emotionCount)-1):
            if emotionCount[i] > highestCount:
                highestCount = emotionCount[i]


        if(highestCount == angerCount):
            mostShownEmotion = 'anger'
        elif(highestCount == fearCount):
            mostShownEmotion = 'fear'
        elif (highestCount == sadCount):
            mostShownEmotion = 'sad'
        elif (highestCount == disgustCount):
            mostShownEmotion = 'disgust'
        elif (highestCount == happyCount):
            mostShownEmotion = 'happy'
        else:
            mostShownEmotion = 'surprised'



        #occurence_count = Counter(totalEmotion)
        #print(occurence_count.most_common(1)[0])
        #mostShownEmotion = occurence_count.most_common(1)[0]

        #mostShownEmotion = 'disappointed'
        previousEmotions = collectionMoods.find_one({'_id': "mike"})
        print(previousEmotions)

        emotionHistory = previousEmotions['moods']
        emotionHistory.append(mostShownEmotion)
        #print('BEFOREhistory',emotionHistory)
        #print('history',emotionHistory)
        #emotionHistory = ['angry', 'happy', 'sad','fear']


        #collectionMoods.update_one({'_id': 'mike'}, {'$push': {'moods': emotionHistory}})
        collectionMoods.update_one({'_id': 'mike'}, {'$push': {'moods': mostShownEmotion}})

        return render_template('results.html', moodHistory = emotionHistory)

    #else:
        #return('here')


if __name__ == '__main__':
    FLASK_DEBUG = 1
    app.run(debug=True)
    #app.run(host='127.0.0.1', port=8002, debug=True,threaded=True)
