import sqlite3
from sqlite3 import IntegrityError


class User:
    def __init__(self, username, pwd_hash, id):
        self.id = id
        self.username = username
        self.pwd_hash = pwd_hash


class Post:
    def __init__(self, data, language, username, id, likes, comments, liked=False):
        self.data = data
        self.language = language
        self.username = username
        self.id = id
        self.likes = likes
        self.liked = liked
        self.comments = comments


class Comment:
    def __init__(self, data, id, username):
        self.data = data
        self.id = id
        self.username = username


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
        try:
            self.con.execute(query, [username, pwd_hash])
        except IntegrityError:
            self.con.commit()
            return False
        self.con.commit()
        return True

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
        if result:
            return result[0]
        return None

    def get_posts(self, limit, user_id=None):
        if user_id:
            query = """SELECT P.data, L.name, U.name, P.id, COUNT(T.id), COUNT(Z.id), \
            (SELECT COUNT(C.id) FROM Comments C WHERE C.post_id = P.id) \
            FROM Posts P LEFT JOIN Users U ON P.user_id = U.id \
            LEFT JOIN Languages L ON L.id = P.language \
            LEFT JOIN Likes T ON T.post_id = P.id \
            LEFT JOIN Likes Z ON P.id = Z.post_id AND Z.user_id = ? \
            GROUP BY P.id \
            LIMIT ?"""
            results = self.con.execute(query, [user_id, limit]).fetchall()
            results = [Post(x[0], x[1], x[2], x[3], x[4], x[6], x[5] != 0)
                       for x in results]
        else:
            query = """SELECT P.data, L.name, U.name, P.id, COUNT(T.id), \
            (SELECT COUNT(C.id) FROM Comments C WHERE C.post_id = P.id) \
            FROM Posts P LEFT JOIN Users U ON P.user_id = U.id \
            LEFT JOIN Languages L ON L.id = P.language \
            LEFT JOIN Likes T ON T.post_id = P.id \
            GROUP BY P.id \
            LIMIT ?"""
            results = self.con.execute(query, [limit]).fetchall()
            results = [Post(x[0], x[1], x[2], x[3], x[4], x[5])
                       for x in results]
        return results

    def get_post_by_id(self, id, user_id=None):
        if user_id:
            query = """SELECT P.data, L.name, U.name, P.id, COUNT(T.id), COUNT(Z.id), \
            (SELECT COUNT(C.id) FROM Comments C WHERE C.post_id = P.id) \
            FROM Posts P LEFT JOIN Languages L ON P.language = L.id \
            LEFT JOIN Users U ON U.id = P.user_id \
            LEFT JOIN Likes T ON T.post_id = P.id \
            LEFT JOIN Likes Z ON P.id = Z.post_id AND Z.user_id = ?
            WHERE P.id = ?"""
            results = self.con.execute(query, [user_id, id]).fetchone()
            if results:
                return Post(results[0], results[1], results[2], results[3], results[4], results[6], results[5] != 0)
        else:
            query = """SELECT P.data, L.name, U.name, P.id, COUNT(T.id), \
            (SELECT COUNT(C.id) FROM Comments C WHERE C.post_id = P.id) \
            FROM Posts P LEFT JOIN Languages L ON P.language = L.id \
            LEFT JOIN Users U ON U.id = P.user_id \
            LEFT JOIN Likes T ON T.post_id = P.id \
            WHERE P.id = ?"""
            results = self.con.execute(query, [id]).fetchone()
            if results:
                return Post(results[0], results[1], results[2], results[3], results[4], results[5])
        return None

    def get_posts_by_user_id(self, user_id, limit, current_user_id=None):
        if user_id:
            query = """SELECT P.data, L.name, U.name, P.id, COUNT(T.id), COUNT(Z.id), \
            (SELECT COUNT(C.id) FROM Comments C WHERE C.post_id = P.id) FROM \
            Posts P LEFT JOIN Users U ON U.id = P.user_id \
            LEFT JOIN Languages L ON L.id = P.language \
            LEFT JOIN Likes T ON T.post_id = P.id \
            LEFT JOIN Likes Z ON P.id = Z.post_id AND Z.user_id = ?
            WHERE U.id = ? \
            GROUP BY P.id \
            LIMIT ?"""
            results = self.con.execute(
                query, [current_user_id, user_id, limit]).fetchall()
            results = [Post(x[0], x[1], x[2], x[3], x[4], x[6], x[5] != 0)
                       for x in results]
        else:
            query = """SELECT P.data, L.name, U.name, P.id, COUNT(T.id), \
            (SELECT COUNT(C.id) FROM Comments C WHERE C.post_id = P.id) FROM \
            Posts P LEFT JOIN Users U ON U.id = P.user_id \
            LEFT JOIN Languages L ON L.id = P.language \
            LEFT JOIN Likes T ON T.post_id = P.id \
            WHERE U.id = ?
            GROUP BY P.id \
            LIMIT ?"""
            results = self.con.execute(query, [user_id, limit]).fetchall()
            results = [Post(x[0], x[1], x[2], x[3], x[4], x[5])
                       for x in results]
        return results

    def update_post_by_id(self, id, data, language_id):
        query = """UPDATE Posts SET data = ?, language = ? WHERE id = ?"""
        self.con.execute(query, [data, language_id, id])
        self.con.commit()

    def delete_post_by_id(self, id):
        query = """DELETE FROM Posts WHERE id = ?"""
        self.con.execute(query, [id])
        self.con.commit()

    def search_post_by_string(self, term, limit, user_id=None):
        if not term:
            term = ""
        if user_id:
            query = """SELECT P.data, L.name, U.name, P.id, COUNT(T.id), COUNT(Z.id), \
            (SELECT COUNT(C.id) FROM Comments C WHERE C.post_id = P.id) FROM \
            Posts P LEFT JOIN Users U ON U.id = P.user_id \
            LEFT JOIN Languages L ON L.id = P.language \
            LEFT JOIN Likes T ON T.post_id = P.id \
            LEFT JOIN Likes Z ON P.id = Z.post_id AND Z.user_id = ?
            WHERE LOWER(P.data) LIKE ? \
            GROUP BY P.id \
            LIMIT ?"""
            results = self.con.execute(
                query, [user_id, "%" + term.lower() + "%", limit]).fetchall()
            results = [Post(x[0], x[1], x[2], x[3], x[4], x[6], x[5] != 0)
                       for x in results]
        else:
            query = """SELECT P.data, L.name, U.name, P.id, COUNT(T.id), \
            (SELECT COUNT(C.id) FROM Comments C WHERE C.post_id = P.id) FROM \
            Posts P LEFT JOIN Users U ON U.id = P.user_id \
            LEFT JOIN Languages L ON L.id = P.language \
            LEFT JOIN Likes T ON T.post_id = P.id \
            WHERE LOWER(P.data) LIKE ? \
            GROUP BY P.id \
            LIMIT ?"""
            results = self.con.execute(
                query, ["%" + term.lower() + "%", limit]).fetchall()
            results = [Post(x[0], x[1], x[2], x[3], x[4], x[5])
                       for x in results]
        return results

    def toggle_like(self, post_id, user_id):
        select_query = """SELECT id FROM Likes WHERE user_id = ? AND post_id = ?"""
        like_id = self.con.execute(select_query, [user_id, post_id]).fetchone()
        if like_id:
            delte_query = """DELETE FROM Likes WHERE id = ?"""
            self.con.execute(delte_query, [like_id[0]])
        else:
            add_query = """INSERT INTO Likes (user_id, post_id) VALUES (?, ?)"""
            self.con.execute(add_query, [user_id, post_id])
        self.con.commit()

    def user_has_liked_post(self, post_id, user_id):
        query = """SELECT id FROM Likes WHERE user_id = ? AND post_id = ?"""
        result = self.con.execute(query, [user_id, post_id])
        return not result is None

    def get_post_like_count(self, post_id):
        query = """SELECT COUNT(id) FROM Likes WHERE post_id = ?"""
        return self.con.execute(query, [post_id]).fetchone()[0]

    def get_comments(self, post_id):
        query = "SELECT C.data, C.id, U.name FROM Comments C, Posts P, Users U WHERE P.id = C.post_id AND U.id = C.user_id AND P.id = ?"
        results = self.con.execute(query, [post_id]).fetchall()
        comments = [Comment(x[0], x[1], x[2]) for x in results]
        return comments

    def create_comment(self, data, user_id, post_id):
        query = """INSERT INTO Comments (data, user_id, post_id) VALUES (?, ?, ?)"""
        self.con.execute(query, [data, user_id, post_id])
        self.con.commit()

    def get_user_post_count(self, user_id):
        query = """SELECT COUNT(id) FROM Posts WHERE user_id = ?"""
        return self.con.execute(query, [user_id]).fetchone()[0]
