"""
Gmail client for fetching and querying emails.
Handles OAuth authentication and message retrieval.
"""
import os
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import GMAIL_SCOPES, GOOGLE_CLIENT_SECRET_PATH, GOOGLE_TOKEN_PATH, GMAIL_USER
from app.utils.logger import setup_logger
from app.utils.text_clean import extract_plain_text

logger = setup_logger(__name__)


class GmailClient:
    """Gmail API client for reading job-related emails."""
    
    def __init__(self):
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        creds = None
        
        # Load existing token
        if os.path.exists(GOOGLE_TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_PATH, GMAIL_SCOPES)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                logger.info("Starting new OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    GOOGLE_CLIENT_SECRET_PATH, GMAIL_SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(GOOGLE_TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
            
            logger.info("Credentials saved")
        
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail API client initialized")
    
    def query_messages(
        self,
        query: str,
        max_results: int = 100,
        after_date: Optional[datetime] = None
    ) -> List[str]:
        """
        Query Gmail messages by search query.
        
        Args:
            query: Gmail search query
            max_results: Maximum number of messages to return
            after_date: Only return messages after this date
        
        Returns:
            List of message IDs
        """
        try:
            # Add date filter if provided
            if after_date:
                date_str = after_date.strftime('%Y/%m/%d')
                query = f"{query} after:{date_str}"
            
            logger.info(f"Querying Gmail: {query}")
            
            results = self.service.users().messages().list(
                userId=GMAIL_USER,
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            message_ids = [msg['id'] for msg in messages]
            
            logger.info(f"Found {len(message_ids)} messages")
            return message_ids
        
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return []
    
    def get_message(self, message_id: str) -> Optional[Dict]:
        """
        Get full message details.
        
        Args:
            message_id: Gmail message ID
        
        Returns:
            Message dictionary with metadata and body
        """
        try:
            message = self.service.users().messages().get(
                userId=GMAIL_USER,
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = {
                header['name']: header['value']
                for header in message['payload'].get('headers', [])
            }
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            # Parse date
            date_str = headers.get('Date', '')
            try:
                received_at = parsedate_to_datetime(date_str)
            except Exception:
                received_at = datetime.utcnow()
            
            return {
                'id': message['id'],
                'thread_id': message['threadId'],
                'subject': headers.get('Subject', ''),
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'date': date_str,
                'received_at': received_at,
                'snippet': message.get('snippet', ''),
                'body': body,
                'labels': message.get('labelIds', [])
            }
        
        except HttpError as error:
            logger.error(f"Error fetching message {message_id}: {error}")
            return None
    
    def _extract_body(self, payload: Dict) -> str:
        """
        Extract email body from message payload.
        
        Args:
            payload: Message payload from Gmail API
        
        Returns:
            Plain text body
        """
        body = ""
        
        # Check if message has parts
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html':
                    data = part['body'].get('data', '')
                    if data:
                        html = base64.urlsafe_b64decode(data).decode('utf-8')
                        body = extract_plain_text(html)
        else:
            # No parts, get body directly
            data = payload['body'].get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                
                # Clean if HTML
                if payload.get('mimeType') == 'text/html':
                    body = extract_plain_text(body)
        
        return body.strip()
    
    def get_messages_since(self, since: datetime, query: str = "") -> List[Dict]:
        """
        Get all messages since a specific datetime.
        
        Args:
            since: Get messages after this datetime
            query: Additional search query
        
        Returns:
            List of message dictionaries
        """
        # Query for messages
        message_ids = self.query_messages(query=query, after_date=since, max_results=100)
        
        # Fetch full message details
        messages = []
        for msg_id in message_ids:
            msg = self.get_message(msg_id)
            if msg:
                messages.append(msg)
        
        return messages
    
    def search_job_related_emails(self, since: Optional[datetime] = None) -> List[Dict]:
        """
        Search for job-related emails.
        
        Args:
            since: Optional datetime to search from
        
        Returns:
            List of job-related messages
        """
        # Build search query for common job platforms and keywords
        queries = [
            "from:(greenhouse.io OR lever.co OR workday.com OR myworkdayjobs.com)",
            "from:(icims.com OR smartrecruiters.com OR taleo.net OR successfactors.com)",
            "from:(jobvite.com OR ashbyhq.com OR jazz.co OR breezy.hr)",
            'subject:("application" OR "interview" OR "assessment" OR "coding challenge")',
        ]
        
        all_messages = []
        
        for query in queries:
            messages = self.get_messages_since(since or datetime.utcnow() - timedelta(days=30), query)
            all_messages.extend(messages)
        
        # Deduplicate by message ID
        seen = set()
        unique_messages = []
        for msg in all_messages:
            if msg['id'] not in seen:
                seen.add(msg['id'])
                unique_messages.append(msg)
        
        logger.info(f"Found {len(unique_messages)} unique job-related emails")
        return unique_messages


if __name__ == "__main__":
    # Test Gmail client
    client = GmailClient()
    messages = client.search_job_related_emails()
    print(f"Found {len(messages)} job-related emails")
    
    if messages:
        print("\nSample message:")
        msg = messages[0]
        print(f"Subject: {msg['subject']}")
        print(f"From: {msg['from']}")
        print(f"Date: {msg['date']}")
