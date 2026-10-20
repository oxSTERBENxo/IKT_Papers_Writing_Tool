"""SQLite storage. One file per deployment; every row needed for the two studies is kept.

Privacy: no names, e-mail or IP addresses are stored. A participant is a random ID created per session in the
student's browser.
"""
from __future__ import annotations

import json
import secrets
import sqlite3
import string
import threading
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    instructor_token TEXT NOT NULL,
    phase TEXT NOT NULL DEFAULT 'ask',          -- ask | vote | closed
    threshold REAL NOT NULL DEFAULT 0.55,       -- cosine similarity needed to join a group
    created_at REAL NOT NULL,
    vote_started_at REAL,
    closed_at REAL
);
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    anon_id TEXT NOT NULL,
    created_at REAL NOT NULL,
    UNIQUE(session_id, anon_id)
);
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    participant_id INTEGER NOT NULL REFERENCES participants(id),
    text TEXT NOT NULL,
    phase TEXT NOT NULL,
    created_at REAL NOT NULL,
    hidden INTEGER NOT NULL DEFAULT 0           -- instructor removed it (off-topic, abusive); kept for the record
);
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions(id),
    participant_id INTEGER NOT NULL REFERENCES participants(id),
    shown_position INTEGER,                     -- position in the voter's shuffled list (position-bias analysis)
    created_at REAL NOT NULL,
    UNIQUE(question_id, participant_id)
);
CREATE TABLE IF NOT EXISTS cluster_runs (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    method TEXT NOT NULL,
    threshold REAL NOT NULL,
    assignment TEXT NOT NULL,                   -- JSON {question_id: cluster_label}
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS rankings (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    cluster_run_id INTEGER NOT NULL REFERENCES cluster_runs(id),
    shown_order TEXT NOT NULL,                  -- JSON list of cluster labels in the order shown to the instructor
    ranking TEXT NOT NULL,                      -- JSON list of cluster labels, most important first
    created_at REAL NOT NULL
);
"""

CODE_ALPHABET = "".join(c for c in string.ascii_uppercase + string.digits if c not in "O0I1L")


class Store:
    def __init__(self, path: str | Path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.lock = threading.Lock()

    def q(self, sql: str, args=()) -> list[sqlite3.Row]:
        with self.lock:
            return self.conn.execute(sql, args).fetchall()

    def x(self, sql: str, args=()) -> int:
        with self.lock:
            cur = self.conn.execute(sql, args)
            self.conn.commit()
            return cur.lastrowid

    # sessions --------------------------------------------------------------
    def create_session(self, title: str) -> dict:
        for _ in range(20):
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(5))
            if not self.q("SELECT 1 FROM sessions WHERE code=?", (code,)):
                break
        token = secrets.token_urlsafe(16)
        self.x("INSERT INTO sessions(code, title, instructor_token, created_at) VALUES (?,?,?,?)",
               (code, title.strip()[:200] or "Lecture", token, time.time()))
        return {"code": code, "instructor_token": token}

    def session(self, code: str) -> sqlite3.Row | None:
        rows = self.q("SELECT * FROM sessions WHERE code=?", (code.upper(),))
        return rows[0] if rows else None

    def set_phase(self, session_id: int, phase: str) -> None:
        now = time.time()
        extra = {"vote": ", vote_started_at=COALESCE(vote_started_at, ?)", "closed": ", closed_at=?"}.get(phase, "")
        args = (phase, now, session_id) if extra else (phase, session_id)
        self.x(f"UPDATE sessions SET phase=?{extra} WHERE id=?", args)

    def set_threshold(self, session_id: int, threshold: float) -> None:
        self.x("UPDATE sessions SET threshold=? WHERE id=?", (threshold, session_id))

    # participants and questions ------------------------------------------------
    def participant(self, session_id: int, anon_id: str) -> int:
        rows = self.q("SELECT id FROM participants WHERE session_id=? AND anon_id=?", (session_id, anon_id))
        if rows:
            return rows[0]["id"]
        return self.x("INSERT INTO participants(session_id, anon_id, created_at) VALUES (?,?,?)",
                      (session_id, anon_id, time.time()))

    def add_question(self, session_id: int, participant_id: int, text: str, phase: str) -> int:
        return self.x("INSERT INTO questions(session_id, participant_id, text, phase, created_at) VALUES (?,?,?,?,?)",
                      (session_id, participant_id, text, phase, time.time()))

    def questions(self, session_id: int, include_hidden: bool = False) -> list[sqlite3.Row]:
        hidden = "" if include_hidden else " AND hidden=0"
        return self.q(f"SELECT * FROM questions WHERE session_id=?{hidden} ORDER BY id", (session_id,))

    def set_hidden(self, session_id: int, question_id: int, hidden: bool) -> None:
        self.x("UPDATE questions SET hidden=? WHERE id=? AND session_id=?", (int(hidden), question_id, session_id))

    # votes ---------------------------------------------------------------------
    def toggle_vote(self, question_id: int, participant_id: int, shown_position: int | None) -> bool:
        if self.q("SELECT 1 FROM votes WHERE question_id=? AND participant_id=?", (question_id, participant_id)):
            self.x("DELETE FROM votes WHERE question_id=? AND participant_id=?", (question_id, participant_id))
            return False
        self.x("INSERT INTO votes(question_id, participant_id, shown_position, created_at) VALUES (?,?,?,?)",
               (question_id, participant_id, shown_position, time.time()))
        return True

    def votes(self, session_id: int) -> list[sqlite3.Row]:
        return self.q("SELECT v.* FROM votes v JOIN questions q ON q.id=v.question_id WHERE q.session_id=?",
                      (session_id,))

    # clustering and rankings ---------------------------------------------------
    def save_cluster_run(self, session_id: int, method: str, threshold: float, assignment: dict) -> int:
        return self.x("INSERT INTO cluster_runs(session_id, method, threshold, assignment, created_at) "
                      "VALUES (?,?,?,?,?)", (session_id, method, threshold, json.dumps(assignment), time.time()))

    def cluster_run(self, run_id: int) -> sqlite3.Row | None:
        rows = self.q("SELECT * FROM cluster_runs WHERE id=?", (run_id,))
        return rows[0] if rows else None

    def save_ranking(self, session_id: int, run_id: int, shown: list, ranking: list) -> int:
        return self.x("INSERT INTO rankings(session_id, cluster_run_id, shown_order, ranking, created_at) "
                      "VALUES (?,?,?,?,?)", (session_id, run_id, json.dumps(shown), json.dumps(ranking), time.time()))

    def export(self, session_id: int) -> dict:
        def rows(sql):
            return [dict(r) for r in self.q(sql, (session_id,))]
        s = dict(self.q("SELECT * FROM sessions WHERE id=?", (session_id,))[0])
        s.pop("instructor_token", None)
        return {
            "session": s,
            "participants": rows("SELECT id, anon_id, created_at FROM participants WHERE session_id=?"),
            "questions": rows("SELECT * FROM questions WHERE session_id=? ORDER BY id"),
            "votes": rows("SELECT v.* FROM votes v JOIN questions q ON q.id=v.question_id WHERE q.session_id=?"),
            "cluster_runs": rows("SELECT * FROM cluster_runs WHERE session_id=? ORDER BY id"),
            "rankings": rows("SELECT * FROM rankings WHERE session_id=? ORDER BY id"),
        }
