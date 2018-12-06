import sqlite3
from time import time
from datetime import datetime
from hashlib import sha512
from flask_login.mixins import UserMixin

db_name = "run/src/models/datastores/master.db"

SALT = "!$m33gl3d33g"

def calculate_hash(string):
    hashobject = sha512()
    saltedstring = (string + SALT).encode()
    hashobject.update(saltedstring)
    return hashobject.hexdigest()

def password_check(password):
    if len(password) < 8:
        return False
    for i in password:
        if i.isdigit():
            return True
    return False

class OpenCursor:
    def __init__(self, db=db_name, *args, **kwargs):
        self.conn = sqlite3.connect(db, *args, **kwargs)
        self.conn.row_factory = sqlite3.Row  # access fetch results by col name
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self.cursor

    def __exit__(self, extype, exvalue, extraceback):
        if not extype:
            self.conn.commit()
        self.cursor.close()
        self.conn.close()

class User(UserMixin):
    def __init__(self, pk=None, username=None, passhash=None, tweet_count=None):
        self.pk = pk
        self.username = username
        self.passhash = passhash
        self.tweet_count = tweet_count
    
    def __bool__(self):
        return bool(self.pk)
    
    def save(self):
        with OpenCursor() as cur:
            if not self.pk:
                SQL = """
                INSERT INTO users(username, passhash, tweet_count)
                VALUES(?, ?, ?);"""
                cur.execute(SQL, (self.username, self.passhash, 0))
                self.pk = cur.lastrowid
            else:
                SQL = """
                UPDATE users SET username=?, passhash=?, tweet_count=? WHERE
                pk=?;"""
                cur.execute(SQL, (self.username, self.passhash, self.tweet_count, self.pk))
    
    def follow_self(self):
        with OpenCursor() as cur:
            SQL = """
            INSERT INTO friends(user_pk, friend_pk)
            VALUES(?, ?);"""
            cur.execute(SQL, (self.pk, self.pk))

    def username_exists_check(self, username):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM users WHERE username=?;"""
            cur.execute(SQL, (username,))
            row = cur.fetchone()
            if row:
                return False
        return True
    
    def set_from_pk(self, pk):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM users WHERE pk=?"""
            cur.execute(SQL, (pk,))
            row = cur.fetchone()
        return self.set_from_row(row)

    def set_from_credentials(self, username, password):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM users WHERE username=? AND passhash=?"""
            cur.execute(SQL, (username, password))
            row = cur.fetchone()
            if not row:
                return self
            self.set_from_row(row)
        return self
    
    def set_from_row(self, row):
        self.pk = row["pk"]
        self.username = row["username"]
        self.passhash = row["passhash"]
        self.tweet_count = row["tweet_count"]
        return self
    
    def tweet_from_row(self, row):
        self.pk = row["pk"]
        self.content = row["content"]
        self.time = row["time"]
        self.user_pk = row["user_pk"]
        return self

    def set_from_friend(self, row):
        self.pk = row["pk"]
        self.username = row["username"]
        return self
    
    def set_from_friend_username(self, row):
        self.username = row["username"]
        return self
    
    def record_tweet(self, tweet, pathname=None, ipfshash=None):
        with OpenCursor() as cur:
            SQL = """
            INSERT INTO tweets(content, time, image_pathname, ipfs_hash, user_pk)
            VALUES (?, ?, ?, ?, ?);"""
            cur.execute(SQL, (tweet, int(time()), pathname, ipfshash, self.pk))
            self.tweet_count = self.tweet_count + 1
        self.save()
    
    def get_tweets(self):
        with OpenCursor() as cur:
            SQL = """
            SELECT content, time, image_pathname, ipfs_hash FROM tweets WHERE user_pk=? ORDER BY time DESC;"""
            cur.execute(SQL, (self.pk,))
            rows = cur.fetchall()
            results = []
            for row in rows:
                tweet = Tweet()
                tweet.set_from_row(row)
                results.append(tweet)
        return results
    
    def get_last_tweet(self):
        with OpenCursor() as cur:
            SQL = """
            SELECT content, time, image_pathname, ipfs_hash FROM tweets WHERE user_pk=? ORDER BY time DESC;"""
            cur.execute(SQL, (self.pk,))
            row = cur.fetchone()
            tweet = Tweet()
            tweet.set_from_row(row)
            result = [tweet.content, tweet.time, tweet.pathname, tweet.ipfshash]
        return result
    
    def get_all_tweets(self):
        with OpenCursor() as cur:
            SQL = """
            SELECT content, time, image_pathname, ipfs_hash, username FROM tweets JOIN users ON users.pk = tweets.user_pk ORDER BY time DESC;"""
            cur.execute(SQL)
            rows = cur.fetchall()
            results = []
            for row in rows:
                tweet = Tweet()
                tweet.set_from_row_alltweets(row)
                results.append(tweet)
        return results
    
    def get_timeline(self):
        with OpenCursor() as cur:
            SQL = """
            SELECT t.pk, t.content, t.time, t.image_pathname, t.ipfs_hash, u.username
            FROM tweets t
            JOIN users u
                ON u.pk = t.user_pk 
            JOIN friends f
                ON f.friend_pk = u.pk
            WHERE f.user_pk = ?
            ORDER BY time DESC;"""
            cur.execute(SQL, (self.pk,))
            rows = cur.fetchall()
            results = []
            for row in rows:
                tweet = Tweet()
                tweet.set_from_row_timeline(row)
                results.append(tweet)
        return results
    
    def retweet(self, tweet_pk):
        with OpenCursor() as cur:
            SQL = """
            SELECT * from tweets
            WHERE pk = ?;"""
            cur.execute(SQL, (tweet_pk,))
            row = cur.fetchone()
            tweet = Tweet()
            tweet.set_from_row(row)
        return tweet

    def see_users(self):
        with OpenCursor() as cur:
            SQL = """
            SELECT pk, username FROM users WHERE pk != ?;"""
            cur.execute(SQL, (self.pk,))
            rows = cur.fetchall()
            results = []
            for row in rows:
                user = User()
                user.set_from_friend(row)
                results.append(user)
        return results
    
    def add_friend(self, friendpk):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM friends WHERE user_pk = ? AND friend_pk = ?;"""
            cur.execute(SQL, (self.pk, friendpk)) 
            row = cur.fetchone()
            if not row:  
                SQL = """
                INSERT INTO friends(user_pk, friend_pk) VALUES (?, ?);"""
                cur.execute(SQL, (self.pk, friendpk))
                return True
            else:
                return False

    def get_friend_name(self, friendpk):
        with OpenCursor() as cur:
            SQL = """
            SELECT username FROM users WHERE pk = ?;"""
            cur.execute(SQL, (friendpk,))
            row = cur.fetchone()
            friend = User()
            friend.set_from_friend_username(row)
        return friend.username

class Tweet():
    def __init__(self, content=None, time=None, pathname=None, ipfshash=None, user_pk=None):
        self.content = content
        self.time = time
        self.user_pk = user_pk
        self.pathname = pathname
        self.ipfshash = ipfshash
    
    def set_from_pk(self, tweet_pk):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM tweets where pk=?;"""
            cur.execute(SQL, (tweet_pk,))
            row = cur.fetchone()
        return self.set_from_row(row)
    
    def set_from_row(self, row):
        self.content = row["content"]
        self.time = row["time"]
        self.pathname = row["image_pathname"]
        self.ipfshash = row["ipfs_hash"]
    
    def set_from_row_alltweets(self, row):
        self.username = row["username"]
        self.content = row["content"]
        self.time = row["time"]
        self.pathname = row["image_pathname"]
        self.ipfshash = row["ipfs_hash"]
    
    def set_from_row_timeline(self, row):
        self.tweet_pk = row["pk"]
        self.username = row["username"]
        self.content = row["content"]
        self.time = row["time"]
        self.pathname = row["image_pathname"]
        self.ipfshash = row["ipfs_hash"]



    
