"""投票服务的身份隔离、事务边界、管理并发和 SSE 回归测试。"""

from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import httpx
import pytest
import uvicorn
from fastapi.testclient import TestClient

from services.vote.app import EventHub, create_app
from services.vote.core import Config, VoteStore


PASSWORD = "test-only-admin-password-1234"


def request_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def config(tmp_path):
    return Config(
        db_path=str(tmp_path / "vote.sqlite3"), admin_password=PASSWORD,
        secret_key="test-only-secret-" * 4, secure_cookie=False,
        allowed_origins=("http://testserver",), vote_interval_ms=0, message_interval_ms=0,
    )


@pytest.fixture
def client(config):
    with TestClient(create_app(config)) as active:
        assert active.post("/api/admin/session", json={"password": PASSWORD}).status_code == 200
        yield active


def new_session(client, **fields):
    response = client.post("/api/session", json=fields, headers={"Cookie": ""})
    assert response.status_code == 200, response.text
    return response.json()


def auth(session):
    return {"Authorization": "Bearer " + session["token"]}


def admin_state(client):
    response = client.get("/api/admin/state")
    assert response.status_code == 200, response.text
    return response.json()


def action(client, name, *, revision=None, rid=None, **fields):
    if revision is None:
        revision = admin_state(client)["revision"]
    return client.post("/api/admin/action", json={
        "action": name, "expectedRevision": revision, "requestId": rid or request_id(), **fields,
    })


def add_contestant(client, name="选手甲", group="A组"):
    response = action(client, "upsert_contestant", contestant={"name": name, "group": group})
    assert response.status_code == 200, response.text
    return next(item for item in response.json()["state"]["contestants"] if item["name"] == name)


def open_contestant(client, contestant):
    response = action(client, "open", contestantId=contestant["id"])
    assert response.status_code == 200
    return next(item for item in response.json()["state"]["contestants"] if item["id"] == contestant["id"])


def cast(client, session, contestant, voted=True, *, rid=None, epoch=None):
    return client.put("/api/votes/" + contestant["id"], headers=auth(session), json={
        "voted": voted, "epoch": contestant["epoch"] if epoch is None else epoch,
        "requestId": rid or request_id(),
    })


def snapshot(client, session):
    response = client.get("/api/snapshot", headers=auth(session))
    assert response.status_code == 200
    return response.json()


def test_empty_install_and_no_unauthenticated_admin_access(client):
    viewer = new_session(client)
    assert viewer["snapshot"]["contestants"] == []
    assert viewer["snapshot"]["currentId"] is None
    assert client.get("/api/health").json()["ok"] is True
    assert client.get("/api/admin/state", headers={"Cookie": ""}).status_code == 401
    response = client.get("/api/snapshot", headers={"Cookie": ""})
    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_redundant_tokens_restore_votes_without_cookie_and_store_hashes(client):
    viewer = new_session(client)
    contestant = open_contestant(client, add_contestant(client))
    assert cast(client, viewer, contestant).status_code == 200
    restored = new_session(client, tokens=["invalid-stale-token", viewer["token"]])
    assert restored["userId"] == viewer["userId"]
    assert restored["snapshot"]["me"]["votes"] == [contestant["id"]]
    assert restored["restored"] == "token"
    row = client.app.state.store.db.execute("SELECT token_hash FROM tokens WHERE user_id=?", (viewer["userId"],)).fetchone()
    assert row[0] != viewer["token"]
    assert len(row[0]) == 64
    # 显式恢复码优先于浏览器里可能残留的另一身份。
    other = new_session(client)
    restored = new_session(client, tokens=[other["token"]], recoveryCode=viewer["recoveryCode"])
    assert restored["userId"] == viewer["userId"]


def test_identical_phone_fingerprints_do_not_merge_new_users(client):
    features = {"fingerprint": "a" * 64, "fingerprintQualified": True, "fingerprintVersion": "v1"}
    first = new_session(client, **features)
    second = new_session(client, **features)
    assert first["userId"] != second["userId"]
    contestant = open_contestant(client, add_contestant(client))
    cast(client, first, contestant)
    assert snapshot(client, second)["me"]["votes"] == []
    restored = new_session(client, **features, identityHint=first["userId"])
    assert restored["restored"] == "fingerprint"
    assert restored["userId"] == first["userId"]
    assert restored["snapshot"]["me"]["votes"] == [contestant["id"]]
    mismatch = new_session(client, fingerprint="b" * 64, fingerprintQualified=True, identityHint=first["userId"])
    assert mismatch["userId"] not in {first["userId"], second["userId"]}
    unqualified = new_session(client, fingerprint="a" * 64, fingerprintQualified=False, identityHint=first["userId"])
    assert unqualified["userId"] != first["userId"]


def test_invalid_recovery_does_not_silently_create_a_new_identity(client):
    before = client.app.state.store.db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    response = client.post("/api/session", json={"recoveryCode": "z" * 43}, headers={"Cookie": ""})
    assert response.status_code == 401
    after = client.app.state.store.db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    assert before == after


def test_vote_idempotency_and_actor_isolation(client):
    first, second = new_session(client), new_session(client)
    contestant = open_contestant(client, add_contestant(client))
    rid = request_id()
    for _ in range(3):
        response = cast(client, first, contestant, rid=rid)
        assert response.status_code == 200
    assert admin_state(client)["contestants"][0]["rawVotes"] == 1
    assert snapshot(client, second)["me"]["votes"] == []
    conflict = cast(client, first, contestant, voted=False, rid=rid)
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "request_id_conflict"
    assert cast(client, second, contestant, rid=rid).status_code == 200
    assert admin_state(client)["contestants"][0]["rawVotes"] == 2
    assert cast(client, first, contestant, voted=False).status_code == 200
    assert snapshot(client, first)["me"]["votes"] == []
    assert admin_state(client)["contestants"][0]["rawVotes"] == 1


def test_lock_rejects_new_requests_and_reopen_rejects_old_epoch(client):
    viewer = new_session(client)
    contestant = open_contestant(client, add_contestant(client))
    rid = request_id()
    assert cast(client, viewer, contestant, rid=rid).status_code == 200
    assert action(client, "lock", contestantId=contestant["id"]).status_code == 200
    rejected = cast(client, viewer, contestant, voted=False)
    assert rejected.status_code == 409
    assert rejected.json()["error"]["code"] == "vote_locked"
    assert snapshot(client, viewer)["me"]["votes"] == [contestant["id"]]
    # 成功请求的网络重试即使跨过锁票也不会变成二次计票。
    replay = cast(client, viewer, contestant, rid=rid)
    assert replay.status_code == 200 and replay.json()["replayed"] is True
    reopened = open_contestant(client, contestant)
    stale = cast(client, viewer, contestant, voted=False)
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "stale_epoch"
    assert cast(client, viewer, reopened, voted=False).status_code == 200


def test_switch_keeps_unlocked_previous_votes_editable(client):
    first = open_contestant(client, add_contestant(client, "选手甲"))
    second = add_contestant(client, "选手乙")
    viewer = new_session(client)
    action(client, "select", contestantId=first["id"])
    cast(client, viewer, first)
    response = action(client, "select", contestantId=second["id"])
    previous = next(row for row in response.json()["state"]["contestants"] if row["id"] == first["id"])
    assert previous["status"] == "performed" and previous["voting"] == "open"
    assert cast(client, viewer, first, voted=False).status_code == 200
    action(client, "select", contestantId=first["id"], lockPrevious=True)
    action(client, "select", contestantId=second["id"], lockPrevious=True)
    assert cast(client, viewer, first).status_code == 409


def test_multiple_admins_conflict_and_retries_do_not_duplicate_adjustments(client):
    contestant = add_contestant(client)
    revision = admin_state(client)["revision"]
    rid = request_id()
    first = action(client, "adjust", revision=revision, rid=rid, contestantId=contestant["id"], delta=5, reason="补录现场纸票", public=True)
    assert first.status_code == 200
    stale = action(client, "lock", revision=revision, contestantId=contestant["id"])
    assert stale.status_code == 409 and stale.json()["state"]["revision"] == revision + 1
    duplicate = action(client, "adjust", revision=revision, rid=rid, contestantId=contestant["id"], delta=5, reason="补录现场纸票", public=True)
    assert duplicate.status_code == 200 and duplicate.json()["replayed"] is True
    state = admin_state(client)
    assert state["contestants"][0]["votes"] == 5
    assert len(state["contestants"][0]["adjustments"]) == 1
    assert len([row for row in state["audit"] if row["action"] == "adjust"]) == 1


def test_public_state_does_not_expose_hidden_adjustments_or_raw_totals(client):
    viewer = new_session(client)
    contestant = add_contestant(client)
    action(client, "adjust", contestantId=contestant["id"], delta=4, reason="公开补录原因", public=True)
    action(client, "adjust", contestantId=contestant["id"], delta=9, reason="仅管理员可见的说明", public=False)
    hidden = snapshot(client, viewer)
    assert hidden["contestants"][0]["votes"] is None
    assert hidden["contestants"][0]["adjustments"] == []
    action(client, "publish", contestantIds=[contestant["id"]], visible=True)
    public = snapshot(client, viewer)
    encoded = json.dumps(public, ensure_ascii=False)
    assert "仅管理员可见的说明" not in encoded
    assert "rawVotes" not in encoded and "adjustmentTotal" not in encoded and "audit" not in encoded
    assert public["contestants"][0]["votes"] == 13
    assert [row["reason"] for row in public["contestants"][0]["adjustments"]] == ["公开补录原因"]
    assert len(admin_state(client)["contestants"][0]["adjustments"]) == 2


def test_cancellations_after_negative_adjustments_never_create_negative_display(client):
    viewer = new_session(client)
    contestant = open_contestant(client, add_contestant(client))
    cast(client, viewer, contestant)
    assert action(client, "adjust", contestantId=contestant["id"], delta=-1, reason="按规则扣票", public=True).status_code == 200
    assert cast(client, viewer, contestant, voted=False).status_code == 200
    state = admin_state(client)["contestants"][0]
    assert state["rawVotes"] == 0 and state["votes"] == 0
    assert action(client, "adjust", contestantId=contestant["id"], delta=-1, reason="继续扣票", public=True).status_code == 422


def test_message_idempotency_deletion_and_private_ban(client, monkeypatch):
    first, second = new_session(client), new_session(client)
    rid = request_id()
    payload = {"text": "这段也太好笑了", "requestId": rid}
    response = client.post("/api/messages", json=payload, headers=auth(first))
    message_id = response.json()["message"]["id"]
    repeated = client.post("/api/messages", json=payload, headers=auth(first))
    assert repeated.json()["replayed"] is True
    assert len(snapshot(client, second)["messages"]) == 1
    state = admin_state(client)
    assert state["messages"][0]["userId"] == first["userId"]
    assert "userId" not in snapshot(client, second)["messages"][0]
    assert action(client, "delete_message", messageId=message_id).status_code == 200
    assert snapshot(client, second)["messages"] == []
    assert client.app.state.vote.pending_messages == []
    assert action(client, "ban", userId=first["userId"], seconds=60).status_code == 200
    banned = client.post("/api/messages", json={"text": "再试一次", "requestId": request_id()}, headers=auth(first))
    assert banned.status_code == 403
    assert snapshot(client, first)["me"]["bannedUntil"] > 0
    assert snapshot(client, second)["me"]["bannedUntil"] == 0
    assert client.post("/api/messages", json={"text": "其他人仍可发送", "requestId": request_id()}, headers=auth(second)).status_code == 200
    assert action(client, "ban", userId=first["userId"], seconds=0).status_code == 200
    assert client.post("/api/messages", json={"text": "恢复发送", "requestId": request_id()}, headers=auth(first)).status_code == 200
    highlighted = action(client, "message", text="下一位选手准备上场", highlight=True)
    assert highlighted.status_code == 200
    assert snapshot(client, first)["messages"][-1]["highlight"] is True


def test_vote_and_message_limits_are_per_user_not_shared_nat(config):
    with TestClient(create_app(replace(config, vote_interval_ms=800, message_interval_ms=5000))) as client:
        client.post("/api/admin/session", json={"password": PASSWORD})
        first, second = new_session(client), new_session(client)
        contestant = open_contestant(client, add_contestant(client))
        assert cast(client, first, contestant).status_code == 200
        limited = cast(client, first, contestant, voted=False)
        assert limited.status_code == 429 and int(limited.headers["retry-after"]) >= 1
        assert cast(client, second, contestant).status_code == 200
        payload = {"text": "好笑", "requestId": request_id()}
        assert client.post("/api/messages", json=payload, headers=auth(first)).status_code == 200
        payload["requestId"] = request_id()
        assert client.post("/api/messages", json=payload, headers=auth(first)).status_code == 429
        assert client.post("/api/messages", json=payload, headers=auth(second)).status_code == 200


def test_validation_csrf_body_limits_and_secret_redaction(client):
    assert client.post("/api/session", json={}, headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.post("/api/session", content="{}").status_code == 415
    assert client.post("/api/session", content=b"x" * 65537, headers={"Content-Type": "application/json"}).status_code == 413
    response = client.post("/api/admin/session", json={"password": PASSWORD, "unexpected": PASSWORD})
    assert response.status_code == 422 and PASSWORD not in response.text
    contestant = add_contestant(client)
    assert action(client, "set_status", contestantId=contestant["id"], status=[]).status_code == 422
    invalid_id = client.post("/api/admin/action", json={"action": "lock_all", "expectedRevision": 1, "requestId": 123})
    assert invalid_id.status_code == 422
    viewer = new_session(client)
    assert client.post("/api/messages", json={"text": "字" * 81, "requestId": request_id()}, headers=auth(viewer)).status_code == 422


def test_batch_import_is_atomic_and_protects_historical_contestants(client):
    response = action(client, "import_contestants", contestants=[{"name": "有效选手", "group": "A"}, {"name": "", "group": "B"}])
    assert response.status_code == 422
    assert admin_state(client)["contestants"] == []
    contestant = open_contestant(client, add_contestant(client))
    viewer = new_session(client)
    cast(client, viewer, contestant)
    cast(client, viewer, contestant, voted=False)
    assert action(client, "remove_contestant", contestantId=contestant["id"]).status_code == 409
    added = add_contestant(client, "尚无记录的选手")
    assert action(client, "remove_contestant", contestantId=added["id"]).status_code == 200


def test_admin_logout_revokes_signed_session_and_preserves_other_admin(client):
    first_token = client.cookies.get("vote_admin")
    second_login = client.post("/api/admin/session", json={"password": PASSWORD})
    assert second_login.status_code == 200
    second_token = client.cookies.get("vote_admin")
    assert first_token != second_token
    response = client.post("/api/admin/logout", json={}, headers={"Cookie": "vote_admin=" + first_token})
    assert response.status_code == 200
    assert client.get("/api/admin/state", headers={"Cookie": "vote_admin=" + first_token}).status_code == 401
    assert client.get("/api/admin/state", headers={"Cookie": "vote_admin=" + second_token}).status_code == 200
    row = client.app.state.store.db.execute("SELECT token_hash,revoked FROM admin_sessions WHERE revoked=1").fetchone()
    assert row[0] != first_token and row[1] == 1


def test_persistence_survives_restart_including_lock_ban_and_admin_revocation(config):
    with TestClient(create_app(config)) as client:
        client.post("/api/admin/session", json={"password": PASSWORD})
        admin_token = client.cookies.get("vote_admin")
        contestant = open_contestant(client, add_contestant(client))
        viewer = new_session(client)
        cast(client, viewer, contestant)
        action(client, "ban", userId=viewer["userId"], seconds=300)
        action(client, "lock", contestantId=contestant["id"])
        previous_stream = snapshot(client, viewer)["streamId"]
        client.post("/api/admin/logout", json={})
    with TestClient(create_app(config)) as restarted:
        recovered = new_session(restarted, tokens=[viewer["token"]])
        assert recovered["userId"] == viewer["userId"]
        assert recovered["snapshot"]["streamId"] != previous_stream
        assert recovered["snapshot"]["me"]["votes"] == [contestant["id"]]
        assert recovered["snapshot"]["me"]["bannedUntil"] > 0
        assert recovered["snapshot"]["contestants"][0]["voting"] == "locked"
        assert restarted.get("/api/admin/state", headers={"Cookie": "vote_admin=" + admin_token}).status_code == 401


def test_second_worker_is_rejected_and_missing_password_fails_closed(config):
    first = VoteStore(config)
    try:
        with pytest.raises(RuntimeError, match="单 worker"):
            VoteStore(config)
    finally:
        first.close()
    with pytest.raises(RuntimeError, match="ADMIN_PASSWORD"):
        VoteStore(replace(config, admin_password=""))


def test_concurrent_votes_and_lock_leave_database_totals_consistent(client):
    contestant = open_contestant(client, add_contestant(client))
    viewers = [new_session(client) for _ in range(24)]
    revision = admin_state(client)["revision"]
    barrier = threading.Barrier(25)

    def voter(viewer):
        barrier.wait(timeout=10)
        return cast(client, viewer, contestant).status_code

    def locker():
        barrier.wait(timeout=10)
        return action(client, "lock", revision=revision, contestantId=contestant["id"]).status_code

    with ThreadPoolExecutor(max_workers=25) as pool:
        futures = [pool.submit(voter, viewer) for viewer in viewers]
        lock_future = pool.submit(locker)
        results = [future.result(timeout=20) for future in futures]
        assert lock_future.result(timeout=20) == 200
    assert set(results) <= {200, 409}
    row = admin_state(client)["contestants"][0]
    assert row["voting"] == "locked"
    assert row["rawVotes"] == results.count(200)
    selected = client.app.state.store.db.execute("SELECT COUNT(*) FROM votes WHERE selected=1").fetchone()[0]
    assert selected == row["rawVotes"]
    for viewer in viewers[:3]:
        assert cast(client, viewer, contestant, voted=False).status_code == 409


def test_slow_streams_are_bounded_and_private_events_are_isolated(config):
    store = VoteStore(config)
    try:
        async def exercise():
            hub = EventHub(store)
            first = hub.subscribe("one")
            second = hub.subscribe("two")
            admin = hub.subscribe("admin", admin=True)
            hub.publish("me", {"id": "one", "votes": ["x"]}, user_id="one")
            assert "event: me" in first.queue.get_nowait()
            assert second.queue.empty() and admin.queue.empty()
            for index in range(30):
                hub.publish("state", {"revision": index})
            assert first.queue.qsize() == 2
            assert "slow_client" in first.queue.get_nowait()
            assert first.queue.get_nowait() is None
            assert first.id not in hub.clients
            assert admin.id in hub.clients
        asyncio.run(exercise())
    finally:
        store.close()


def test_sse_bearer_snapshot_and_lock_propagate_without_polling(config):
    """真实 TCP SSE：鉴权、分帧、立即锁票与双观众身份隔离。"""
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(create_app(config), log_level="error", access_log=False, lifespan="on", timeout_graceful_shutdown=1))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.01)
    assert server.started

    async def scenario():
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}", timeout=5, trust_env=False) as browser:
            assert (await browser.post("/api/admin/session", json={"password": PASSWORD})).status_code == 200
            async def admin(name, **fields):
                revision = (await browser.get("/api/admin/state")).json()["revision"]
                response = await browser.post("/api/admin/action", json={"action": name, "expectedRevision": revision, "requestId": request_id(), **fields})
                assert response.status_code == 200
                return response.json()["state"]
            state = await admin("upsert_contestant", contestant={"name": "SSE测试选手", "group": "A组"})
            contestant_id = state["contestants"][0]["id"]
            await admin("open", contestantId=contestant_id)
            first = (await browser.post("/api/session", json={}, headers={"Cookie": ""})).json()
            second = (await browser.post("/api/session", json={}, headers={"Cookie": ""})).json()

            async def next_event(lines):
                name, data = None, None
                async for line in lines:
                    if line.startswith("event: "):
                        name = line[7:]
                    elif line.startswith("data: "):
                        data = json.loads(line[6:])
                    elif line == "" and name is not None:
                        return name, data
                raise AssertionError("SSE prematurely closed")

            async with browser.stream("GET", "/api/events", headers=auth(first)) as one:
                assert one.status_code == 200
                assert one.headers["x-accel-buffering"] == "no"
                first_lines = one.aiter_lines()
                name, initial = await next_event(first_lines)
                assert name == "snapshot" and initial["me"]["id"] == first["userId"]
                async with browser.stream("GET", "/api/events", headers=auth(second)) as two:
                    second_lines = two.aiter_lines()
                    _, second_initial = await next_event(second_lines)
                    assert second_initial["me"]["id"] == second["userId"]
                    await admin("publish", contestantIds=[contestant_id], visible=True)
                    assert (await next_event(first_lines))[0] == "state"
                    assert (await next_event(second_lines))[0] == "state"
                    voted = await browser.put("/api/votes/" + contestant_id, headers=auth(first), json={
                        "voted": True, "epoch": initial["contestants"][0]["epoch"], "requestId": request_id(),
                    })
                    assert voted.status_code == 200
                    name, private = await next_event(first_lines)
                    assert name == "me" and private["id"] == first["userId"]
                    name, counts = await asyncio.wait_for(next_event(second_lines), timeout=4)
                    assert name == "counts"
                    assert counts["counts"] == [{"id": contestant_id, "votes": 1}]
                    assert set(counts) == {"revision", "streamId", "serverTime", "counts"}
                    assert (await next_event(first_lines))[0] == "counts"
                    started = time.monotonic()
                    await admin("lock", contestantId=contestant_id)
                    name, changed = await asyncio.wait_for(next_event(first_lines), timeout=1.5)
                    assert name == "state"
                    assert changed["contestants"][0]["voting"] == "locked"
                    assert "me" not in changed
                    _, second_changed = await asyncio.wait_for(next_event(second_lines), timeout=1.5)
                    assert second_changed["contestants"][0]["voting"] == "locked"
                    assert time.monotonic() - started < 1.5

    try:
        asyncio.run(scenario())
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        listener.close()
    assert not thread.is_alive()


def test_csv_export_escapes_spreadsheet_formula_names(client):
    add_contestant(client, name="=HYPERLINK(\"bad\")", group="+danger")
    response = client.get("/api/admin/export")
    assert response.status_code == 200
    assert "'=HYPERLINK" in response.text
    assert "'+danger" in response.text
    assert client.get("/api/admin/export", headers={"Cookie": ""}).status_code == 401
