import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "plagiarism.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name        TEXT NOT NULL,
            course              TEXT NOT NULL,
            assignment_title    TEXT NOT NULL,
            text                TEXT NOT NULL,
            plagiarism_score    REAL DEFAULT 0,
            ai_generated_score  REAL DEFAULT 0,
            similarity_matches  TEXT DEFAULT '[]',
            granite_analysis    TEXT DEFAULT '',
            instructor_feedback TEXT DEFAULT '',
            flag                INTEGER DEFAULT 0,
            submitted_at        TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_corpus (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id   INTEGER,
            feedback        TEXT,
            flag            INTEGER DEFAULT 0,
            created_at      TEXT
        )
    """)

    conn.commit()
    conn.close()
