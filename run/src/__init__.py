#!/usr/bin/env python3

from flask import Flask, request, redirect, session, render_template, url_for, send_from_directory
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from .models import model
import locale
from datetime import datetime
import tzlocal
from os import path

app = Flask(__name__)
app.secret_key = b'thesessionneedsthis'

local_timezone = tzlocal.get_localzone()
locale.setlocale(locale.LC_ALL, 'en_US')

# login_manager = LoginManager()
# login_manager.init_app(app)
# login.login_view = 'login'
# login_manager.login_message_category = "you must be signed in to view this page"

# @login_manager.user_loader
# def load_user(pk):
#     user = model.User()
#     user.set_from_pk(pk)
#     return user

@app.route('/', methods=["GET"])
def send_to_alltweets():
	return redirect(url_for('alltweets'))

@app.route('/alltweets', methods=["GET"])
def alltweets():
    user = model.User()
    alltweets = user.get_all_tweets()
    tweets = {}
    tweets["usernames"] = [i.username for i in alltweets]
    tweets["contents"] = [i.content for i in alltweets]
    tweets["pathnames"] = []
    tweets["times"] = [str(datetime.fromtimestamp(i.time, local_timezone))[0:-6] for i in alltweets]
    for i in alltweets:
        try:
            with open("static/{}".format(i.pathname),'r') as f:
                tweets["pathnames"].append(i.pathname)
        except IOError:
            tweets["pathnames"].append("https://ipfs.io/ipfs/{}".format(i.ipfshash))
    length = range(0, len(tweets["contents"]))
    return render_template('unauthorized/alltweets.html', tweets=tweets, length=length)

@app.route('/createaccount', methods=["GET","POST"])
def createaccount():
    if request.method == "GET":
        return render_template('unauthorized/createaccount.html')
    elif request.method == "POST":
        user = model.User()
        username = request.form["username"]
        if not user.username_exists_check(username):
            return render_template('unauthorized/createaccount.html', message="Username already exists")
        password = request.form["password"]
        if not model.password_check(password):
            return render_template('unauthorized/createaccount.html', message="Password must be 8 characters long and include 1 number")  
        password2 = request.form["password2"]
        if password2 != password:
            return render_template('/unauthorized/createaccount.html', message="Passwords don't match. Try again")
        user = model.User(username=username, passhash=model.calculate_hash(password))
        user.save()
        user.follow_self()
        return render_template('unauthorized/login.html', success_message="Account created!")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template('unauthorized/login.html')
    else:
        try:
            user = model.User()
            username = request.form["username"]
            password = model.calculate_hash(request.form["password"])
            user.set_from_credentials(username=username, password=password)
        except:
            user = None
        if not user:
            return render_template('unauthorized/login.html', message="Incorrect username or password")
        # login_user(user)
        session["Active User"] = user.pk
        return redirect(url_for('timeline'))

@app.route('/timeline', methods=["GET", "POST"])
def timeline():
    if request.method == "GET":
        user = model.User()
        user.set_from_pk(session["Active User"])
        timeline = user.get_timeline()
        tweets = {}
        tweets["tweet_pks"] = [i.tweet_pk for i in timeline]
        tweets["usernames"] = [i.username for i in timeline]
        tweets["contents"] = [i.content for i in timeline]
        tweets["pathnames"] = []
        tweets["times"] = [str(datetime.fromtimestamp(i.time, local_timezone))[0:-6] for i in timeline]
        for i in timeline:
            try:
                with open("static/{}".format(i.pathname),'r') as f:
                    tweets["pathnames"].append(i.pathname)
            except IOError:
                tweets["pathnames"].append("https://ipfs.io/ipfs/{}".format(i.ipfshash))
        length = range(0, len(tweets["contents"]))
        if tweets["tweet_pks"] == []:
            return render_template('authorized/timeline.html', tweets=tweets, length=length, message="Find users to follow in the 'Follow' tab!")
        return render_template('authorized/timeline.html', tweets=tweets, length=length)
    else:
        user = model.User()
        user.set_from_pk(session["Active User"])
        tweet_pk = request.form["retweet"]
        tweet = model.Tweet()
        tweet.set_from_pk(tweet_pk)
        print(tweet.pathname, tweet.ipfshash)
        user.record_tweet(tweet=tweet.content, pathname=tweet.pathname, ipfshash=tweet.ipfshash)
        return redirect(url_for('tweetsuccess'))

@app.route('/posttweet', methods=["GET", "POST"])
def mainpage():
    user = model.User()
    user.set_from_pk(session["Active User"])
    if request.method == "GET":
        return render_template('authorized/posttweet.html')
    else:
        tweet = request.form["tweet"]
        user.record_tweet(tweet)
        return redirect(url_for('tweetsuccess'))

@app.route('/tweetsuccess', methods=["GET"])
def tweetsuccess():
    user = model.User()
    user.set_from_pk(session["Active User"])
    last_tweet = user.get_last_tweet()
    tweet = {}
    tweet["content"] = last_tweet[0]
    tweet["pathname"] = []
    tweet["time"] = str(datetime.fromtimestamp(last_tweet[1], local_timezone))[0:-6]
    try:
        with open("static/{}".format(last_tweet[2]),'r') as f:
            tweet["pathname"].append(last_tweet[2])
    except IOError:
        tweet["pathname"].append("https://ipfs.io/ipfs/{}".format(last_tweet[3]))
    return render_template('authorized/tweetsuccess.html', tweet=tweet)

@app.route('/seetweets', methods=["GET"])
def seetweets():
    user = model.User()
    user.set_from_pk(session["Active User"])
    alltweets = user.get_tweets()
    tweets = {}
    tweets["contents"] = [i.content for i in alltweets]
    tweets["times"] = [str(datetime.fromtimestamp(i.time, local_timezone))[0:-6] for i in alltweets]
    tweets["pathnames"] = []
    for i in alltweets:
        try:
            with open("static/{}".format(i.pathname),'r') as f:
                tweets["pathnames"].append(i.pathname)
        except IOError:
            if not i.ipfshash:
                tweets['pathnames'].append(None)
            else:
                tweets["pathnames"].append("https://ipfs.io/ipfs/{}".format(i.ipfshash))
    length = range(0, len(tweets["contents"]))
    return render_template('authorized/seetweets.html', tweets=tweets, length=length)

@app.route('/addfriends', methods=["GET", "POST"])
def addfriends():
    if request.method == "GET":
        user = model.User()
        user.set_from_pk(session["Active User"])
        allusers = user.see_users()
        users = {}
        users["pks"] = [i.pk for i in allusers]
        users["usernames"] = [i.username for i in allusers]
        length = range(0, len(users["pks"]))
        return render_template("authorized/addfriends.html", users=users, length=length)
    if request.method == "POST":
        user = model.User()
        user.set_from_pk(session["Active User"])
        allusers = user.see_users()
        users = {}
        users["pks"] = [i.pk for i in allusers]
        users["usernames"] = [i.username for i in allusers]
        length = range(0, len(users["pks"]))
        friend = int(request.form["follow"])
        if not user.add_friend(friend):
            friend_name = user.get_friend_name(friend)
            return render_template("authorized/addfriends.html", users=users, length=length, fail_message="You already follow {}".format(friend_name))
        else:
            friend_name = user.get_friend_name(friend)
            return render_template("authorized/addfriends.html", users=users, length=length, success_message="Now following {}!".format(friend_name))

@app.route('/logout', methods=["GET"])
def logout():
    session.pop("Active User")
    # logout_user()
    return redirect(url_for('login'))


