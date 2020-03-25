from flask import Flask, redirect, request, send_file, render_template, Response, jsonify
from flask_restful import Api, Resource, reqparse
from urllib.parse import quote_plus
from base64 import b64encode, b64decode
import requests
import slack

SPOTIFY_APP_CLIENT_ID = "SPOTIFY_APP_CLIENT_ID"
SPOTIFY_APP_CLIENT_SECRET = "SPOTIFY_APP_CLIENT_SECRET"
SLACK_BOT_CLIENT_ID = "SLACK_BOT_CLIENT_ID"
SLACK_BOT_CLIENT_SECRET = "SLACK_BOT_CLIENT_SECRET"

app = Flask(__name__)
api = Api(app)

def callback_parser():
    parser = reqparse.RequestParser()
    parser.add_argument('code')
    return parser

@app.route('/getRefreshForSpotify/<token>', methods=['GET'])
def refresh(token):
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": token
    }
    token_bytes = str(SPOTIFY_APP_CLIENT_ID + ":" + SPOTIFY_APP_CLIENT_SECRET).encode('ascii')
    b64_bytes = b64encode(token_bytes)
    b64token = b64_bytes.decode('ascii')
    headers = { "Authorization": "Basic " + b64token}
    res = requests.post(url, data=data, headers=headers).json()
    return jsonify(res), 200
    

@app.route('/authorize', methods=['GET'])
def authorize():
    url = "https://accounts.spotify.com/authorize"
    formed_url = url + "?client_id=" + SPOTIFY_APP_CLIENT_ID + "&response_type=code&redirect_uri=" + quote_plus("REDIRECT_URL") + "&show_dialog=true&scope=" + quote_plus("user-read-playback-state user-read-currently-playing")
    return redirect(formed_url, 302)

@app.route('/authorize_slack', methods=['GET'])
def auth_slack():
    url = "https://slack.com/oauth/authorize"
    formed_url = url + "?scope=users.profile:write&client_id=" + SLACK_BOT_CLIENT_ID + "&redirect_uri=" + quote_plus("REDIRECT_URL")
    return redirect(formed_url, 302)

class CallbackSlack(Resource):
    def get(self):
        parser = callback_parser()
        args = parser.parse_args()
        code = args['code']
        client = slack.WebClient(token="")
        response = client.oauth_access(
            client_id=SLACK_BOT_CLIENT_ID,
            client_secret=SLACK_BOT_CLIENT_SECRET,
            code=code,
            redirect_uri="REDIRECT_URL"
        )
        response = Response(render_template('slack.html', slack_token=response['access_token']), 200, {"Content-Type": "text/html"})
        return response

class CallbackCode(Resource):
    def get(self):
        parser = callback_parser()
        args = parser.parse_args()
        code = args['code']
        auth_code_url = "https://accounts.spotify.com/api/token"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "scope": "user-read-currently-playing user-read-playback-state",
            "redirect_uri": "REDIRECT_URL"
        }
        token_bytes = str(SPOTIFY_APP_CLIENT_ID + ":" + SPOTIFY_APP_CLIENT_SECRET).encode('ascii')
        b64_bytes = b64encode(token_bytes)
        b64token = b64_bytes.decode('ascii')
        headers = { "Authorization": "Basic " + b64token}
        res = requests.post(auth_code_url, data=data, headers=headers).json()
        access_code = res['access_token']
        refresh_code = res['refresh_token']
        response = Response(render_template('index.html', spotify_token=access_code, spotify_rtoken=refresh_code), 200, {"Content-Type": "text/html"})
        return response
    
@app.route("/assets/<folder>/<filename>")
def css(folder, filename):
    return send_file('templates/assets/' + folder + "/" + filename), 200

@app.route("/assets/sass/<folder>/<filename>")
def sasss(folder, filename):
    return send_file('templates/assets/sass' + folder + "/" + filename), 200
    
    
api.add_resource(CallbackCode, '/callback_code')
api.add_resource(CallbackSlack, '/callback_slack')