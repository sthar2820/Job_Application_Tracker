"""
Tests for ClassifyAgent.
Uses anonymized sample email templates.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agents.classify_agent import ClassifyAgent


def test_classify_confirmation():
    """Test confirmation email classification."""
    agent = ClassifyAgent()
    
    email_data = {
        'subject': 'Application Received - Software Engineer',
        'body': 'Thank you for applying to the Software Engineer position. We have received your application and will review it shortly.',
        'snippet': 'Thank you for applying'
    }
    
    result = agent.run(email_data)
    assert result['event_type'] == 'confirmation'
    assert result['status_update'] == 'applied'
    
    print("✓ Test 1 passed: Confirmation classification")


def test_classify_rejection():
    """Test rejection email classification."""
    agent = ClassifyAgent()
    
    email_data = {
        'subject': 'Update on Your Application',
        'body': 'Thank you for your interest in the position. Unfortunately, we have decided to move forward with other candidates at this time.',
        'snippet': 'Unfortunately, we have decided'
    }
    
    result = agent.run(email_data)
    assert result['event_type'] == 'rejection'
    assert result['status_update'] == 'rejected'
    
    print("✓ Test 2 passed: Rejection classification")


def test_classify_interview():
    """Test interview email classification."""
    agent = ClassifyAgent()
    
    email_data = {
        'subject': 'Interview Invitation - Next Steps',
        'body': 'We would like to schedule an interview with you for the Software Engineer position. Please let us know your availability.',
        'snippet': 'schedule an interview'
    }
    
    result = agent.run(email_data)
    assert result['event_type'] == 'interview'
    assert result['status_update'] == 'interview'
    
    print("✓ Test 3 passed: Interview classification")


def test_classify_assessment():
    """Test assessment email classification."""
    agent = ClassifyAgent()
    
    email_data = {
        'subject': 'Complete Your Coding Challenge',
        'body': 'As a next step, please complete the coding challenge. You will have 48 hours to submit your solution.',
        'snippet': 'coding challenge'
    }
    
    result = agent.run(email_data)
    assert result['event_type'] == 'assessment'
    assert result['status_update'] == 'assessment'
    
    print("✓ Test 4 passed: Assessment classification")


def test_classify_offer():
    """Test offer email classification."""
    agent = ClassifyAgent()
    
    email_data = {
        'subject': 'Congratulations! Job Offer',
        'body': 'We are pleased to extend an offer of employment for the Software Engineer position. Please review the attached offer letter.',
        'snippet': 'pleased to extend an offer'
    }
    
    result = agent.run(email_data)
    assert result['event_type'] == 'offer'
    assert result['status_update'] == 'offer'
    
    print("✓ Test 5 passed: Offer classification")


def test_classify_update():
    """Test generic update email classification."""
    agent = ClassifyAgent()
    
    email_data = {
        'subject': 'Application Status Update',
        'body': 'Your application is currently under review by our hiring team. We will contact you with next steps.',
        'snippet': 'under review'
    }
    
    result = agent.run(email_data)
    # Should default to update or in_review
    assert result['event_type'] in ['update', 'confirmation']
    
    print("✓ Test 6 passed: Update classification")


def test_rejection_priority():
    """Test that rejection takes priority over other classifications."""
    agent = ClassifyAgent()
    
    # Email with both interview mention and rejection
    email_data = {
        'subject': 'Interview Update',
        'body': 'Thank you for interviewing with us. Unfortunately, we will not be moving forward with your application at this time.',
        'snippet': 'not be moving forward'
    }
    
    result = agent.run(email_data)
    # Rejection should take priority
    assert result['event_type'] == 'rejection'
    
    print("✓ Test 7 passed: Rejection priority")


def run_all_tests():
    """Run all classify tests."""
    print("Running ClassifyAgent tests...")
    print("=" * 60)
    
    test_classify_confirmation()
    test_classify_rejection()
    test_classify_interview()
    test_classify_assessment()
    test_classify_offer()
    test_classify_update()
    test_rejection_priority()
    
    print("=" * 60)
    print("✓ All ClassifyAgent tests passed!")


if __name__ == "__main__":
    run_all_tests()
