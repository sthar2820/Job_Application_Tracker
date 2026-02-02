"""
Configuration management for Job Application Tracker.
Loads environment variables and validates configuration.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_EMAILS_DIR = DATA_DIR / "sample_emails"

# Google Gmail API Configuration
GOOGLE_CLIENT_SECRET_PATH = os.getenv("GOOGLE_CLIENT_SECRET_PATH", "credentials.json")
GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
GMAIL_USER = os.getenv("GMAIL_USER", "me")

# Gmail API scopes
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Polling Configuration
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "120"))

# Database Configuration
DB_PATH = os.getenv("DB_PATH", "./job_applications.db")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Application Status Values
APPLICATION_STATUSES = [
    "applied",
    "in_review",
    "assessment",
    "interview",
    "rejected",
    "offer",
    "other"
]

# Event Types
EVENT_TYPES = [
    "confirmation",
    "rejection",
    "interview",
    "assessment",
    "offer",
    "update",
    "other"
]

# Job Platform Domains
JOB_PLATFORMS = {
    "greenhouse.io": "Greenhouse",
    "lever.co": "Lever",
    "workday.com": "Workday",
    "myworkdayjobs.com": "Workday",
    "icims.com": "iCIMS",
    "smartrecruiters.com": "SmartRecruiters",
    "taleo.net": "Taleo",
    "successfactors.com": "SuccessFactors",
    "jobvite.com": "Jobvite",
    "breezy.hr": "Breezy HR",
    "ashbyhq.com": "Ashby",
    "jazz.co": "JazzHR",
}

# Job-related keywords for filtering
JOB_KEYWORDS = [
    "application",
    "thank you for applying",
    "unfortunately",
    "interview",
    "assessment",
    "coding challenge",
    "technical challenge",
    "offer",
    "congratulations",
    "position",
    "role",
    "candidate",
    "requisition",
    "applied to",
    "application received",
    "not moving forward",
    "next steps",
    "schedule",
    "rejected",
    "declined",
]


def validate_config():
    """Validate that required configuration is present."""
    errors = []
    
    if not os.path.exists(GOOGLE_CLIENT_SECRET_PATH):
        errors.append(f"Google client secret file not found: {GOOGLE_CLIENT_SECRET_PATH}")
    
    if POLL_INTERVAL_SECONDS < 60:
        errors.append("POLL_INTERVAL_SECONDS should be at least 60 seconds to avoid rate limits")
    
    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True


if __name__ == "__main__":
    try:
        validate_config()
        print("✓ Configuration is valid")
        print(f"  Database: {DB_PATH}")
        print(f"  Poll interval: {POLL_INTERVAL_SECONDS}s")
        print(f"  Gmail user: {GMAIL_USER}")
    except ValueError as e:
        print(f"✗ {e}")
