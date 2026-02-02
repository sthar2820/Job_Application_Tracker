"""
Tests for ExtractAgent.
Uses anonymized sample email data.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agents.extract_agent import ExtractAgent


def test_extract_company_from_subject():
    """Test company extraction from subject line."""
    agent = ExtractAgent()
    
    # Test case 1: Standard format
    email_data = {
        'subject': 'Your application to Google - Software Engineer',
        'from': 'jobs@greenhouse.io',
        'body': '',
        'snippet': ''
    }
    
    result = agent.run(email_data)
    assert result['company'] == 'Google'
    assert 'Software Engineer' in result['role_title']
    
    print("✓ Test 1 passed: Company extraction from subject")


def test_extract_role_from_subject():
    """Test role extraction from subject line."""
    agent = ExtractAgent()
    
    # Test case 2: Role in subject
    email_data = {
        'subject': 'Microsoft - Senior Data Scientist Position',
        'from': 'recruiting@microsoft.com',
        'body': '',
        'snippet': ''
    }
    
    result = agent.run(email_data)
    assert 'Data Scientist' in result['role_title']
    
    print("✓ Test 2 passed: Role extraction from subject")


def test_extract_portal_link():
    """Test portal link extraction."""
    agent = ExtractAgent()
    
    # Test case 3: Portal link
    email_data = {
        'subject': 'Application Update',
        'from': 'jobs@lever.co',
        'body': 'View your application status: https://jobs.lever.co/company/role-id-123',
        'snippet': ''
    }
    
    result = agent.run(email_data)
    assert result['portal_link'] is not None
    assert 'lever.co' in result['portal_link']
    
    print("✓ Test 3 passed: Portal link extraction")


def test_extract_req_id():
    """Test requisition ID extraction."""
    agent = ExtractAgent()
    
    # Test case 4: Req ID
    email_data = {
        'subject': 'Application Received - Req ID: ABC-12345',
        'from': 'jobs@company.com',
        'body': 'Requisition ID: ABC-12345',
        'snippet': ''
    }
    
    result = agent.run(email_data)
    assert result['req_id'] == 'ABC-12345'
    
    print("✓ Test 4 passed: Requisition ID extraction")


def test_extract_platform():
    """Test platform detection."""
    agent = ExtractAgent()
    
    # Test case 5: Platform
    email_data = {
        'subject': 'Application Received',
        'from': 'no-reply@greenhouse.io',
        'body': '',
        'snippet': ''
    }
    
    result = agent.run(email_data)
    assert result['platform'] == 'Greenhouse'
    
    print("✓ Test 5 passed: Platform detection")


def run_all_tests():
    """Run all extract tests."""
    print("Running ExtractAgent tests...")
    print("=" * 60)
    
    test_extract_company_from_subject()
    test_extract_role_from_subject()
    test_extract_portal_link()
    test_extract_req_id()
    test_extract_platform()
    
    print("=" * 60)
    print("✓ All ExtractAgent tests passed!")


if __name__ == "__main__":
    run_all_tests()
