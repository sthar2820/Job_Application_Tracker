"""
FilterAgent: Determines if an email is job-related or noise.
Uses keyword matching and domain heuristics.
"""
import re
from typing import Dict
from app.config import JOB_KEYWORDS, JOB_PLATFORMS
from app.utils.text_clean import extract_email_domain
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class FilterAgent:
    """Agent to filter job-related emails from noise."""
    
    def __init__(self):
        self.job_keywords = JOB_KEYWORDS
        self.job_platforms = JOB_PLATFORMS
    
    def run(self, email_data: Dict) -> Dict:
        """
        Determine if email is job-related.
        
        Args:
            email_data: Dictionary with 'subject', 'from', 'body', 'snippet'
        
        Returns:
            {
                'is_job_related': bool,
                'reason': str,
                'confidence': float
            }
        """
        subject = email_data.get('subject', '').lower()
        from_email = email_data.get('from', '').lower()
        body = email_data.get('body', '').lower()
        snippet = email_data.get('snippet', '').lower()
        
        # Combined text for analysis
        combined_text = f"{subject} {snippet} {body[:500]}"
        
        # Check sender domain
        domain = extract_email_domain(from_email)
        domain_score = self._check_domain(domain)
        
        # Check keywords
        keyword_score = self._check_keywords(combined_text)
        
        # Determine if job-related
        is_job_related = domain_score > 0 or keyword_score >= 2
        confidence = min(1.0, (domain_score * 0.6 + keyword_score * 0.1))
        
        # Determine reason
        reasons = []
        if domain_score > 0:
            reasons.append(f"known job platform domain ({domain})")
        if keyword_score > 0:
            reasons.append(f"{keyword_score} job keywords found")
        
        reason = "; ".join(reasons) if reasons else "no job indicators found"
        
        logger.debug(f"Filter result for '{subject[:50]}...': {is_job_related} ({reason})")
        
        return {
            'is_job_related': is_job_related,
            'reason': reason,
            'confidence': confidence
        }
    
    def _check_domain(self, domain: str) -> float:
        """
        Check if sender domain is a known job platform.
        
        Returns:
            Score (0-1)
        """
        if not domain:
            return 0.0
        
        # Exact match
        for platform_domain in self.job_platforms.keys():
            if platform_domain in domain:
                return 1.0
        
        # Common job-related domains
        job_domains = [
            'greenhouse', 'lever', 'workday', 'icims', 'smartrecruiters',
            'taleo', 'successfactors', 'jobvite', 'ashby', 'jazz',
            'breezy', 'applytojob', 'myworkday', 'recruiting'
        ]
        
        for job_domain in job_domains:
            if job_domain in domain:
                return 0.8
        
        return 0.0
    
    def _check_keywords(self, text: str) -> int:
        """
        Count job-related keywords in text.
        
        Returns:
            Count of keywords found
        """
        count = 0
        
        for keyword in self.job_keywords:
            if keyword.lower() in text:
                count += 1
        
        # Additional patterns
        patterns = [
            r'application\s+(to|for|at)',
            r'thank\s+you\s+for\s+(applying|your\s+application)',
            r'interview\s+(invitation|scheduled|request)',
            r'coding\s+(challenge|assessment|test)',
            r'technical\s+(interview|assessment|challenge)',
            r'position\s+at',
            r'role\s+at',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                count += 1
        
        return count
