# Time Tracker App (Render-Ready)

This is a lightweight Flask time tracking app that stores entries in
Firebase Firestore using `firebase-admin`. Column names may use spaces
(e.g. `"From Time"`) or snake case (e.g. `from_time`)—the app converts them
automatically. Charts are rendered client-side with Chart.js.

## Features
- User signup (name & email)
- Time tracking (with from–to time, task, and description)
- Daily log viewer
- Weekly report using Chart.js with day-by-day bars
- Accordion daily log view with inline charts
- Inline editing popup
- CSV download (raw + weekly)
- CSV upload to bulk import entries
- Sharp Economy branding
- Stores data in Firebase Firestore

## File Structure
```
.
├── app.py
├── render.yaml
├── requirements.txt
├── static/
│   ├── style.css
│   └── logo.png
└── templates/
    ├── index.html
    └── report.html
```

Copy `.env.sample` to `.env` and fill in `FIREBASE_CERT` (the service account JSON) and `FLASK_SECRET_KEY` before running the app. The Firestore collection will be created automatically on first run.

### Required Firebase credentials
Create a Firebase project and generate a service account key for Firestore access. Paste the JSON for that key into the `FIREBASE_CERT` environment variable on Render. No other credentials are required.

## Deployment on Render
1. Push to a Git repo
2. Connect to [Render.com](https://render.com/)
3. Choose "Web Service"
4. Select `render.yaml` as setup guide
5. Ensure the Python version is pinned (e.g., `runtime.txt` with `python-3.11.9`)
6. Done ✅

### Automatic deployment from GitHub
Create a Deploy Hook in Render for your web service and add the hook URL as a
`RENDER_DEPLOY_HOOK_URL` secret in your GitHub repository. The included
GitHub Actions workflow triggers this hook whenever a commit is pushed to the
`main` branch.

> If you face any issues: increase instance memory, check logs, or email dev@sharpeconomy.org
