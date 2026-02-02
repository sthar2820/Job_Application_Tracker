# 💼 Job Application Tracker

An intelligent, privacy-focused system that automatically tracks your job applications by monitoring your Gmail inbox, extracting structured information, and presenting insights through a live dashboard.

## 🎯 Problem Statement

Job hunting involves managing dozens or hundreds of applications across multiple platforms. Keeping track of application statuses, interview schedules, and follow-ups becomes overwhelming. This tool automates the entire tracking process by:

- **Monitoring** your Gmail inbox for job-related emails
- **Extracting** structured information (company, role, dates, links)
- **Classifying** events (confirmations, interviews, rejections, offers)
- **Storing** everything in a local database
- **Visualizing** your job search pipeline with actionable insights

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Gmail Inbox                           │
│           (Job confirmations, interviews, etc.)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Polling Worker (app/poller.py)             │
│                   Runs every 2 minutes                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Pipeline                            │
│                                                              │
│  1. FilterAgent    → Is this job-related?                   │
│  2. ClassifyAgent  → What type of event?                    │
│  3. ExtractAgent   → Pull company, role, dates, links       │
│  4. ResolveAgent   → Match to existing application          │
│  5. ActionAgent    → Suggest next steps                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                SQLite Database (job_applications.db)         │
│                                                              │
│  • applications  → Your job applications                    │
│  • events        → Email events per application             │
│  • emails_processed → Deduplication tracking                │
│  • system_state  → Last check timestamp                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Streamlit Dashboard (app/dashboard.py)          │
│                                                              │
│  • KPIs: Applications, pipeline, interviews, rejections     │
│  • Charts: Timeline, status distribution, funnel            │
│  • Tables: Recent events, all applications                  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Gmail account
- Google Cloud project with Gmail API enabled

### 1. Clone and Setup

```bash
cd Job_Application_Tracker
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable the **Gmail API**
4. Create OAuth 2.0 credentials (Desktop application)
5. Download the credentials as `credentials.json`
6. Place `credentials.json` in the project root

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Initialize Database

```bash
python -m app.db.init_db
```

### 5. Run Initial Poll (First-time OAuth)

```bash
python -m app.poller --once
```

This will open a browser for Gmail OAuth authorization. Grant permissions, and the token will be saved for future use.

### 6. Start the Dashboard

```bash
streamlit run app/dashboard.py
```

### 7. Start Continuous Polling (Optional)

In a separate terminal:

```bash
python -m app.poller
```

This will check for new emails every 2 minutes.

## 📊 Database Schema

### `applications`
Stores your job applications.

| Column | Type | Description |
|--------|------|-------------|
| application_id | INTEGER | Primary key |
| company | TEXT | Company name |
| role_title | TEXT | Job title |
| platform | TEXT | Job platform (Greenhouse, Lever, etc.) |
| source | TEXT | Application source (LinkedIn, Indeed, etc.) |
| applied_date | DATETIME | When you applied |
| first_seen_date | DATETIME | When we first saw this application |
| status | TEXT | Current status (applied, interview, rejected, etc.) |
| last_updated | DATETIME | Last modification time |
| portal_link | TEXT | Application portal URL |
| notes | TEXT | Optional notes |

### `events`
Tracks email events for each application.

| Column | Type | Description |
|--------|------|-------------|
| event_id | INTEGER | Primary key |
| application_id | INTEGER | Foreign key to applications |
| event_type | TEXT | confirmation, rejection, interview, assessment, offer, update |
| event_time | DATETIME | When the event occurred |
| email_message_id | TEXT | Gmail message ID |
| subject | TEXT | Email subject |
| from_email | TEXT | Sender email |
| confidence | REAL | Classification confidence (0-1) |
| extracted_json | TEXT | Extracted data as JSON |
| action_suggestion | TEXT | Suggested next step |

### `emails_processed`
Prevents duplicate processing.

| Column | Type | Description |
|--------|------|-------------|
| email_message_id | TEXT | Gmail message ID (primary key) |
| thread_id | TEXT | Gmail thread ID |
| received_at | DATETIME | When email was received |
| from_domain | TEXT | Sender domain |
| subject | TEXT | Email subject |
| classification | TEXT | How it was classified |
| processed_at | DATETIME | When we processed it |

### `system_state`
System configuration and state.

| Column | Type | Description |
|--------|------|-------------|
| key | TEXT | State key (primary key) |
| value | TEXT | State value |

## 🤖 How It Works

### Polling Worker

The `app/poller.py` worker runs every 2 minutes (configurable) and:

1. Reads the last checked timestamp from the database
2. Queries Gmail for new emails from job platforms
3. Filters out already-processed messages
4. Runs each new email through the agent pipeline
5. Updates the database with extracted information
6. Updates the last checked timestamp

### Agent Pipeline

#### 1. **FilterAgent** (`app/agents/filter_agent.py`)
- **Input:** Raw email (subject, from, body, snippet)
- **Output:** `is_job_related`, `reason`, `confidence`
- **Logic:** Checks sender domain (greenhouse.io, lever.co, etc.) and keywords ("application", "interview", "coding challenge", etc.)

#### 2. **ClassifyAgent** (`app/agents/classify_agent.py`)
- **Input:** Email data
- **Output:** `event_type`, `status_update`, `confidence`
- **Types:** confirmation, rejection, interview, assessment, offer, update
- **Logic:** Pattern matching on subject and body text with priority ordering (rejection > offer > interview > assessment > confirmation)

#### 3. **ExtractAgent** (`app/agents/extract_agent.py`)
- **Input:** Email data
- **Output:** `company`, `role_title`, `req_id`, `platform`, `portal_link`, `key_dates`, `location`
- **Logic:** Regex patterns + heuristics to extract structured fields from unstructured email text

#### 4. **ResolveAgent** (`app/agents/resolve_agent.py`)
- **Input:** Extracted data
- **Output:** `application_id`, `is_new`, `match_method`
- **Logic:** Matches to existing applications by:
  1. Portal link (exact match)
  2. Company + role fuzzy matching (80% threshold)
  3. Creates new application if no match

#### 5. **ActionAgent** (`app/agents/action_agent.py`)
- **Input:** Event type + extracted data
- **Output:** `action_suggestion`, `follow_up_date`
- **Logic:** Provides contextual next steps based on event type

## 🎨 Dashboard Features

### Key Metrics
- **Applications (30d):** Total applications in the last 30 days
- **Active Pipeline:** Applications in progress (not rejected/offer)
- **Interviews:** Number of scheduled interviews
- **Rejections:** Total rejections
- **Response Rate:** Percentage of applications with non-confirmation responses

### Visualizations
- **Applications Over Time:** Line chart showing application trends
- **Status Distribution:** Bar chart of current statuses
- **Application Funnel:** Conversion funnel from applied → offer

### Data Tables
- **Recent Events:** Chronological list of all email events with actions
- **All Applications:** Complete application list with status and dates

## 🔒 Privacy & Security

- ✅ **No full email bodies stored** – Only metadata and extracted fields
- ✅ **Local database** – Data stays on your machine (SQLite)
- ✅ **Read-only Gmail access** – OAuth with minimal scopes
- ✅ **No external APIs** – No data sent to third parties
- ✅ **Token security** – Gmail tokens stored in `.gitignore`d files

## 🛠️ CLI Commands

### Initialize Database
```bash
python -m app.db.init_db
```

### Reset Database (⚠️ Deletes all data)
```bash
python -m app.db.init_db --reset
```

### Run Poller Once
```bash
python -m app.poller --once
```

### Run Poller Continuously
```bash
python -m app.poller
```

### Start Dashboard
```bash
streamlit run app/dashboard.py
```

### Run Tests
```bash
python -m app.tests
```

Or with pytest:
```bash
pytest app/tests/
```

## 📁 Project Structure

```
job-application-tracker/
├── app/
│   ├── dashboard.py           # Streamlit UI
│   ├── poller.py              # Polling worker
│   ├── config.py              # Configuration & env loading
│   ├── agents/
│   │   ├── filter_agent.py    # Job-related filter
│   │   ├── classify_agent.py  # Event type classification
│   │   ├── extract_agent.py   # Entity extraction
│   │   ├── resolve_agent.py   # Application matching
│   │   └── action_agent.py    # Next step suggestions
│   ├── db/
│   │   ├── init_db.py         # Database creation
│   │   └── models.py          # Query helpers
│   ├── utils/
│   │   ├── gmail_client.py    # Gmail API wrapper
│   │   ├── text_clean.py      # HTML stripping, normalization
│   │   ├── dedupe.py          # Deduplication logic
│   │   └── logger.py          # Logging setup
│   └── tests/
│       ├── __init__.py        # Test runner
│       ├── test_extract.py    # ExtractAgent tests
│       └── test_classify.py   # ClassifyAgent tests
├── data/
│   └── sample_emails/         # (Optional) Anonymized samples
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
└── requirements.txt           # Python dependencies
```

## ⚙️ Configuration

Edit `.env` to customize:

```bash
# Gmail API
GOOGLE_CLIENT_SECRET_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json
GMAIL_USER=me

# Polling interval (seconds)
POLL_INTERVAL_SECONDS=120

# Database path
DB_PATH=./job_applications.db

# Logging level
LOG_LEVEL=INFO
```

## 🧪 Testing

The project includes tests for core agent functionality:

```bash
python -m app.tests
```

Tests use anonymized sample data and validate:
- Company and role extraction
- Event type classification (rejection, interview, offer, etc.)
- Portal link and requisition ID extraction
- Platform detection

## ⚠️ Limitations

- **Email parsing is imperfect:** Some companies use non-standard formats
- **No OCR:** Attachments (PDFs, images) are not processed
- **Some applications don't send confirmations:** May miss silent applications
- **Gmail rate limits:** Polling too frequently may hit API limits
- **Manual applications:** Applications you track elsewhere won't appear

## 🚧 Next Steps / Future Enhancements

### Phase 2: LLM-Powered Extraction
- Integrate OpenAI/Claude for better entity extraction
- Handle complex/non-standard email formats
- Sentiment analysis for email tone

### Phase 3: Advanced Features
- **Push notifications:** Desktop/email alerts for interviews/rejections
- **Calendar integration:** Auto-add interviews to Google Calendar
- **Email templates:** Quick reply templates for follow-ups
- **Analytics:** Time-to-response, best application times, platform analysis

### Phase 4: Multi-User & Cloud
- Web-hosted version with authentication
- Multi-user support
- Email sync across devices
- Export to CSV/Excel

## 🤝 Contributing

This is a personal portfolio project, but suggestions are welcome! Areas for improvement:

- Better extraction patterns for specific platforms
- Additional job platforms (LinkedIn, Indeed, etc.)
- UI/UX improvements for dashboard
- Performance optimizations

## 📝 License

MIT License - Feel free to use for personal projects.

## 🙏 Acknowledgments

- Built with Python, Streamlit, and the Gmail API
- Inspired by the frustration of manually tracking 100+ job applications
- Designed as a production-grade analytics pipeline demo

---

**Built by:** [Your Name]  
**Contact:** [Your Email]  
**Portfolio:** [Your Website]

---

## 📸 Screenshots

### Dashboard KPIs
*(Placeholder: Add screenshot of KPI metrics)*

### Status Distribution
*(Placeholder: Add screenshot of status bar chart)*

### Recent Events Table
*(Placeholder: Add screenshot of events table)*

---

**⭐ If this helped your job search, consider starring the repo!**
