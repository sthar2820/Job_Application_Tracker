"""
ResolveAgent: Matches emails to existing application records.
Uses req_id, portal_link, and company/role similarity matching.
"""
from typing import Dict, Optional
from fuzzywuzzy import fuzz

from app.db.models import (
    find_applications_by_company_role,
    find_applications_by_portal_link,
    create_application
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ResolveAgent:
    """Agent to resolve emails to application records."""
    
    def __init__(self, similarity_threshold: int = 80):
        """
        Initialize ResolveAgent.
        
        Args:
            similarity_threshold: Minimum fuzzy match score (0-100) for company/role matching
        """
        self.similarity_threshold = similarity_threshold
    
    def run(self, extracted_data: Dict) -> Dict:
        """
        Resolve email to an application record.
        
        Args:
            extracted_data: Output from ExtractAgent with company, role_title, etc.
        
        Returns:
            {
                'application_id': int,
                'is_new': bool,
                'match_method': str
            }
        """
        company = extracted_data.get('company', 'Unknown Company')
        role_title = extracted_data.get('role_title', 'Unknown Role')
        portal_link = extracted_data.get('portal_link')
        req_id = extracted_data.get('req_id')
        platform = extracted_data.get('platform')
        
        # Strategy 1: Match by portal_link
        if portal_link:
            matches = find_applications_by_portal_link(portal_link)
            if matches:
                app_id = matches[0]['application_id']
                logger.info(f"Matched to application {app_id} via portal_link")
                return {
                    'application_id': app_id,
                    'is_new': False,
                    'match_method': 'portal_link'
                }
        
        # Strategy 2: Match by company + role (fuzzy)
        matches = find_applications_by_company_role(company, role_title)
        
        if matches:
            # Check similarity
            best_match = None
            best_score = 0
            
            for match in matches:
                # Calculate similarity
                company_score = fuzz.ratio(
                    company.lower(),
                    match['company'].lower()
                )
                role_score = fuzz.ratio(
                    role_title.lower(),
                    match['role_title'].lower()
                )
                
                # Combined score
                combined_score = (company_score + role_score) / 2
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_match = match
            
            # If good match found
            if best_score >= self.similarity_threshold:
                app_id = best_match['application_id']
                logger.info(f"Matched to application {app_id} via fuzzy matching (score: {best_score:.1f})")
                return {
                    'application_id': app_id,
                    'is_new': False,
                    'match_method': f'fuzzy_match_{best_score:.0f}'
                }
        
        # Strategy 3: Create new application
        logger.info(f"Creating new application: {company} - {role_title}")
        
        app_id = create_application(
            company=company,
            role_title=role_title,
            platform=platform,
            portal_link=portal_link,
            status='applied'
        )
        
        return {
            'application_id': app_id,
            'is_new': True,
            'match_method': 'created_new'
        }
