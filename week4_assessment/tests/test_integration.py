def test_complete_ticket_lifecycle(real_client):
    create_response = real_client.post(
        "/tickets",
        json={
            "subject": "Email is unavailable",
            "description": "Messages are not loading",
            "severity": 4,
        },
    )

    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]

    first_get_response = real_client.get(f"/tickets/{ticket_id}")

    assert first_get_response.status_code == 200
    assert first_get_response.json()["subject"] == "Email is unavailable"
    assert first_get_response.json()["resolved"] is False

    patch_response = real_client.patch(
        f"/tickets/{ticket_id}",
        json={"severity": 2, "resolved": True},
    )

    assert patch_response.status_code == 200

    second_get_response = real_client.get(f"/tickets/{ticket_id}")

    assert second_get_response.status_code == 200
    assert second_get_response.json()["subject"] == "Email is unavailable"
    assert second_get_response.json()["description"] == "Messages are not loading"
    assert second_get_response.json()["severity"] == 2
    assert second_get_response.json()["resolved"] is True

    delete_response = real_client.delete(f"/tickets/{ticket_id}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    final_get_response = real_client.get(f"/tickets/{ticket_id}")

    assert final_get_response.status_code == 404
    assert final_get_response.json() == {"detail": "Ticket could not be found"}


def test_creation_defaults_persist(real_client):
    create_response = real_client.post(
        "/tickets", json={"subject": "Minor display issue"}
    )
    ticket_id = create_response.json()["id"]

    get_response = real_client.get(f"/tickets/{ticket_id}")

    assert create_response.status_code == 201
    assert get_response.status_code == 200
    assert get_response.json()["description"] is None
    assert get_response.json()["severity"] == 1
    assert get_response.json()["resolved"] is False


def test_put_replacement_persists(real_client):
    create_response = real_client.post(
        "/tickets",
        json={"subject": "Original", "description": "Old", "severity": 2},
    )
    ticket_id = create_response.json()["id"]

    update_response = real_client.put(
        f"/tickets/{ticket_id}",
        json={
            "subject": "Replacement",
            "description": None,
            "severity": 5,
            "resolved": True,
        },
    )
    get_response = real_client.get(f"/tickets/{ticket_id}")

    assert update_response.status_code == 200
    assert get_response.json() == {
        "id": ticket_id,
        "subject": "Replacement",
        "description": None,
        "severity": 5,
        "resolved": True,
    }


def test_list_limit_returns_only_requested_number(real_client):
    real_client.post("/tickets", json={"subject": "First"})
    real_client.post("/tickets", json={"subject": "Second"})
    real_client.post("/tickets", json={"subject": "Third"})

    response = real_client.get("/tickets?limit=2")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert [ticket["subject"] for ticket in response.json()] == ["First", "Second"]
