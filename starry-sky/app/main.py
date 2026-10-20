"""Starry Sky: students ask questions during a lecture; similar questions become one star, and a star is brighter the
more students asked it. Built as the data-collection instrument for the two studies in the research proposal.

Lecture flow (instructor controls the phase):
  ask    students submit questions privately; nobody sees other students' questions
  vote   every student sees all questions in their own random order and can upvote
  closed nothing more is accepted; the instructor ranks the groups blind (no counts shown)

Run:  python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import clustering
from .db import Store

STATIC = Path(__file__).resolve().parent / "static"
PHASES = ("ask", "vote", "closed")
MAX_QUESTION = 500
MAX_PER_STUDENT = 20


class NewSession(BaseModel):
    title: str = Field("Lecture", max_length=200)

class Ask(BaseModel):
    anon_id: str
    text: str

class Vote(BaseModel):
    anon_id: str
    question_id: int

class Phase(BaseModel):
    phase: str

class Threshold(BaseModel):
    threshold: float = Field(ge=0.1, le=0.95)

class Hide(BaseModel):
    question_id: int
    hidden: bool = True

class Ranking(BaseModel):
    run_id: int
    shown_order: list[int]
    ranking: list[int]


def create_app(db_path: str | None = None) -> FastAPI:
    store = Store(db_path or os.environ.get("STARRY_DB", "data/starry.sqlite3"))
    app = FastAPI(title="Starry Sky")
    app.state.store = store
    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    if os.environ.get("STARRY_BACKEND", "sentence") == "sentence":
        # Load (and on first use download) the model now, not on the instructor's first refresh.
        threading.Thread(target=clustering.backend, daemon=True).start()

    # -- helpers -----------------------------------------------------------------
    def get_session(code: str):
        s = store.session(code)
        if s is None:
            raise HTTPException(404, "No lecture with this code.")
        return s

    def instructor(code: str, token: str | None):
        s = get_session(code)
        if not token or token != s["instructor_token"]:
            raise HTTPException(403, "Instructor link required.")
        return s

    def check_anon(anon_id: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", anon_id or ""):
            raise HTTPException(400, "Invalid participant id.")
        return anon_id

    def compute_sky(s, method: str | None = None) -> dict:
        qs = [dict(q) for q in store.questions(s["id"])]
        vs = [dict(v) for v in store.votes(s["id"])]
        return clustering.sky(qs, vs, s["threshold"], method)

    def shuffled(questions: list, s, anon_id: str) -> list:
        seed = int(hashlib.sha256(f"{s['code']}:{anon_id}".encode()).hexdigest()[:12], 16)
        items = list(questions)
        random.Random(seed).shuffle(items)
        return items

    # -- pages ---------------------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/s/{code}", response_class=HTMLResponse)
    def student_page(code: str):
        get_session(code)
        return FileResponse(STATIC / "student.html")

    @app.get("/i/{code}", response_class=HTMLResponse)
    def instructor_page(code: str):
        get_session(code)
        return FileResponse(STATIC / "instructor.html")

    # -- session management --------------------------------------------------------

    @app.post("/api/sessions")
    def new_session(body: NewSession, request: Request):
        created = store.create_session(body.title)
        base = str(request.base_url).rstrip("/")
        return {**created, "student_url": f"{base}/s/{created['code']}",
                "instructor_url": f"{base}/i/{created['code']}?t={created['instructor_token']}"}

    # -- student API -------------------------------------------------------------------
    @app.get("/api/s/{code}/state")
    def student_state(code: str, anon_id: str):
        s = get_session(code)
        pid = store.participant(s["id"], check_anon(anon_id))
        qs = store.questions(s["id"])
        mine = [{"id": q["id"], "text": q["text"]} for q in qs if q["participant_id"] == pid]
        out = {"title": s["title"], "phase": s["phase"], "mine": mine}
        if s["phase"] == "vote":
            my_votes = {v["question_id"] for v in store.votes(s["id"]) if v["participant_id"] == pid}
            # No counts and no author markers: students vote on wording alone, in their own random order.
            out["ballot"] = [{"id": q["id"], "text": q["text"], "voted": q["id"] in my_votes,
                              "mine": q["participant_id"] == pid}
                             for q in shuffled(qs, s, anon_id)]
        return out


    @app.post("/api/s/{code}/questions")
    def ask(code: str, body: Ask):
        s = get_session(code)
        if s["phase"] != "ask":
            raise HTTPException(409, "Questions are closed for now.")
        text = re.sub(r"\s+", " ", body.text).strip()
        if not text:
            raise HTTPException(400, "Empty question.")
        if len(text) > MAX_QUESTION:
            raise HTTPException(400, f"Please keep it under {MAX_QUESTION} characters.")
        pid = store.participant(s["id"], check_anon(body.anon_id))
        if sum(1 for q in store.questions(s["id"], True) if q["participant_id"] == pid) >= MAX_PER_STUDENT:
            raise HTTPException(429, "You have reached the question limit for this lecture.")
        qid = store.add_question(s["id"], pid, text, s["phase"])
        return {"id": qid}


    @app.post("/api/s/{code}/vote")
    def vote(code: str, body: Vote):
        s = get_session(code)
        if s["phase"] != "vote":
            raise HTTPException(409, "Voting is not open.")
        anon = check_anon(body.anon_id)
        pid = store.participant(s["id"], anon)
        qs = store.questions(s["id"])
        ballot = [q["id"] for q in shuffled(qs, s, anon)]
        if body.question_id not in ballot:
            raise HTTPException(404, "Unknown question.")
        own = next(q for q in qs if q["id"] == body.question_id)["participant_id"] == pid
        if own:
            raise HTTPException(400, "You cannot upvote your own question.")
        voted = store.toggle_vote(body.question_id, pid, ballot.index(body.question_id) + 1)
        return {"voted": voted}

    # -- instructor API ------------------------------------------------------------------
    @app.get("/api/i/{code}/sky")
    def instructor_sky(code: str, t: str):
        s = instructor(code, t)
        sky = compute_sky(s)
        n_students = len({q["participant_id"] for q in store.questions(s["id"])})
        return {"title": s["title"], "code": s["code"], "phase": s["phase"], "threshold": s["threshold"],
                "method": clustering.describe(), "n_questions": len(sky["assignment"]),
                "n_askers": n_students, "stars": sky["stars"]}


    @app.post("/api/i/{code}/phase")
    def set_phase(code: str, t: str, body: Phase):
        s = instructor(code, t)
        if body.phase not in PHASES:
            raise HTTPException(400, f"phase must be one of {PHASES}")
        store.set_phase(s["id"], body.phase)
        return {"phase": body.phase}


    @app.post("/api/i/{code}/threshold")
    def set_threshold(code: str, t: str, body: Threshold):
        s = instructor(code, t)
        store.set_threshold(s["id"], body.threshold)
        return {"threshold": body.threshold}


    @app.post("/api/i/{code}/hide")
    def hide(code: str, t: str, body: Hide):
        s = instructor(code, t)
        store.set_hidden(s["id"], body.question_id, body.hidden)
        return {"ok": True}

    @app.post("/api/i/{code}/ranking/start")
    def ranking_start(code: str, t: str):
        """Freeze the current grouping and return the groups in random order, without any counts (blind ranking)."""
        s = instructor(code, t)
        sky = compute_sky(s)
        run_id = store.save_cluster_run(s["id"], sky["method"], sky["threshold"], sky["assignment"])
        items = [{"id": st["id"], "representative": st["representative"],
                  "questions": [q["text"] for q in st["questions"]]} for st in sky["stars"]]
        random.Random(run_id).shuffle(items)
        return {"run_id": run_id, "items": items}


    @app.post("/api/i/{code}/ranking")
    def ranking_save(code: str, t: str, body: Ranking):
        s = instructor(code, t)
        run = store.cluster_run(body.run_id)
        if run is None or run["session_id"] != s["id"]:
            raise HTTPException(404, "Unknown grouping.")
        labels = set(json.loads(run["assignment"]).values())
        if set(body.ranking) != labels or len(body.ranking) != len(labels):
            raise HTTPException(400, "Rank every group exactly once.")
        rid = store.save_ranking(s["id"], body.run_id, body.shown_order, body.ranking)
        return {"ranking_id": rid}

    @app.get("/api/i/{code}/export")
    def export(code: str, t: str):
        s = instructor(code, t)
        data = store.export(s["id"])
        data["current_grouping"] = compute_sky(s)
        data["grouping_method"] = clustering.describe()
        headers = {"Content-Disposition": f'attachment; filename="starry-{s["code"]}.json"'}
        return JSONResponse(data, headers=headers)

    return app

