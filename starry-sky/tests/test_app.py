"""End-to-end tests of the lecture flow with the TF-IDF backend (no model download)."""
import pytest
from fastapi.testclient import TestClient

from app import clustering
from app.main import create_app

A, B, C, D = "studentaaaa1", "studentbbbb2", "studentcccc3", "studentdddd4"


@pytest.fixture()
def client(tmp_path):
    return TestClient(create_app(str(tmp_path / "test.sqlite3")))


@pytest.fixture()
def lecture(client):
    d = client.post("/api/sessions", json={"title": "Algorithms week 5"}).json()
    return d["code"], d["instructor_token"]


def ask(client, code, anon, text):
    return client.post(f"/api/s/{code}/questions", json={"anon_id": anon, "text": text})


def test_create_and_pages(client, lecture):
    code, token = lecture
    assert len(code) == 5
    assert client.get(f"/s/{code}").status_code == 200
    assert client.get(f"/i/{code}").status_code == 200
    assert client.get("/s/NOPE9").status_code == 404


def test_instructor_api_needs_token(client, lecture):
    code, token = lecture
    assert client.get(f"/api/i/{code}/sky", params={"t": "wrong"}).status_code == 403
    assert client.get(f"/api/i/{code}/sky", params={"t": token}).status_code == 200


def test_ask_phase_is_private(client, lecture):
    code, _ = lecture
    assert ask(client, code, A, "What is memoization?").status_code == 200
    state_b = client.get(f"/api/s/{code}/state", params={"anon_id": B}).json()
    assert state_b["phase"] == "ask"
    assert state_b["mine"] == [] and "ballot" not in state_b  # B cannot see A's question
    state_a = client.get(f"/api/s/{code}/state", params={"anon_id": A}).json()
    assert [q["text"] for q in state_a["mine"]] == ["What is memoization?"]


def test_input_validation(client, lecture):
    code, _ = lecture
    assert ask(client, code, A, "   ").status_code == 400
    assert ask(client, code, A, "x" * 501).status_code == 400
    assert ask(client, code, "bad id!", "Valid question").status_code == 400
    for i in range(20):
        assert ask(client, code, C, f"question number {i}").status_code == 200
    assert ask(client, code, C, "one too many").status_code == 429


def test_full_flow_grouping_votes_ranking_export(client, lecture):
    code, token = lecture
    ask(client, code, A, "What is the difference between memoization and tabulation?")
    ask(client, code, B, "Difference between memoization and tabulation in dynamic programming?")
    ask(client, code, C, "memoization vs tabulation difference")
    ask(client, code, D, "When is the exam?")
    # no voting during the ask phase
    assert client.post(f"/api/s/{code}/vote", json={"anon_id": A, "question_id": 1}).status_code == 409

    assert client.post(f"/api/i/{code}/phase", params={"t": token}, json={"phase": "vote"}).status_code == 200
    assert ask(client, code, A, "late question").status_code == 409
    ballot_a = client.get(f"/api/s/{code}/state", params={"anon_id": A}).json()["ballot"]
    ballot_b = client.get(f"/api/s/{code}/state", params={"anon_id": B}).json()["ballot"]
    assert sorted(q["id"] for q in ballot_a) == sorted(q["id"] for q in ballot_b)
    assert all("upvotes" not in q for q in ballot_a)  # no counts shown to students
    exam = next(q["id"] for q in ballot_a if "exam" in q["text"])
    own = next(q["id"] for q in ballot_a if q["mine"])
    assert client.post(f"/api/s/{code}/vote", json={"anon_id": A, "question_id": own}).status_code == 400
    for voter in (A, B, C):
        r = client.post(f"/api/s/{code}/vote", json={"anon_id": voter, "question_id": exam})
        assert r.json() == {"voted": True}
    assert client.post(f"/api/s/{code}/vote", json={"anon_id": C, "question_id": exam}).json() == {"voted": False}

    client.post(f"/api/i/{code}/threshold", params={"t": token}, json={"threshold": 0.15})
    sky = client.get(f"/api/i/{code}/sky", params={"t": token}).json()
    assert sky["n_questions"] == 4 and sky["n_askers"] == 4
    brightest = sky["stars"][0]
    assert brightest["askers"] == 3 and brightest["n_questions"] == 3  # the three memoization questions merged
    exam_star = next(s for s in sky["stars"] if "exam" in s["representative"])
    assert exam_star["askers"] == 1 and exam_star["upvotes"] == 2  # brightness and upvotes are separate signals
    for s in sky["stars"]:
        assert 0.0 <= s["x"] <= 1.0 and 0.0 <= s["y"] <= 1.0

    client.post(f"/api/i/{code}/phase", params={"t": token}, json={"phase": "closed"})
    start = client.post(f"/api/i/{code}/ranking/start", params={"t": token}).json()
    items = start["items"]
    assert all(set(item) == {"id", "representative", "questions"} for item in items)  # blind: no counts
    ids = [i["id"] for i in items]
    bad = client.post(f"/api/i/{code}/ranking", params={"t": token},
                      json={"run_id": start["run_id"], "shown_order": ids, "ranking": ids[:1]})
    assert bad.status_code == 400
    ok = client.post(f"/api/i/{code}/ranking", params={"t": token},
                     json={"run_id": start["run_id"], "shown_order": ids, "ranking": list(reversed(ids))})
    assert ok.status_code == 200

    data = client.get(f"/api/i/{code}/export", params={"t": token}).json()
    assert "instructor_token" not in data["session"]
    assert len(data["questions"]) == 4 and len(data["votes"]) == 2
    assert all(v["shown_position"] >= 1 for v in data["votes"])
    assert len(data["cluster_runs"]) == 1 and len(data["rankings"]) == 1
    assert data["session"]["phase"] == "closed" and data["session"]["vote_started_at"]


def test_hidden_questions_leave_the_sky_but_stay_in_export(client, lecture):
    code, token = lecture
    ask(client, code, A, "What is memoization?")
    ask(client, code, B, "spam spam spam")
    qid = 2
    client.post(f"/api/i/{code}/hide", params={"t": token}, json={"question_id": qid, "hidden": True})
    sky = client.get(f"/api/i/{code}/sky", params={"t": token}).json()
    assert sky["n_questions"] == 1
    data = client.get(f"/api/i/{code}/export", params={"t": token}).json()
    assert [q["hidden"] for q in data["questions"]] == [0, 1]


def test_clustering_unit():
    vecs = clustering.embed(["a b c", "a b c d", "x y z"], "tfidf")
    labels = clustering.cluster(vecs, 0.5)
    assert labels[0] == labels[1] != labels[2]
    assert list(clustering.cluster(vecs[:1], 0.5)) == [0]
    assert clustering.layout(vecs[:0], []) == []
    pts = clustering.layout(vecs, [1, 1, 1])
    assert len(pts) == 3 and all(0.0 <= a <= 1.0 and 0.0 <= b <= 1.0 for a, b in pts)
    assert clustering.sky([], [], 0.5)["stars"] == []
