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

usernames = [f"user{x}" for x in range(1, 10**5)]
pwd = generate_password_hash("salasana")
for username in usernames:
    con.execute("INSERT INTO Users (name, pwd_hash) VALUES (?, ?)",
                [username, pwd])
con.commit()

print("creating languages...")
languages = ["python", "C", "asm", "scratch"]
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

snippets_c = [
    """#include <stdio.h>

int main() {
    printf(\"Hello World!\\n\");
    return 0;
}""",
    """#include <stdio.h>

int main() {
    for(int i = 0; i < 100; i++) {
        printf(\"luku on %d\\n", i);
    }
    return 0;
}"""
]

for user_id in range(1, len(usernames)):
    for snippet in snippets_python:
        con.execute("INSERT INTO Posts (data, language, user_id) VALUES (?, ?, ?)",
                    [snippet, 1, user_id])
    for snippet in snippets_c:
        con.execute("INSERT INTO Posts (data, language, user_id) VALUES (?, ?, ?)",
                    [snippet, 2, user_id])
con.commit()

print("creating comments and likes...")
print("this might take a while (less than a minute still)")
n_posts = len(usernames) * (len(snippets_python) + len(snippets_c))
for post_id in range(1, n_posts + 1):
    for user_id in range(post_id, post_id + 10):
        user_id = user_id % len(usernames)
        con.execute("INSERT INTO Comments (user_id, post_id, data) VALUES (?, ?, ?)",
                    [user_id, post_id, f"käyttäjän {user_id} kommentti postaukseen {post_id}"])
        con.execute("INSERT INTO Likes (post_id, user_id) values (?, ?)",
                    [post_id, user_id])
con.commit()
