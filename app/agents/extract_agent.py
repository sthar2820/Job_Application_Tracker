"""
ExtractAgent: Extracts structured information from job emails.
Pulls company, role, dates, links, req_id, platform, etc.
"""
import re
from datetime import datetime
from typing import Dict, Optional, List
from urllib.parse import urlparse
from dateutil import parser as date_parser

from app.config import JOB_PLATFORMS
from app.utils.text_clean import clean_company_name, extract_email_domain
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ExtractAgent:
    """Agent to extract structured data from job emails."""
    
    def __init__(self):
        self.job_platforms = JOB_PLATFORMS
    
    def run(self, email_data: Dict) -> Dict:
        """
        Extract structured information from email.
        
        Args:
            email_data: Dictionary with 'subject', 'body', 'from', 'snippet'
        
        Returns:
            {
                'company': str,
                'role_title': str,
                'req_id': Optional[str],
                'platform': Optional[str],
                'portal_link': Optional[str],
                'key_dates': List[str],
                'location': Optional[str]
            }
        """
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        from_email = email_data.get('from', '')
        snippet = email_data.get('snippet', '')
        
        # Extract company
        company = self._extract_company(subject, from_email, body)
        
        # Extract role
        role_title = self._extract_role(subject, body, snippet)
        
        # Extract req_id
        req_id = self._extract_req_id(subject, body)
        
        # Extract platform
        platform = self._extract_platform(from_email, body)
        
        # Extract portal link
        portal_link = self._extract_portal_link(body)
        
        # Extract dates
        key_dates = self._extract_dates(body, snippet)
        
        # Extract location
        location = self._extract_location(subject, body)
        
        result = {
            'company': company,
            'role_title': role_title,
            'req_id': req_id,
            'platform': platform,
            'portal_link': portal_link,
            'key_dates': key_dates,
            'location': location
        }
        
        logger.debug(f"Extracted: {company} - {role_title}")
        
        return result
    
    def _extract_company(self, subject: str, from_email: str, body: str) -> str:
        """Extract company name."""
        # Skip subjects that start with "Your Application for" - extract from sender instead
        if re.match(r'^Your\s+Application\s+for', subject, re.IGNORECASE):
            # Jump to sender extraction
            pass
        else:
            # Try from subject patterns - more comprehensive
            patterns = [
                r'(?:thank\s+you\s+for\s+applying\s+(?:to|at)|thank\s+you\s+for\s+your\s+application\s+to|application\s+to)\s+([A-Z][A-Za-z0-9\s&\',.\-]+?)(?:\s*$|!)',
                r'^([A-Z][A-Za-z0-9\s&\',.\-]+?)\s+[-–—]\s+',
                r'^([A-Z][A-Za-z0-9\s&\',.\-]+?):\s+(?!Your|Application)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, subject, re.IGNORECASE)
                if match:
                    company = match.group(1).strip()
                    # Clean up common noise words
                    company = re.sub(r'\s+(Application|Team|Careers|Jobs|Recruiting)$', '', company, flags=re.IGNORECASE)
                    # Skip if starts with common non-company words
                    if re.match(r'^(Your|Application|Thank|Position|Role)\s+', company, re.IGNORECASE):
                        continue
                    if len(company) > 2 and len(company) < 100:
                        return clean_company_name(company)
        
        # Try from body (first 500 chars)
        body_patterns = [
            r'on\s+behalf\s+of\s+([A-Z][A-Za-z0-9\s&\',.-]+?)(?:\.|,|\n)',
            r'position\s+at\s+([A-Z][A-Za-z0-9\s&\',.-]+?)(?:\.|,|\n)',
        ]
        
        for pattern in body_patterns:
            match = re.search(pattern, body[:500], re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) > 2 and len(company) < 100:
                    return clean_company_name(company)
        
        # Try from email sender name
        sender_match = re.search(r'^([^<@]+)', from_email)
        if sender_match:
            sender_name = sender_match.group(1).strip()
            # Remove "via" platforms and quotes
            sender_name = re.sub(r'\s+via\s+.+$', '', sender_name, flags=re.IGNORECASE)
            sender_name = sender_name.replace('"', '').strip()
            
            # Remove common suffixes like "Jobs", "@ icims", "from X", etc.
            sender_name = re.sub(r'\s+Jobs$', '', sender_name, flags=re.IGNORECASE)
            sender_name = re.sub(r'\s+@\s+.*$', '', sender_name)
            sender_name = re.sub(r'^.*?\s+from\s+', '', sender_name, flags=re.IGNORECASE)
            sender_name = re.sub(r'\s+Corporate$', '', sender_name, flags=re.IGNORECASE)
            
            # Skip if it's clearly a system/person name
            if re.search(r'(noreply|no-reply|donotreply|autoreply|system|notification|admin)', sender_name, re.IGNORECASE):
                pass
            elif re.search(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$', sender_name):  # First Last name pattern
                pass
            else:
                # If looks like company name
                if len(sender_name) > 2 and len(sender_name) < 50:
                    return clean_company_name(sender_name)
        
        # Fallback: extract from email domain
        domain = extract_email_domain(from_email)
        if domain:
            # Remove common platform domains
            for platform_domain in self.job_platforms.keys():
                if platform_domain in domain:
                    return "Unknown Company"
            
            # Use domain as company (without TLD)
            company = domain.split('.')[0]
            # Skip generic domains
            if company.lower() not in ['mail', 'email', 'noreply', 'support', 'info']:
                return clean_company_name(company.replace('-', ' ').replace('_', ' '))
        
        return "Unknown Company"
    
    def _extract_role(self, subject: str, body: str, snippet: str) -> str:
        """Extract role/position title."""
        # Try from subject patterns - more comprehensive
        patterns = [
            r'(?:Your\s+[Aa]pplication\s+for)\s+([A-Z][A-Za-z0-9\s,/\-().&]+?)(?:\s*-|\s*$)',
            r'^[^:]+:\s+([A-Z][A-Za-z0-9\s,/\-().&]+?)\s+(?:position|role)(?:\s+update|$)',
            r'(?:position|role|job)(?:\s+as)?:\s+([A-Z][A-Za-z0-9\s,/\-().&]+?)(?:\s+at|update|\n|$)',
            r'^[^:|-]+\s+[-|]\s+([A-Z][A-Za-z0-9\s,/\-().&]+?)$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                role = match.group(1).strip()
                # Clean up common noise
                role = re.sub(r'\s+(application|update|at|position|job|role|confirmation)$', '', role, flags=re.IGNORECASE)
                role = re.sub(r'^(the|a|an)\s+', '', role, flags=re.IGNORECASE)
                
                # Skip generic phrases
                if re.match(r'^(applying|application|confirmation|update|career\s+match)$', role, re.IGNORECASE):
                    continue
                
                # Validate length and content
                if len(role) > 3 and len(role) < 150:
                    # Skip if it's just company name-like or single word
                    if not re.match(r'^[A-Z][a-z]+\s*$', role) and ' ' in role:
                        return role.strip()
        
        # Try from body (more patterns)
        body_patterns = [
            r'(?:applied for|applying for|application for|position of|role of)\s+(?:the\s+)?([A-Z][A-Za-z0-9\s,/\-().&]+?)(?:\s+position|\s+role|\s+at|\.|,|\n)',
            r'(?:position:|role:)\s+([A-Z][A-Za-z0-9\s,/\-().&]+?)(?:\n|\.|$)',
            r'interest\s+in\s+(?:the\s+)?([A-Z][A-Za-z0-9\s,/\-().&]+?)\s+(?:position|role)',
        ]
        
        for pattern in body_patterns:
            match = re.search(pattern, body[:800], re.IGNORECASE)
            if match:
                role = match.group(1).strip()
                role = re.sub(r'\s+(position|role|job)$', '', role, flags=re.IGNORECASE)
                if len(role) > 3 and len(role) < 150:
                    return role.strip()
        
        # Try from snippet
        if snippet:
            for pattern in patterns:
                match = re.search(pattern, snippet, re.IGNORECASE)
                if match:
                    role = match.group(1).strip()
                    if len(role) > 3 and len(role) < 150:
                        return role.strip()
        
        return "Unknown Role"
    
    def _extract_req_id(self, subject: str, body: str) -> Optional[str]:
        """Extract requisition/job ID."""
        patterns = [
            r'(?:requisition|req|job)\s*(?:id|#|number)?:?\s*([A-Z0-9\-]+)',
            r'(?:ID|#)\s*([A-Z0-9\-]{5,})',
        ]
        
        combined = f"{subject} {body[:1000]}"
        
        for pattern in patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_platform(self, from_email: str, body: str) -> Optional[str]:
        """Extract job platform name."""
        domain = extract_email_domain(from_email)
        
        if domain:
            for platform_domain, platform_name in self.job_platforms.items():
                if platform_domain in domain:
                    return platform_name
        
        # Check body for platform mentions
        platform_mentions = ['greenhouse', 'lever', 'workday', 'icims', 'smartrecruiters']
        body_lower = body.lower()
        
        for platform in platform_mentions:
            if platform in body_lower:
                return platform.title()
        
        return None
    
    def _extract_portal_link(self, body: str) -> Optional[str]:
        """Extract application portal link."""
        # Find URLs in body
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, body)
        
        # Filter for job-related URLs
        job_url_keywords = [
            'greenhouse', 'lever', 'workday', 'icims', 'smartrecruiters',
            'jobs', 'careers', 'apply', 'application', 'candidate'
        ]
        
        for url in urls:
            url_lower = url.lower()
            for keyword in job_url_keywords:
                if keyword in url_lower:
                    # Clean URL (remove tracking params)
                    clean_url = re.sub(r'[?&]utm_[^&]*', '', url)
                    return clean_url
        
        # Return first URL if any
        return urls[0] if urls else None
    
    def _extract_dates(self, body: str, snippet: str) -> List[str]:
        """Extract key dates (interview times, deadlines)."""
        dates = []
        
        # Look for date patterns
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',
        ]
        
        combined = f"{snippet} {body[:1000]}"
        
        for pattern in date_patterns:
            matches = re.findall(pattern, combined, re.IGNORECASE)
            for match in matches:
                try:
                    parsed_date = date_parser.parse(match, fuzzy=True)
                    dates.append(parsed_date.isoformat())
                except Exception:
                    pass
        
        return list(set(dates))[:5]  # Limit to 5 unique dates
    
    def _extract_location(self, subject: str, body: str) -> Optional[str]:
        """Extract job location."""
        # Look for location patterns
        patterns = [
            r'(?:location|based in|office in):\s*([A-Z][A-Za-z\s,]+?)(?:\n|\.|\|)',
            r'\b([A-Z][a-z]+,\s+[A-Z]{2})\b',  # City, STATE
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+,\s+[A-Z]{2})\b',  # City Name, STATE
        ]
        
        combined = f"{subject} {body[:500]}"
        
        for pattern in patterns:
            match = re.search(pattern, combined)
            if match:
                location = match.group(1).strip()
                if len(location) < 50:
                    return location
        
        # Check for remote
        if re.search(r'\b(remote|work from home)\b', combined, re.IGNORECASE):
            return "Remote"
        
        return None
