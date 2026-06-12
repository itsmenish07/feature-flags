import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import main
from database import Base


@pytest.fixture
def client(tmp_path):
    db_path = (tmp_path / "test.db").as_posix()
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    TestingSession = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[main.get_db] = override_get_db

    with TestClient(main.app) as c:
        yield c

    main.app.dependency_overrides.clear()


def test_create_and_list_flag(client):
    res = client.post("/flags", params={"name": "checkout"})
    body = res.json()

    assert body["name"] == "checkout"
    assert body["enabled"] is False
    assert body["rollout_percentage"] == 100

    flags = client.get("/flags").json()
    assert [f["name"] for f in flags] == ["checkout"]


def test_duplicate_flag_is_rejected(client):
    client.post("/flags", params={"name": "checkout"})
    res = client.post("/flags", params={"name": "checkout"})

    assert res.json() == {"error": "Flag already exists"}
    assert len(client.get("/flags").json()) == 1


def test_toggle_flag(client):
    flag_id = client.post("/flags", params={"name": "checkout"}).json()["id"]

    assert client.put(f"/flags/{flag_id}").json()["enabled"] is True
    assert client.put(f"/flags/{flag_id}").json()["enabled"] is False


def test_update_rule(client):
    flag_id = client.post("/flags", params={"name": "checkout"}).json()["id"]

    res = client.put(
        f"/flags/{flag_id}/rule",
        params={"target_group": "beta", "rollout_percentage": 40}
    ).json()

    assert res["target_group"] == "beta"
    assert res["rollout_percentage"] == 40


def test_rule_clamps_rollout(client):
    flag_id = client.post("/flags", params={"name": "checkout"}).json()["id"]

    over = client.put(f"/flags/{flag_id}/rule", params={"rollout_percentage": 250})
    assert over.json()["rollout_percentage"] == 100


def test_delete_flag(client):
    flag_id = client.post("/flags", params={"name": "checkout"}).json()["id"]

    assert client.delete(f"/flags/{flag_id}").json() == {"deleted": flag_id}
    assert client.get("/flags").json() == []


def test_delete_missing_flag(client):
    assert client.delete("/flags/999").json() == {"error": "Flag not found"}


def test_config_crud(client):
    created = client.post(
        "/configs",
        params={"key": "welcome", "value": "hi"}
    ).json()
    assert created["value"] == "hi"

    dup = client.post("/configs", params={"key": "welcome", "value": "hey"})
    assert dup.json() == {"error": "Config already exists"}

    updated = client.put(
        f"/configs/{created['id']}",
        params={"value": "hello"}
    ).json()
    assert updated["value"] == "hello"

    assert client.delete(f"/configs/{created['id']}").json() == {
        "deleted": created["id"]
    }


def test_group_filter(client):
    client.post("/flags", params={"name": "beta_only", "target_group": "beta"})
    client.post("/flags", params={"name": "shared", "target_group": "everyone"})

    names = {f["name"] for f in client.get("/flags/group/beta").json()}
    assert names == {"beta_only", "shared"}

    names = {f["name"] for f in client.get("/flags/group/pro").json()}
    assert names == {"shared"}


def test_rollout_is_consistent_per_user(client):
    flag_id = client.post(
        "/flags",
        params={"name": "checkout", "rollout_percentage": 50}
    ).json()["id"]
    client.put(f"/flags/{flag_id}")

    first = client.get("/flags/user/user-7/everyone").json()
    second = client.get("/flags/user/user-7/everyone").json()
    assert first == second
