from fastapi.testclient import TestClient

from src.app import activities


def test_root_redirects_to_static_index(client: TestClient):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_seeded_activities(client: TestClient):
    # Arrange
    expected_activity_names = set(activities)
    expected_fields = {"description", "schedule", "max_participants", "participants"}
    expected_participant = "michael@mergington.edu"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    response_activities = response.json()
    assert set(response_activities) == expected_activity_names
    assert all(set(activity) == expected_fields for activity in response_activities.values())
    assert all(isinstance(activity["participants"], list) for activity in response_activities.values())
    assert expected_participant in response_activities["Chess Club"]["participants"]


def test_signup_adds_participant(client: TestClient):
    # Arrange
    activity_name = "Soccer Club"
    email = "new.student@mergington.edu"
    participants_before = list(activities[activity_name]["participants"])

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert activities[activity_name]["participants"] == participants_before + [email]


def test_signup_rejects_unknown_activity(client: TestClient):
    # Arrange
    activity_name = "Unknown Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant(client: TestClient):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    participants_before = list(activities[activity_name]["participants"])

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert activities[activity_name]["participants"] == participants_before


def test_signup_requires_email(client: TestClient):
    # Arrange
    activity_name = "Soccer Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup")

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]


def test_unregister_removes_only_requested_participant(client: TestClient):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    remaining_participant = "daniel@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]
    assert remaining_participant in activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity(client: TestClient):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_missing_participant(client: TestClient):
    # Arrange
    activity_name = "Soccer Club"
    email = "not.registered@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found in this activity"}


def test_unregister_requires_email(client: TestClient):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants")

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]