import sqlite3

class User:
    def __init__(self, username, pwd_hash, id):
        self.id = id
        self.username = username
        self.pwd_hash = pwd_hash

class Post:
    def __init__(self, data, id, language, user):
        self.data = data
        self.language = language
        self.user = user

class Db:
    def __init__(self):
        self.con = sqlite3.connect("database.db")
        self.con.execute("PRAGMA foreign_keys = ON")

    def get_user_by_username(self, username):
        query = """SELECT * FROM Users WHERE name=?"""
        values = self.con.execute(query, [username]).fetchone()
        if values:
            return User(values[1], values[2], values[0])
        return None

    def create_user(self, username, pwd_hash):
        query = """INSERT INTO Users (name, pwd_hash) VALUES (?, ?)"""
        self.con.execute(query, [username, pwd_hash])
        self.con.commit()
    
    def create_post(self, data, language_id, user_id):
        query = """INSERT INTO Posts (data, language, user_id) VALUES (?, ?, ?)"""
        self.con.execute(query, [data, language_id, user_id])
        self.con.commit()
    
    def get_languages(self):
        query = """SELECT name FROM Languages"""
        results = self.con.execute(query).fetchall()
        if not results:
            results = []
        results = map(lambda x: x[0], results)
        return results
    
    def get_language_id(self, name):
        query = """SELECT id FROM Languages WHERE name = ?"""
        result = self.con.execute(query, [name]).fetchone()
        return result[0]
    
        