"""
Text cleaning utilities for email processing.
Strips HTML, normalizes whitespace, and extracts plain text.
"""
import re
from bs4 import BeautifulSoup
from typing import Optional


def strip_html(html_content: str) -> str:
    """
    Strip HTML tags and return plain text.
    
    Args:
        html_content: HTML string
    
    Returns:
        Plain text with HTML removed
    """
    if not html_content:
        return ""
    
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading/trailing space
        lines = (line.strip() for line in text.splitlines())
        
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    except Exception as e:
        # Fallback: simple regex-based HTML removal
        return re.sub(r'<[^>]+>', '', html_content)


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    Args:
        text: Input text
    
    Returns:
        Text with normalized whitespace
    """
    if not text:
        return ""
    
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with double newline
    text = re.sub(r'\n\n+', '\n\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_plain_text(html_or_text: str) -> str:
    """
    Extract plain text from HTML or text content.
    
    Args:
        html_or_text: HTML or plain text
    
    Returns:
        Clean plain text
    """
    # Check if content contains HTML
    if '<' in html_or_text and '>' in html_or_text:
        text = strip_html(html_or_text)
    else:
        text = html_or_text
    
    return normalize_whitespace(text)


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum character length
    
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."


def extract_email_domain(email: str) -> Optional[str]:
    """
    Extract domain from email address.
    
    Args:
        email: Email address
    
    Returns:
        Domain or None
    """
    if not email or '@' not in email:
        return None
    
    try:
        return email.split('@')[1].lower()
    except IndexError:
        return None


def clean_company_name(company: str) -> str:
    """
    Clean and normalize company name.
    
    Args:
        company: Raw company name
    
    Returns:
        Cleaned company name
    """
    if not company:
        return ""
    
    # Remove common suffixes
    company = re.sub(r'\s+(Inc\.?|LLC|Ltd\.?|Corporation|Corp\.?)$', '', company, flags=re.IGNORECASE)
    
    # Normalize whitespace
    company = normalize_whitespace(company)
    
    # Title case
    company = company.title()
    
    return company.strip()
