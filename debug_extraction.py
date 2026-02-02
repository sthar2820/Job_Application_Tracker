"""Debug script to show what's being extracted from emails."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.gmail_client import GmailClient
from app.agents.extract_agent import ExtractAgent

def debug_extractions():
    """Show extractions from recent job emails."""
    gmail = GmailClient()
    extract_agent = ExtractAgent()
    
    # Get recent job emails
    messages = gmail.search_job_related_emails(since=None)
    print(f"Found {len(messages)} job-related emails\n")
    
    count = 0
    for msg in messages:
        count += 1
        if count > 15:  # Only show first 15
            break
            
        print(f"\n{'='*80}")
        print(f"Email #{count}")
        print(f"{'='*80}")
        print(f"Subject: {msg['subject'][:100]}")
        print(f"From: {msg['from'][:80]}")
        
        # Extract
        extraction = extract_agent.run({
            'from': msg['from'],
            'subject': msg['subject'],
            'snippet': msg['snippet'],
            'body': msg.get('body', '')
        })
        
        print(f"\nExtracted:")
        print(f"  Company: {extraction.get('company', 'N/A')}")
        print(f"  Role: {extraction.get('role_title', 'N/A')}")
        
if __name__ == "__main__":
    debug_extractions()
