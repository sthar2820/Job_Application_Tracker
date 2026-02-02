"""
ActionAgent: Suggests next steps and follow-up actions.
Provides actionable recommendations based on event type.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ActionAgent:
    """Agent to suggest next actions and follow-ups."""
    
    def run(self, event_type: str, extracted_data: Dict) -> Dict:
        """
        Suggest next action based on event type.
        
        Args:
            event_type: Event type from ClassifyAgent
            extracted_data: Extracted data from ExtractAgent
        
        Returns:
            {
                'action_suggestion': str,
                'follow_up_date': Optional[str] (ISO format)
            }
        """
        company = extracted_data.get('company', 'the company')
        
        # Generate suggestions based on event type
        if event_type == 'confirmation':
            action = f"Application confirmed. Follow up if no response in 7-10 days."
            follow_up_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
        
        elif event_type == 'rejection':
            action = f"Application not selected. Consider requesting feedback (optional). Keep applying!"
            follow_up_date = None
        
        elif event_type == 'interview':
            action = f"Interview scheduled! Prepare: research {company}, review role requirements, prepare questions."
            # Check if date in extracted data
            key_dates = extracted_data.get('key_dates', [])
            if key_dates:
                follow_up_date = key_dates[0]
            else:
                follow_up_date = (datetime.utcnow() + timedelta(days=3)).isoformat()
        
        elif event_type == 'assessment':
            action = f"Complete coding/technical assessment. Review requirements carefully. Set aside focused time."
            follow_up_date = (datetime.utcnow() + timedelta(days=2)).isoformat()
        
        elif event_type == 'offer':
            action = f"🎉 Offer received! Review terms, negotiate if needed, respond within deadline."
            follow_up_date = (datetime.utcnow() + timedelta(days=3)).isoformat()
        
        elif event_type == 'update':
            action = f"Application update received. Review details and wait for next steps."
            follow_up_date = (datetime.utcnow() + timedelta(days=5)).isoformat()
        
        else:
            action = f"Review email and take appropriate action."
            follow_up_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
        
        logger.debug(f"Action for {event_type}: {action}")
        
        return {
            'action_suggestion': action,
            'follow_up_date': follow_up_date
        }
