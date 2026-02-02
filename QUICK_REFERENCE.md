# 📋 Quick Reference Card

## Essential Commands

| Command | Purpose |
|---------|---------|
| `python -m app.db.init_db` | Initialize database |
| `python -m app.poller --once` | Process emails once |
| `python -m app.poller` | Run continuously (every 2 min) |
| `streamlit run app/dashboard.py` | Start dashboard |
| `python -m app.tests` | Run all tests |
| `./run.sh` or `run.bat` | Interactive launcher |

## Project Structure (Key Files)

```
app/
├── poller.py              # Main worker (start here)
├── dashboard.py           # Streamlit UI
├── config.py              # Configuration
├── agents/                # 5 processing agents
│   ├── filter_agent.py   # Job-related filter
│   ├── classify_agent.py # Event type
│   ├── extract_agent.py  # Entity extraction
│   ├── resolve_agent.py  # Application matching
│   └── action_agent.py   # Next steps
├── db/
│   ├── init_db.py        # Database setup
│   └── models.py         # CRUD operations
└── utils/
    ├── gmail_client.py   # Gmail API
    ├── text_clean.py     # HTML parsing
    ├── dedupe.py         # Duplicate check
    └── logger.py         # Logging
```

## Agent Pipeline Flow

```
Gmail Email
    ↓
1. FilterAgent → is_job_related?
    ↓ (yes)
2. ClassifyAgent → event_type (confirmation/rejection/interview/etc)
    ↓
3. ExtractAgent → company, role, dates, links
    ↓
4. ResolveAgent → match to application_id
    ↓
5. ActionAgent → next_step suggestion
    ↓
Save to Database
```

## Database Tables

| Table | Purpose |
|-------|---------|
| `applications` | Job application records |
| `events` | Email events per application |
| `emails_processed` | Deduplication tracking |
| `system_state` | Last check timestamp |

## Event Types

- `confirmation` - Application received
- `rejection` - Not selected
- `interview` - Interview invitation
- `assessment` - Coding challenge
- `offer` - Job offer
- `update` - General update
- `other` - Uncategorized

## Application Statuses

- `applied` - Initial application
- `in_review` - Under review
- `assessment` - Doing challenge
- `interview` - Interview scheduled
- `rejected` - Not selected
- `offer` - Offer received
- `other` - Other status

## Configuration (.env)

```bash
GOOGLE_CLIENT_SECRET_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json
GMAIL_USER=me
POLL_INTERVAL_SECONDS=120
DB_PATH=./job_applications.db
LOG_LEVEL=INFO
```

## Supported Job Platforms

- Greenhouse (`greenhouse.io`)
- Lever (`lever.co`)
- Workday (`workday.com`)
- iCIMS (`icims.com`)
- SmartRecruiters (`smartrecruiters.com`)
- Taleo (`taleo.net`)
- SuccessFactors (`successfactors.com`)
- Jobvite (`jobvite.com`)
- Ashby (`ashbyhq.com`)
- JazzHR (`jazz.co`)
- Breezy HR (`breezy.hr`)

## Dashboard Metrics

| Metric | Description |
|--------|-------------|
| Applications (30d) | Total apps last 30 days |
| Active Pipeline | Not rejected/offered |
| Interviews | Scheduled interviews |
| Rejections | Total rejections |
| Response Rate | Events per application |

## Common Issues

| Problem | Solution |
|---------|----------|
| `credentials.json not found` | Download from Google Cloud Console |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| No data in dashboard | Run `python -m app.poller --once` first |
| OAuth browser not opening | Check firewall, use `--once` flag |
| Duplicate emails | Normal - dedupe handled automatically |

## Gmail API Limits

- **Default quota:** 250 quota units/second
- **Daily limit:** 1 billion quota units
- **Per-message:** 5 units
- **Safe polling:** Every 2+ minutes

## Privacy Checklist

- ✅ No full email bodies stored
- ✅ Only metadata + extracted fields
- ✅ Local database (not cloud)
- ✅ Read-only Gmail access
- ✅ Credentials in .gitignore
- ✅ No third-party APIs

## File Locations

| File | Location | Purpose |
|------|----------|---------|
| Database | `./job_applications.db` | SQLite database |
| Credentials | `./credentials.json` | OAuth client |
| Token | `./token.json` | Access token |
| Logs | Console output | Runtime logs |

## Troubleshooting Commands

```bash
# Check database exists
ls -la job_applications.db

# View database schema
sqlite3 job_applications.db ".schema"

# Count applications
sqlite3 job_applications.db "SELECT COUNT(*) FROM applications;"

# Check last poll time
sqlite3 job_applications.db "SELECT value FROM system_state WHERE key='last_checked_iso';"

# Reset everything (⚠️ deletes data)
python -m app.db.init_db --reset
```

## Next Steps After Setup

1. ✅ Run poller once: `python -m app.poller --once`
2. ✅ Check dashboard: `streamlit run app/dashboard.py`
3. ✅ Start continuous polling: `python -m app.poller` (separate terminal)
4. ✅ Monitor logs for errors
5. ✅ Customize filters/keywords in `app/config.py` if needed

## Getting Help

- 📖 Read `README.md` for detailed guide
- 🔧 Read `SETUP.md` for setup steps
- 📧 Read `GMAIL_SETUP.md` for Gmail API help
- 🧪 Run tests: `python -m app.tests`
- 📝 Check `CHANGELOG.md` for version info

---

**Version:** 1.0.0  
**Status:** Production Ready  
**Last Updated:** 2026-02-02
