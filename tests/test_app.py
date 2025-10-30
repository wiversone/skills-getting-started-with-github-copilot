import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_get_activities():
    """Test GET /activities endpoint"""
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    assert isinstance(activities, dict)
    # Check if we have at least one activity
    assert len(activities) > 0
    # Check structure of an activity
    for activity_name, details in activities.items():
        assert isinstance(activity_name, str)
        assert isinstance(details, dict)
        assert "description" in details
        assert "schedule" in details
        assert "max_participants" in details
        assert "participants" in details
        assert isinstance(details["participants"], list)

def test_signup_for_activity():
    """Test POST /activities/{activity}/signup endpoint"""
    # First get available activities
    activities = client.get("/activities").json()
    activity_name = list(activities.keys())[0]
    test_email = "test@mergington.edu"
    
    # Try to sign up
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": test_email}
    )
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    
    # Verify participant was added
    activities = client.get("/activities").json()
    assert test_email in activities[activity_name]["participants"]

def test_unregister_from_activity():
    """Test POST /activities/{activity}/unregister endpoint"""
    # First get available activities
    activities = client.get("/activities").json()
    activity_name = list(activities.keys())[0]
    test_email = "unregister_test@mergington.edu"
    
    # First sign up
    client.post(
        f"/activities/{activity_name}/signup",
        params={"email": test_email}
    )
    
    # Then unregister
    response = client.post(
        f"/activities/{activity_name}/unregister",
        params={"email": test_email}
    )
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    
    # Verify participant was removed
    activities = client.get("/activities").json()
    assert test_email not in activities[activity_name]["participants"]

def test_signup_full_activity():
    """Test signup when activity is full"""
    # First get available activities
    activities = client.get("/activities").json()
    
    # Find an activity with available spots
    activity_name = None
    for name, details in activities.items():
        if len(details["participants"]) < details["max_participants"]:
            activity_name = name
            activity = details
            break
    
    assert activity_name is not None, "No activity with available spots found"
    
    # Calculate how many spots are available
    available_spots = activity["max_participants"] - len(activity["participants"])
    
    # Fill up the remaining spots
    for i in range(available_spots + 1):
        email = f"test{i}@mergington.edu"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        if i < available_spots:
            assert response.status_code == 200
        else:
            # This one should fail as the activity is full
            assert response.status_code == 400
            assert "full" in response.json()["detail"].lower()

def test_invalid_activity():
    """Test signup/unregister with invalid activity name"""
    test_email = "test@mergington.edu"
    invalid_activity = "nonexistent_activity"
    
    # Try to sign up
    response = client.post(
        f"/activities/{invalid_activity}/signup",
        params={"email": test_email}
    )
    assert response.status_code == 404
    
    # Try to unregister
    response = client.post(
        f"/activities/{invalid_activity}/unregister",
        params={"email": test_email}
    )
    assert response.status_code == 404

def test_duplicate_signup():
    """Test signing up the same email twice"""
    # First get available activities
    activities = client.get("/activities").json()
    
    # Find an activity with available spots
    activity_name = None
    for name, details in activities.items():
        if len(details["participants"]) < details["max_participants"]:
            activity_name = name
            break
    
    assert activity_name is not None, "No activity with available spots found"
    test_email = "duplicate@mergington.edu"
    
    # First signup should succeed
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": test_email}
    )
    assert response.status_code == 200
    
    # Verify first signup succeeded
    activities = client.get("/activities").json()
    assert test_email in activities[activity_name]["participants"]
    
    # Second signup should fail with 400
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": test_email}
    )
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()