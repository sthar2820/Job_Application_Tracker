# Job Application Tracker - Quick Setup Guide

## 1. Install Dependencies
```bash
pip install -r requirements.txt
```

## 2. Setup Gmail API

### Get Credentials:
1. Visit https://console.cloud.google.com/
2. Create new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download as `credentials.json` → place in project root

## 3. Configure
```bash
cp .env.example .env
```

Edit `.env` if needed (defaults should work).

## 4. Initialize Database
```bash
python -m app.db.init_db
```

## 5. First Run (OAuth Authorization)
```bash
python -m app.poller --once
```

→ Browser opens → Grant Gmail permissions → Token saved

## 6. Start Dashboard
```bash
streamlit run app/dashboard.py
```

## 7. Start Continuous Polling (optional)
```bash
# In separate terminal
python -m app.poller
```

---

## Troubleshooting

### "credentials.json not found"
→ Download OAuth credentials from Google Cloud Console

### "ModuleNotFoundError"
→ Activate virtual environment: `source venv/bin/activate`

### "No applications showing"
→ Run poller first: `python -m app.poller --once`

### "Gmail API quota exceeded"
→ Reduce POLL_INTERVAL_SECONDS in .env (default: 120s)

---

## Quick Commands

| Command | Description |
|---------|-------------|
| `python -m app.poller --once` | Process emails once |
| `python -m app.poller` | Run continuously |
| `streamlit run app/dashboard.py` | Start dashboard |
| `python -m app.tests` | Run tests |
| `python -m app.db.init_db --reset` | Reset database ⚠️ |
