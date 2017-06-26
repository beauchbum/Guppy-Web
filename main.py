import json
from flask import Flask, request, redirect, g, render_template, make_response, url_for, session, flash
import requests
import requests_toolbelt.adapters.appengine

import base64
import urllib2
import urllib
from datetime import timedelta
import json
import os


# Authentication Steps, paramaters, and responses are defined at https://developer.spotify.com/web-api/authorization-guide/
# Visit this url to see all the steps, parameters, and expected response.

app = Flask(__name__)
app.config.update(
    SEND_FILE_MAX_AGE_DEFAULT=3600
)


#  Client Keys
CLIENT_ID = "57b61875218e4e1f8a8d0cdb57a7259b"
CLIENT_SECRET = "1b705460a08a48d1b4c94a17c7d37aff"

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)
IP = "34.211.42.62"

ACCESS_TOKEN = ""

# Server-side Parameters
if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
    REDIRECT_URI = "https://guppy-web.appspot.com/callback/q"
    requests_toolbelt.adapters.appengine.monkeypatch()

else:
    CLIENT_SIDE_URL = "http://127.0.0.1"
    PORT = 8000
    REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
#REDIRECT_URI = "sync-me-up://callback"
SCOPE = "playlist-modify-public playlist-modify-private user-read-playback-state user-modify-playback-state user-read-recently-played"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

UNKNOWN = "User Unknown"

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

@app.before_request
def make_session_permanent():
    print "session made perm"
    session.permanent = True


@app.route("/", methods=["POST", "GET"])
def index():

    if "sid" in session:
        following = []
        search = False
        search_results = []
        me = {}
        my_devices = []
        my_listeners = []
        url = "http://" + IP + "/get_guppy_id_2.php?spotify_id=%s" % (session['sid'])
        result = urllib2.urlopen(url)
        data = json.load(result)
        if data['success'] == 1:
            user = data['user'][0]
            my_gid = user['guppy_id']
            session["gid"] = my_gid
            fb_token_valid = int(user['fb_token_valid'])
            my_prof_pic = user['prof_pic']
            if my_prof_pic == "":
                my_prof_pic = user["fb_prof_pic"]
            my_song = user['song']
            my_artist = user['artist']
            my_playing = user['playing']
            listening_gid = user["id"]
            me = {"my_gid":my_gid, "fb_token_valid":fb_token_valid, "my_prof_pic":my_prof_pic, "my_song":my_song, "my_artist": my_artist, "my_playing":my_playing, "listening_gid": listening_gid}
            listening = []

            url = "http://" + IP + "/get_listeners.php?gid=%s" % (my_gid)
            result = urllib2.urlopen(url)
            data = json.load(result)
            if data["success"] == 1:
                listeners = data["listeners"]
                for l in listeners:
                    my_listener_name = l['name']
                    if my_listener_name == "None":
                        my_listener_name = l['fb_name']
                    my_listener_gid = l['gid']
                    my_listener_prof_pic = l['prof_pic']
                    if my_listener_prof_pic == "":
                        my_listener_prof_pic = l['fb_prof_pic']
                    my_listeners.append({"gid":my_listener_gid, "name":my_listener_name, "prof_pic":my_listener_prof_pic, "following":int(l["following"])})



            if listening_gid is not None:
                url = "http://" + IP + "/get_listening_state.php?gid=%s" % (listening_gid)
                result = urllib2.urlopen(url)
                data = json.load(result)
                users = data["users"]
                for u in users:
                    listening_name = u['name']
                    if listening_name == "None":
                        listening_name = u['fb_name']
                    listening_prof_pic = u['prof_pic']
                    if listening_prof_pic == "":
                        listening_prof_pic = u['fb_prof_pic']
                    listening_prof_url = u['prof_url']
                    listening_artist = u['artist']
                    listening_song = u['song']
                    listening_playing = int(u['playing'])
                    listening.append({"gid": listening_gid, "name": listening_name, "prof_pic": listening_prof_pic,
                                      "prof_url": listening_prof_url, "artist": listening_artist,
                                      "song": listening_song, "playing":listening_playing})



            url = "http://" + IP + "/get_devices.php?gid=%s" % (my_gid)
            result = urllib2.urlopen(url)
            data = json.load(result)


            if data["success"] == 1:
                devices = data["devices"]
            else:
                devices = []
            my_name = user['name']
            url = "http://" + IP + "/get_following_2.php?current_user_id=%s" % (my_gid)
            result = urllib2.urlopen(url)
            data = json.load(result)

            if data['success'] == 1:
                following = []
                users = data['users']
                for u in users:
                    following_gid = u['guppy_id']
                    following_name = u['name']
                    if following_name == "None":
                        following_name = u['fb_name']
                    following_prof_pic = u['prof_pic']
                    if following_prof_pic == "":
                        following_prof_pic = u['fb_prof_pic']
                    following_prof_url = u['prof_url']
                    following_artist = u['artist']
                    following_song = u['song']
                    following_playing = int(u["playing"])
                    following_listening = int(u["listening"])
                    following_listening_id = u["listening_id"]
                    following_listening_status = 0
                    following_listener = 0
                    if following_listening_id is not None:
                        following_listening_status = 1
                        following_listener = int(u["following_listener"])

                    following_listening_name =u["listening_name"]
                    following_listening_prof = u["listening_prof"]
                    following.append({"gid":following_gid, "name":following_name, "prof_pic":following_prof_pic, "prof_url":following_prof_url, "artist":following_artist, "song":following_song, "playing":following_playing,
                                          "listening":following_listening, "listening_status": following_listening_status, "following":int(u["following"]),
                                            "following_listener":following_listener, "listening_gid": following_listening_id, "listening_name":following_listening_name, "listening_prof":following_listening_prof})
                if "search" in session:
                    if session["search"] == True:
                        search = session["search"]
                        search_term = session["search_term"] + "%"
                        session.pop('search', None)
                        session.pop('search_term', None)
                        url = "http://" + IP + "/search_users.php?search_term=%s&my_gid=%s" % (search_term,my_gid)
                        result = urllib2.urlopen(url)
                        data = json.load(result)

                        if data["success"] == 1:
                            users = data["users"]
                            for u in users:
                                name = u["name"]
                                if name == "None":
                                    name = u["fb_name"]
                                prof_pic = u["prof_pic"]
                                if prof_pic == "":
                                    prof_pic = u["fb_prof_pic"]
                                search_listening_status = 0
                                search_following_listener = 0
                                if u["listening_id"] is not None:
                                    search_listening_status = 1
                                    search_following_listener = int(u["following_listener"])
                                search_result = {"gid":u["guppy_id"], "name":name, "song":u["song"], "artist":u["artist"], "uri":u["uri"], "playing":u["playing"], "prof_pic":prof_pic, "following":int(u["following"]),
                                                 "listening":int(u["listening"]), "listening_status":search_listening_status, "listening_id":u["listening_id"], "listening_name":u["listening_name"],
                                                 "following_listener":search_following_listener, "listening_prof":u["listening_prof"]}
                                search_results.append(search_result)

        print search
        return render_template("index.html", logged=True, following=following, me=me, devices=devices, listening=listening, my_listeners=my_listeners, search=search, search_results=search_results)
    else:
        following = []
        search = False
        my_devices = []
        listening = []
        return render_template("index.html", logged=False, following=following, my_name=UNKNOWN, listening=listening, search=search)




@app.route("/authorize")
def authorize():
    # Auth Step 1: Authorization
    url_args = "&".join(["{}={}".format(key,urllib.quote(val)) for key,val in auth_query_parameters.iteritems()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)

@app.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
    }
    base64encoded = base64.b64encode("{}:{}".format(CLIENT_ID, CLIENT_SECRET))
    headers = {"Authorization": "Basic {}".format(base64encoded)}
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization":"Bearer {}".format(access_token)}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)


    # Combine profile and playlist data to display
    #display_arr = [profile_data] + playlist_data["items"]

    sid = profile_data['id']
    name = profile_data['display_name']
    prof_url = profile_data['external_urls']['spotify']
    try:
        prof_pic = profile_data['images'][0]['url']
    except IndexError:
        prof_pic = ""

    if name is None:
        name = "None"


    session["sid"] = sid
    url = "http://" + IP + "/create_user.php"
    data = urllib.urlencode({'name': name, 'profile_url':prof_url, 'id':sid, 'prof_pic':prof_pic, 'access_token':access_token, 'refresh_token':refresh_token})
    result = urllib2.urlopen(url, data)
    url = "http://" + IP + "/update_user.php"
    result = urllib2.urlopen(url, data)
    url = "http://" + IP + "/get_guppy_id.php?spotify_id=%s" % (session['sid'])
    result = urllib2.urlopen(url)
    data = json.load(result)
    if data['success'] == 1:
        user = data['user'][0]
        my_gid = user['guppy_id']
    url = "http://" + IP + "/refresh_my_devices.php?gid=%s" % (my_gid)
    result = urllib2.urlopen(url)


    return redirect(url_for('index'))


@app.route('/tune_in', methods=["POST"])
def tune_in():

    if "tune_in_their_gid" in request.form:
        tune_in_their_gid = request.form["tune_in_their_gid"]
        #device_id = request.form["device_select"]
        tune_in_my_gid = request.form["tune_in_my_gid"]
        tune_in_anonymous = request.form.getlist("anonymous")
        if len(tune_in_anonymous) > 0:
            tune_in_anonymous = 1
        else:
            tune_in_anonymous = 0

        url = "http://" + IP + "/start_playback_2.php"
        temp_data = urllib.urlencode(
            {'my_gid': str(tune_in_my_gid), 'their_gid': str(tune_in_their_gid),'anonymous': str(tune_in_anonymous)})
        result = urllib2.urlopen(url, temp_data)
        data = json.load(result)
        if data["success"] == 0:

            if data["error"] == 404 or data["error"] == 403 or data["error"] == -1:
                flash(u'Tried to play, but there is no active device. Open Spotify.', category='danger')
            else:
                print "ERROR TUNING IN" + str(data["error"])
        else:
            print data
            flash(u'Success! Playing on %s' % (str(data["device_name"])), category='success')



    return redirect(url_for('index'))


@app.route('/tune_out', methods=["POST"])
def tune_out():
    if "tune_out_my_gid" in request.form:
        tune_out_my_gid = request.form["tune_out_my_gid"]
        url = "http://" + IP + "/stop_playback.php?my_gid=%s" % (tune_out_my_gid)
        result = urllib2.urlopen(url)
    return redirect(url_for('index'))


@app.route('/refresh_devices', methods=["POST", "GET"])
def refresh_devices():
    if "gid" in session:
        refresh_my_gid = session["gid"]
        url = "http://" + IP + "/refresh_my_devices.php?gid=%s" % (refresh_my_gid)
        result = urllib2.urlopen(url)
    return redirect(url_for('index'))

@app.route('/refresh_fb_friends', methods=["POST", "GET"])
def refresh_fb_friends():
    if "gid" in session:
        refresh_fb_gid = session["gid"]
        url = "http://" + IP + "/update_my_fb_friends.php?gid=%s" % (refresh_fb_gid)
        result = urllib2.urlopen(url)
    return redirect(url_for('index'))


@app.route('/fb_login', methods=["POST", "GET"])
def fb_login():
    if "fbLoginToken" in request.form:
        if "gid" in session:
            fb_gid = session["gid"]
            fb_token = request.form["fbLoginToken"]
            fb_id = request.form["fbLoginId"]
            url = "http://" + IP + "/set_facebook_account.php?token=%s&fb_id=%s&my_gid=%s" % (fb_token, fb_id, fb_gid)
            urllib2.urlopen(url)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('sid', None)
    return redirect(url_for('index'))


@app.route("/follow", methods=["GET"])
def follow():
    follow_my_gid = request.args['my_gid']
    follow_their_gid = request.args['their_gid']
    url = "http://" + IP + "/follow_user.php?followed_id=%s&follower_id=%s" % (follow_their_gid, follow_my_gid)
    result = urllib2.urlopen(url)
    return ""

@app.route("/unfollow", methods=["GET"])
def unfollow():
    print "Unfollow"
    unfollow_my_gid = request.args['my_gid']
    unfollow_their_gid = request.args['their_gid']
    print unfollow_my_gid
    print unfollow_their_gid
    url = "http://" + IP + "/unfollow_user.php?followed_id=%s&follower_id=%s" % (unfollow_their_gid, unfollow_my_gid)
    result = urllib2.urlopen(url)
    return ""

@app.route("/search", methods=["POST"])
def search():
    search = False
    if "search" in request.form:
        if request.form["search"] != "":
            search = True
            search_term = request.form["search"]
            session["search"] = search
            session["search_term"] = search_term

    return redirect(url_for('index'))


app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__ == "__main__":
    app.run(debug=True,port=PORT)