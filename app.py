import pathlib
# from deepface import DeepFace
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from flask import Flask, render_template, url_for, redirect, request, session
import cv2
import time
import pandas as pd



app = Flask(__name__)


app.secret_key = "ONealalsf23p9e"
app.config['SESSION_COOKIE_NAME'] = 'Temp Cookie'
TOKEN_INFO = "token_info"


#Default training data provided by CV2 for facial recog
cascPath = pathlib.Path(cv2.__file__).parent.absolute() / 'data/haarcascade_frontalface_default.xml'
faceCascade = cv2.CascadeClassifier(str(cascPath))
video_capture = cv2.VideoCapture(0)


# def camera():
#
#     #Run for 10 seconds
#     t_end = time.time() + 20
#
#     #Keep capturing till time over
#     while time.time() < t_end:
#     # While cam is on
#     #while True:
#         # Capture frame-by-frame
#         ret, frame = video_capture.read()
#         result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
#         #print(result)
#
#         # Color scale
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#
#         faces = faceCascade.detectMultiScale(
#             gray,
#             scaleFactor=1.1,
#             minNeighbors=5,  # Things not facial
#             minSize=(30, 30),
#             flags=cv2.CASCADE_SCALE_IMAGE
#         )
#
#         # Draw a rectangle around the faces
#         for (x, y, w, h) in faces:
#             cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
#
#             cv2.putText(frame, result[0]['dominant_emotion'], (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12),
#                         2)
#
#         #cv2.imshow('Emotion', frame)
#
#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame=buffer.tobytes()
#
#         yield (b'--frame\r\n'
#                     b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#
#     # When everything is done, release the capture
#     video_capture.release()
#     cv2.destroyAllWindows()


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
    return redirect("/queue-display")


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







# @app.route('/')
# def queue():
#     results = spotipy.album_tracks('album_id') # Replace 'album_id' with the ID of the album you want to display
#
#     songs = []
#     for track in results['items']:
#         song = {
#             'name': track['name'],
#             'artist': track['artists'][0]['name'],
#             'image': track['album']['images'][0]['url']
#         }
#         songs.append(song)
#
#     return render_template('index.html', songs=songs)






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



if __name__ == '__main__':
    app.run(debug=True)
