"""
Backend tests for the Mergington High School Activities API.

Each test follows the Arrange-Act-Assert (AAA) pattern:
  - Arrange: set up inputs and any required preconditions
  - Act:     send exactly one request to the endpoint under test
  - Assert:  verify the status code, response body, and any state change
"""

import copy
import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import app

client = TestClient(app, raise_server_exceptions=True)


@pytest.fixture(autouse=True)
def reset_activities():
    """Snapshot and restore the in-memory activities store before each test
    so mutations in one test cannot affect another."""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects_to_index():
    # Arrange
    expected_redirect = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_redirect


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all_activities():
    # Arrange
    expected_keys = set(app_module.activities.keys())

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert set(response.json().keys()) == expected_keys


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    new_email = "new_student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {new_email} for {activity_name}"}
    assert new_email in app_module.activities[activity_name]["participants"]


def test_signup_returns_404_for_unknown_activity():
    # Arrange
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_400_for_duplicate_email():
    # Arrange
    activity_name = "Chess Club"
    existing_email = app_module.activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_normalizes_email_before_duplicate_check():
    # Arrange
    activity_name = "Chess Club"
    existing_email = app_module.activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": f"  {existing_email.upper()}  "},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_returns_422_for_invalid_email():
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "not-an-email"},
    )

    # Assert
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_removes_participant():
    # Arrange
    activity_name = "Chess Club"
    enrolled_email = app_module.activities[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": enrolled_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {enrolled_email} from {activity_name}"}
    assert enrolled_email not in app_module.activities[activity_name]["participants"]


def test_unregister_returns_404_for_unknown_activity():
    # Arrange
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_for_non_enrolled_student():
    # Arrange
    activity_name = "Chess Club"
    non_enrolled_email = "not_enrolled@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": non_enrolled_email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_normalizes_email_before_lookup():
    # Arrange
    activity_name = "Chess Club"
    enrolled_email = app_module.activities[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": f"  {enrolled_email.upper()}  "},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {enrolled_email} from {activity_name}"}
    assert enrolled_email not in app_module.activities[activity_name]["participants"]
