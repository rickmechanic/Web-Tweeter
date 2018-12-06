import sqlite3

conn = sqlite3.connect('run/src/models/datastores/master.db')
cur = conn.cursor()

SQL = """DROP TABLE IF EXISTS users;"""
cur.execute(SQL)
SQL = """DROP TABLE IF EXISTS tweets;"""
cur.execute(SQL)
SQL = """DROP TABLE IF EXISTS friends;"""
cur.execute(SQL)

SQL = """
CREATE TABLE users(
    pk INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR,
    passhash VARCHAR,
    tweet_count INTEGER
);"""
cur.execute(SQL)

SQL = """
CREATE TABLE tweets(
    pk INTEGER PRIMARY KEY AUTOINCREMENT,
    content VARCHAR,
    time INTEGER,
    image_pathname VARCHAR,
    ipfs_hash VARCHAR,
    user_pk INTEGER,
    FOREIGN KEY(user_pk) REFERENCES users(pk)
);"""
cur.execute(SQL)

SQL = """
CREATE TABLE friends(
    user_pk INTEGER,
    friend_pk INTEGER
);"""
cur.execute(SQL)