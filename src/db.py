import sqlite3

class User:
    def __init__(self, username, pwd_hash, id):
        self.id = id
        self.username = username
        self.pwd_hash = pwd_hash

class Db:
    def __init__(self):
        self.con = sqlite3.connect("database.db")
        self.con.execute("PRAGMA foreign_keys = ON")

    def get_user_by_username(self, username):
        query = """SELECT * FROM Users WHERE name=?"""
        values = self.con.execute(query, [username]).fetchone()
        return User(values[1], values[2], values[0])

    def create_user(self, username, pwd_hash):
        query = """INSERT INTO Users (name, pwd_hash) VALUES (?, ?)"""
        self.con.execute(query, [username, pwd_hash])
        self.con.commit()