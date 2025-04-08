CREATE TABLE Users (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        pwd_hash TEXT
);

CREATE TABLE Posts (
        id INTEGER PRIMARY KEY,
        data TEXT,
        language INTEGER REFERENCES Languages ON DELETE CASCADE,
        user_id INTEGER REFERENCES Users ON DELETE CASCADE
);

CREATE TABLE Languages (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE
);

CREATE TABLE Likes (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES Users ON DELETE CASCADE,
        post_id INTEGER REFERENCES Posts ON DELETE CASCADE
);

CREATE TABLE Comments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES Users ON DELETE CASCADE,
        post_id INTEGER REFERENCES Posts ON DELETE CASCADE,
        data TEXT
);
