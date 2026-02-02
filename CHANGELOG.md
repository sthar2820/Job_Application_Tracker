# Changelog

## Version 1.0.0 (2026-02-02)

### Initial Release

#### Core Features
- ✅ Automated Gmail polling every 2 minutes
- ✅ 5-agent pipeline for email processing
  - FilterAgent: Job-related email detection
  - ClassifyAgent: Event type classification (7 types)
  - ExtractAgent: Entity extraction (company, role, dates, links, etc.)
  - ResolveAgent: Fuzzy matching to existing applications
  - ActionAgent: Next-step recommendations
- ✅ SQLite database with 4 tables
- ✅ Streamlit dashboard with KPIs and visualizations
- ✅ Privacy-focused (no full email storage)
- ✅ Comprehensive test suite

#### Supported Platforms
- Greenhouse
- Lever
- Workday
- iCIMS
- SmartRecruiters
- Taleo
- SuccessFactors
- Jobvite
- Ashby
- JazzHR
- Breezy HR

#### Event Types
- Confirmation (application received)
- Rejection
- Interview invitation
- Assessment/coding challenge
- Offer
- Generic update

#### Dashboard Features
- KPI metrics (applications, pipeline, interviews, rejections, response rate)
- Applications over time chart
- Status distribution chart
- Application funnel
- Recent events table (sortable, filterable)
- All applications table
- Auto-refresh option

#### Technical Stack
- Python 3.8+
- Gmail API (OAuth 2.0)
- SQLite database
- Streamlit (dashboard)
- Plotly (visualizations)
- BeautifulSoup (HTML parsing)
- FuzzyWuzzy (string matching)

#### Known Limitations
- Email parsing accuracy depends on sender format
- No OCR for PDF attachments
- Manual Gmail API setup required
- Gmail API rate limits apply

---

## Planned for Version 2.0

### LLM Integration
- OpenAI/Claude API for better extraction
- Handle non-standard email formats
- Sentiment analysis

### Advanced Features
- Desktop notifications
- Google Calendar integration
- Email quick-reply templates
- Analytics dashboards (time-to-response, platform analysis)

### Multi-User Support
- Web hosting with authentication
- Team dashboards
- Export to CSV/Excel

---

## Contributing

Found a bug? Have a feature request? Open an issue on GitHub!
