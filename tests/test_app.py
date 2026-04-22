"""
Tests for the Mergington High School Activities API.
All tests follow the Arrange-Act-Assert (AAA) pattern.
"""

import pytest


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_index(self, client):
        """Test that root endpoint redirects to static/index.html."""
        # Arrange
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_all_activities_returns_success(self, client):
        """Test that get_activities returns 200 with all activities."""
        # Arrange
        expected_activities = {
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Soccer Club",
            "Art Club",
            "Drama Club",
            "Debate Club",
            "Science Club"
        }
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert set(data.keys()) == expected_activities

    def test_activities_contain_required_fields(self, client):
        """Test that each activity has all required fields."""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            assert set(activity_data.keys()) == required_fields
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)

    def test_activities_participants_are_emails(self, client):
        """Test that participant lists contain valid emails."""
        # Arrange
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            for participant in activity_data["participants"]:
                assert "@" in participant
                assert "mergington.edu" in participant


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_student_succeeds(self, client, sample_email):
        """Test that a new student can successfully sign up for an activity."""
        # Arrange
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]
        assert sample_email in data["message"]

    def test_signup_duplicate_student_fails(self, client):
        """Test that duplicate signups are rejected with 400 error."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_fails(self, client, sample_email):
        """Test that signup for non-existent activity returns 404."""
        # Arrange
        activity_name = "Nonexistent Activity"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_adds_participant_to_activity(self, client, sample_email):
        """Test that signup actually adds the participant to the activity."""
        # Arrange
        activity_name = "Gym Class"
        
        # Act - Sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        # Get activities to verify
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        assert sample_email in data[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""

    def test_unregister_signed_up_student_succeeds(self, client, sample_email):
        """Test that a signed-up student can successfully unregister."""
        # Arrange
        activity_name = "Gym Class"
        # First, sign up the student
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_not_signed_up_student_fails(self, client):
        """Test that unregistering a non-participant returns 400."""
        # Arrange
        activity_name = "Chess Club"
        email = "never.registered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_from_nonexistent_activity_fails(self, client, sample_email):
        """Test that unregister from non-existent activity returns 404."""
        # Arrange
        activity_name = "Nonexistent Activity"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_removes_participant_from_activity(self, client):
        """Test that unregister actually removes the participant from the activity."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        # First get initial count
        response_before = client.get("/activities")
        initial_count = len(response_before.json()[activity_name]["participants"])
        
        # Act - Unregister
        client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        # Get activities to verify
        response_after = client.get("/activities")
        
        # Assert
        data = response_after.json()
        final_count = len(data[activity_name]["participants"])
        assert final_count == initial_count - 1
        assert email not in data[activity_name]["participants"]


class TestIntegration:
    """Integration tests for multiple operations."""

    def test_signup_then_unregister_flow(self, client, sample_email):
        """Test the complete flow of signing up and then unregistering."""
        # Arrange
        activity_name = "Programming Class"
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        # Assert - Signup successful
        assert signup_response.status_code == 200
        
        # Act - Verify participant is added
        activities_response = client.get("/activities")
        assert sample_email in activities_response.json()[activity_name]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        # Assert - Unregister successful
        assert unregister_response.status_code == 200
        
        # Act - Verify participant is removed
        final_activities_response = client.get("/activities")
        assert sample_email not in final_activities_response.json()[activity_name]["participants"]

    def test_multiple_students_can_signup_for_same_activity(self, client):
        """Test that multiple different students can sign up for the same activity."""
        # Arrange
        activity_name = "Basketball Team"
        students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        # Act - Sign up all students
        for email in students:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert - All students are in the activity
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        for email in students:
            assert email in participants
