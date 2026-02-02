# Gmail API Setup - Detailed Guide

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Enter project name: `Job Application Tracker`
4. Click **Create**

## Step 2: Enable Gmail API

1. In the Google Cloud Console, navigate to **APIs & Services** → **Library**
2. Search for "Gmail API"
3. Click on **Gmail API**
4. Click **Enable**

## Step 3: Configure OAuth Consent Screen

1. Navigate to **APIs & Services** → **OAuth consent screen**
2. Select **External** (unless you have Google Workspace)
3. Click **Create**

### Fill in App Information:
- **App name:** Job Application Tracker
- **User support email:** Your email
- **Developer contact information:** Your email
- Click **Save and Continue**

### Scopes:
- Click **Add or Remove Scopes**
- Search for: `https://www.googleapis.com/auth/gmail.readonly`
- Check the box
- Click **Update** → **Save and Continue**

### Test Users (for development):
- Click **Add Users**
- Add your Gmail address
- Click **Save and Continue**

## Step 4: Create OAuth Credentials

1. Navigate to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: `Job Application Tracker Desktop`
5. Click **Create**

## Step 5: Download Credentials

1. In the credentials list, find your newly created OAuth client
2. Click the **Download** icon (⬇️)
3. Save the file as `credentials.json`
4. Move `credentials.json` to your project root directory

```bash
mv ~/Downloads/client_secret_*.json /path/to/Job_Application_Tracker/credentials.json
```

## Step 6: First Run (Authorization)

```bash
python -m app.poller --once
```

This will:
1. Open your browser
2. Ask you to sign in to Google
3. Show permission request for Gmail read access
4. Ask you to allow access
5. Save the token to `token.json`

**Note:** You only need to do this once. The `token.json` file will be used for future runs.

## Troubleshooting

### "Access blocked: This app's request is invalid"
→ Make sure you added your email to Test Users in OAuth consent screen

### "Invalid grant" error
→ Delete `token.json` and run authorization again

### "The user does not have sufficient permissions"
→ Check that Gmail API is enabled

### "Quota exceeded"
→ You've hit Gmail API rate limits. Wait or reduce POLL_INTERVAL_SECONDS

## Security Notes

- ✅ `credentials.json` contains your OAuth client ID (low risk)
- ⚠️ `token.json` contains access tokens (keep private!)
- ✅ Both are in `.gitignore` (won't be committed to Git)
- ✅ App only requests read-only access to Gmail
- ✅ You can revoke access anytime at https://myaccount.google.com/permissions

## Scopes Explained

Our app uses: `https://www.googleapis.com/auth/gmail.readonly`

This allows:
- ✅ Read emails
- ✅ Search emails
- ✅ Get email metadata

This does NOT allow:
- ❌ Send emails
- ❌ Delete emails
- ❌ Modify emails
- ❌ Access Google Drive, Calendar, etc.
