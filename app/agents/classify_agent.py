"""
ClassifyAgent: Classifies job-related emails into event types.
Determines event_type and suggested status update.
"""
import re
from typing import Dict
from app.config import EVENT_TYPES, APPLICATION_STATUSES
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ClassifyAgent:
    """Agent to classify job email event types."""
    
    def __init__(self):
        self.event_types = EVENT_TYPES
        self.rejection_patterns = [
            r'unfortunately',
            r'not\s+(moving\s+forward|selected|chosen)',
            r'will\s+not\s+be\s+(moving|proceeding)',
            r'decided\s+to\s+(pursue|move\s+forward\s+with)\s+other',
            r'have\s+decided\s+not\s+to',
            r'regret\s+to\s+inform',
            r'not\s+be\s+considered',
            r'position\s+has\s+been\s+filled',
            r'your\s+application\s+was\s+not\s+successful',
        ]
        
        self.interview_patterns = [
            r'interview',
            r'schedule\s+(a\s+)?(call|meeting|chat)',
            r'speak\s+with\s+you',
            r'next\s+step',
            r'phone\s+(screen|call)',
            r'video\s+call',
            r'meet\s+with',
            r'available\s+for\s+(a\s+)?(call|chat)',
        ]
        
        self.assessment_patterns = [
            r'coding\s+(challenge|test|assessment)',
            r'technical\s+(challenge|test|assessment)',
            r'complete\s+(the\s+)?(assignment|challenge|test)',
            r'take-home\s+(challenge|assignment)',
            r'hackerrank',
            r'codility',
            r'codesignal',
        ]
        
        self.confirmation_patterns = [
            r'thank\s+you\s+for\s+(applying|your\s+application)',
            r'application\s+(received|submitted)',
            r'received\s+your\s+application',
            r'confirm\s+receipt',
            r'we\s+have\s+received',
        ]
        
        self.offer_patterns = [
            r'offer\s+(of\s+employment|letter)',
            r'pleased\s+to\s+offer',
            r'extend\s+(an\s+)?offer',
            r'congratulations',
            r'offer\s+package',
        ]
    
    def run(self, email_data: Dict) -> Dict:
        """
        Classify email event type.
        
        Args:
            email_data: Dictionary with 'subject', 'body', 'snippet'
        
        Returns:
            {
                'event_type': str,
                'status_update': str,
                'confidence': float,
                'indicators': list
            }
        """
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        snippet = email_data.get('snippet', '').lower()
        
        # Combined text
        combined_text = f"{subject} {snippet} {body[:1000]}"
        
        # Check patterns in priority order
        results = []
        
        # 1. Rejection (highest priority)
        rejection_score = self._match_patterns(combined_text, self.rejection_patterns)
        if rejection_score > 0:
            results.append(('rejection', 'rejected', rejection_score))
        
        # 2. Offer
        offer_score = self._match_patterns(combined_text, self.offer_patterns)
        if offer_score > 0:
            results.append(('offer', 'offer', offer_score * 1.2))
        
        # 3. Interview
        interview_score = self._match_patterns(combined_text, self.interview_patterns)
        if interview_score > 0:
            results.append(('interview', 'interview', interview_score))
        
        # 4. Assessment
        assessment_score = self._match_patterns(combined_text, self.assessment_patterns)
        if assessment_score > 0:
            results.append(('assessment', 'assessment', assessment_score))
        
        # 5. Confirmation
        confirmation_score = self._match_patterns(combined_text, self.confirmation_patterns)
        if confirmation_score > 0:
            results.append(('confirmation', 'applied', confirmation_score * 0.8))
        
        # Select best match
        if results:
            # Sort by score (descending)
            results.sort(key=lambda x: x[2], reverse=True)
            event_type, status_update, raw_score = results[0]
            confidence = min(1.0, raw_score / 3.0)
            
            indicators = [r[0] for r in results]
        else:
            # Default to 'update'
            event_type = 'update'
            status_update = 'in_review'
            confidence = 0.3
            indicators = []
        
        logger.debug(f"Classified '{subject[:50]}...' as {event_type} (confidence: {confidence:.2f})")
        
        return {
            'event_type': event_type,
            'status_update': status_update,
            'confidence': confidence,
            'indicators': indicators
        }
    
    def _match_patterns(self, text: str, patterns: list) -> float:
        """
        Match patterns in text and return score.
        
        Args:
            text: Text to search
            patterns: List of regex patterns
        
        Returns:
            Match score
        """
        score = 0.0
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                score += len(matches)
        
        return score
