import sqlite3
from werkzeug.security import generate_password_hash

print("creating database...")

schema = open("src/schema.sql").read()
tables = schema.split(";")
con = sqlite3.connect("database.db")
for table in tables:
    con.execute(table)
con.commit()

print("database created")
print("creating users...")

usernames = ["hertta", "perttu", "inka", "rene", "miika"]
for username in usernames:
    pwd = generate_password_hash("salasana")
    con.execute("INSERT INTO Users (name, pwd_hash) VALUES (?, ?)",
                [username, pwd])
con.commit()

print("creating languages...")
languages = ["python", "C"]
for language in languages:
    con.execute("INSERT INTO Languages (name) VALUES (?)", [language])
con.commit()

print("creating posts...")
snippets_python = [
    """print(\"hello world\")""",
    """def foo():
    return \"bar\"""",
    """for i in range(10):
    print(i)""",
    """guess = input(\"veikkaa\")
while input != \"salasana\":
    guess = input(\"veikkaa\")
print(\"onneksi olkoon!\")""",
    """import sqlite3

con = sqlite3.connect(\"db.db\")
print(con.execute(\"SELECT * FROM Table\").fetchall())"""
]

for user_id in range(1, len(usernames)):
    for snippet in snippets_python:
        con.execute("INSERT INTO Posts (data, language, user_id) VALUES (?, ?, ?)",
                    [snippet, 1, user_id])
con.commit()
