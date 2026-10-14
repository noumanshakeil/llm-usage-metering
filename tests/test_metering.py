import pytest

@pytest.mark.asyncio
async def test_usage_and_alert(client):
    k = await client.post("/api/keys", json={"name": "demo", "budget_usd": 0.001})
    kid = k.json()["id"]
    u = await client.post("/api/usage", json={"key_id": kid, "prompt_tokens": 500, "completion_tokens": 500, "model": "mock"})
    assert u.status_code == 200
    dash = await client.get("/api/dashboard")
    assert dash.json()["total_spent"] > 0
