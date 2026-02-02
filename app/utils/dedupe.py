"""
Deduplication utilities for tracking processed emails.
"""
from typing import Set
from app.db.models import is_email_processed


def is_duplicate(message_id: str) -> bool:
    """
    Check if a message has already been processed.
    
    Args:
        message_id: Gmail message ID
    
    Returns:
        True if already processed, False otherwise
    """
    return is_email_processed(message_id)


def get_unprocessed_messages(messages: list) -> list:
    """
    Filter out already-processed messages.
    
    Args:
        messages: List of message dictionaries with 'id' key
    
    Returns:
        List of unprocessed messages
    """
    unprocessed = []
    
    for msg in messages:
        if not is_duplicate(msg['id']):
            unprocessed.append(msg)
    
    return unprocessed
