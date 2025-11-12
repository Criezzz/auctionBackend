from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_and_read_item():
    response = client.post("/items/", json={"title": "Hammer", "description": "A tool"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Hammer"
    item_id = data["id"]

    get_resp = client.get(f"/items/{item_id}")
    assert get_resp.status_code == 200
    data2 = get_resp.json()
    assert data2["id"] == item_id
