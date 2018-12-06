import sqlite3

pass_hash = "c5e2246876b3bc887ad2cda0320a8f0790ccd4fc2eb667e28a9f9129308ee3364be877735c63973e967af54f86d4d70bdf3d5509f1446b8af095ef0264b43273"

conn = sqlite3.connect("run/src/models/datastores/backup.db")
cur = conn.cursor()

SQL = """
SELECT DISTINCT username FROM metadata;"""
cur.execute(SQL)
results = cur.fetchall()
cur.close()
conn.close()

conn = sqlite3.connect("run/src/models/datastores/master.db")
cur = conn.cursor()

for i in results:
    SQL = """
    INSERT INTO users(username, passhash, tweet_count)
    VALUES (?, ?, ?);"""
    cur.execute(SQL, (i[0], pass_hash, 0))
    
SQL = """
SELECT username, pk FROM users;"""
cur.execute(SQL)
results = cur.fetchall()

for i in results:
    SQL = """
    INSERT INTO friends(user_pk, friend_pk)
    VALUES (?, ?);"""
    cur.execute(SQL, (i[1], i[1]))

names_pks = {}
for i in results:
    names_pks[i[0]] = i[1]

conn.commit()
cur.close()
conn.close()


conn = sqlite3.connect("run/src/models/datastores/backup.db")
cur = conn.cursor()

SQL = """
SELECT username, text, timestamp, image_pathname, ipfs_hash
FROM metadata;"""
cur.execute(SQL)
results = cur.fetchall()
cur.close()
conn.close()

conn = sqlite3.connect("run/src/models/datastores/master.db")
cur = conn.cursor()

for i in results:
    SQL = """
    INSERT INTO tweets(content, time, image_pathname, ipfs_hash, user_pk)
    VALUES (?, ?, ?, ?, ?);"""
    cur.execute(SQL, (i[1], i[2], i[3], i[4], names_pks[i[0]]))
conn.commit()
cur.close()
conn.close()
