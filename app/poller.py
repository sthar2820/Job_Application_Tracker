"""
Email polling worker for Job Application Tracker.
Runs every N minutes to check for new job-related emails and process them.
"""
import time
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import POLL_INTERVAL_SECONDS
from app.utils.logger import setup_logger
from app.utils.gmail_client import GmailClient
from app.utils.dedupe import get_unprocessed_messages
from app.utils.text_clean import extract_email_domain
from app.db.models import (
    get_system_state,
    set_system_state,
    mark_email_processed,
    update_application_status,
    create_event
)
from app.agents.filter_agent import FilterAgent
from app.agents.classify_agent import ClassifyAgent
from app.agents.extract_agent import ExtractAgent
from app.agents.resolve_agent import ResolveAgent
from app.agents.action_agent import ActionAgent

logger = setup_logger(__name__)


class EmailPoller:
    """Worker that polls Gmail for job-related emails."""
    
    def __init__(self):
        self.gmail_client = GmailClient()
        self.filter_agent = FilterAgent()
        self.classify_agent = ClassifyAgent()
        self.extract_agent = ExtractAgent()
        self.resolve_agent = ResolveAgent()
        self.action_agent = ActionAgent()
    
    def poll_once(self):
        """Run one polling cycle."""
        logger.info("=" * 60)
        logger.info("Starting polling cycle")
        
        try:
            # Get last checked timestamp
            last_checked_iso = get_system_state('last_checked_iso')
            
            if last_checked_iso:
                last_checked = datetime.fromisoformat(last_checked_iso)
                logger.info(f"Last checked: {last_checked}")
            else:
                # Default to 30 days ago
                last_checked = datetime.utcnow() - timedelta(days=30)
                logger.info("No previous check found, searching last 30 days")
            
            # Fetch new job-related emails
            messages = self.gmail_client.search_job_related_emails(since=last_checked)
            logger.info(f"Found {len(messages)} potential job emails")
            
            # Filter out already processed
            unprocessed = get_unprocessed_messages(messages)
            logger.info(f"{len(unprocessed)} new messages to process")
            
            # Process each message
            processed_count = 0
            for message in unprocessed:
                try:
                    self._process_message(message)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing message {message['id']}: {e}", exc_info=True)
            
            # Update last checked timestamp
            set_system_state('last_checked_iso', datetime.utcnow().isoformat())
            
            logger.info(f"Polling cycle complete. Processed {processed_count}/{len(unprocessed)} messages")
        
        except Exception as e:
            logger.error(f"Error in polling cycle: {e}", exc_info=True)
    
    def _process_message(self, message: dict):
        """Process a single email message through the agent pipeline."""
        msg_id = message['id']
        subject = message['subject']
        
        logger.info(f"Processing: {subject[:60]}...")
        
        # Step 1: Filter - is it job-related?
        filter_result = self.filter_agent.run(message)
        
        if not filter_result['is_job_related']:
            logger.debug(f"Skipping (not job-related): {filter_result['reason']}")
            # Still mark as processed to avoid reprocessing
            from_domain = extract_email_domain(message['from'])
            mark_email_processed(
                message_id=msg_id,
                thread_id=message['thread_id'],
                received_at=message['received_at'],
                from_domain=from_domain or '',
                subject=subject,
                classification='not_job_related'
            )
            return
        
        logger.debug(f"✓ Job-related: {filter_result['reason']}")
        
        # Step 2: Classify event type
        classify_result = self.classify_agent.run(message)
        event_type = classify_result['event_type']
        status_update = classify_result['status_update']
        confidence = classify_result['confidence']
        
        logger.debug(f"✓ Classified as: {event_type} (confidence: {confidence:.2f})")
        
        # Step 3: Extract structured data
        extracted_data = self.extract_agent.run(message)
        company = extracted_data['company']
        role_title = extracted_data['role_title']
        
        logger.debug(f"✓ Extracted: {company} - {role_title}")
        
        # Step 4: Resolve to application
        resolve_result = self.resolve_agent.run(extracted_data)
        application_id = resolve_result['application_id']
        is_new = resolve_result['is_new']
        match_method = resolve_result['match_method']
        
        logger.debug(f"✓ Resolved to application {application_id} ({match_method}, new={is_new})")
        
        # Step 5: Generate action suggestion
        action_result = self.action_agent.run(event_type, extracted_data)
        action_suggestion = action_result['action_suggestion']
        
        logger.debug(f"✓ Action: {action_suggestion[:60]}...")
        
        # Save event
        create_event(
            application_id=application_id,
            event_type=event_type,
            event_time=message['received_at'],
            email_message_id=msg_id,
            subject=subject,
            from_email=message['from'],
            confidence=confidence,
            extracted_json=extracted_data,
            action_suggestion=action_suggestion
        )
        
        # Update application status
        update_application_status(application_id, status_update)
        
        # Mark email as processed
        from_domain = extract_email_domain(message['from'])
        mark_email_processed(
            message_id=msg_id,
            thread_id=message['thread_id'],
            received_at=message['received_at'],
            from_domain=from_domain or '',
            subject=subject,
            classification=event_type
        )
        
        logger.info(f"✓ Successfully processed message for {company} - {role_title}")
    
    def run_forever(self):
        """Run polling loop indefinitely."""
        logger.info(f"Starting email poller (interval: {POLL_INTERVAL_SECONDS}s)")
        
        while True:
            try:
                self.poll_once()
                logger.info(f"Sleeping for {POLL_INTERVAL_SECONDS} seconds...")
                time.sleep(POLL_INTERVAL_SECONDS)
            except KeyboardInterrupt:
                logger.info("Poller stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                logger.info("Continuing after error...")
                time.sleep(POLL_INTERVAL_SECONDS)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Job Application Email Poller")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    
    poller = EmailPoller()
    
    if args.once:
        poller.poll_once()
    else:
        poller.run_forever()


if __name__ == "__main__":
    from datetime import timedelta  # Add missing import
    main()
