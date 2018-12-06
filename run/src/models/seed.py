import sqlite3
from time import time
from hashlib import sha512

SALT = "!$m33gl3d33g"

def calculate_hash(string):
    hashobject = sha512()
    saltedstring = (string + SALT).encode()
    hashobject.update(saltedstring)
    return hashobject.hexdigest()

conn = sqlite3.connect("run/src/models/datastores/master.db")
cur = conn.cursor()

SQL = """INSERT INTO users(username, passhash, tweet_count)
VALUES(?, ?, ?);"""
pw_hash = calculate_hash("password")
cur.execute(SQL, ("Rick", pw_hash, 1))

SQL = """INSERT INTO users(username, passhash, tweet_count)
VALUES(?, ?, ?);"""
pw_hash = calculate_hash("password")
cur.execute(SQL, ("Jake", pw_hash, 1))

SQL = """INSERT INTO users(username, passhash, tweet_count)
VALUES(?, ?, ?);"""
pw_hash = calculate_hash("password")
cur.execute(SQL, ("Andie", pw_hash, 1))

SQL = """INSERT INTO tweets(content, time, user_pk) 
VALUES(?, ?, ?);"""
cur.execute(SQL, ("Rick's first tweet", int(time()), 1))

SQL = """INSERT INTO tweets(content, time, user_pk) 
VALUES(?, ?, ?);"""
cur.execute(SQL, ("Jake's first tweet", int(time()), 2))

conn.commit()
cur.close()
conn.close()