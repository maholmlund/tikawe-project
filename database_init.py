import sqlite3
from werkzeug.security import generate_password_hash

print("creating database...")

schema = open("src/schema.sql").read()
tables = schema.split(";")
con = sqlite3.connect("database.db")
for table in tables:
    con.execute(table)
con.commit()

print("creating languages...")
languages = ["python", "C", "asm", "scratch"]
for language in languages:
    con.execute("INSERT INTO Languages (name) VALUES (?)", [language])
con.commit()

print("done")
