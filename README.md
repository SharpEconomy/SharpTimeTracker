# Time Tracker App (Render-Ready)

This is a lightweight Flask time tracking app that stores entries in
Firebase Firestore using `firebase-admin`. Column names may use spaces
or snake case—the app converts them automatically. Charts are rendered
client-side with Chart.js.

## Features
- User signup (name & email)
- Time tracking (with duration, task, and description)
- Daily log viewer
- Weekly report using Chart.js with day-by-day bars
- Accordion daily log view with inline charts
- Inline editing popup
- Excel download (raw + weekly)
- Upload CSV or Excel to bulk import entries. The spreadsheet format uses the columns:
  `Name, Date, Duration, Task, Description, File`.
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

Create two Secret Files in Render:

1. `sharptimetracker-firebase-adminsdk-fbsvc-973348138e.json` – your Firebase service account JSON
2. `flask_secret_key` – a random string for Flask sessions

These files are mounted at `/etc/secrets/` when the service starts and the app reads them automatically. No `.env` file is required.

### Required Firebase credentials
Create a Firebase project and generate a service account key for Firestore access. Upload the JSON file to Render as the secret file `sharptimetracker-firebase-adminsdk-fbsvc-973348138e.json`. The app reads this file from `/etc/secrets` when it starts. No environment variables are required.

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
`render-deploy.yml` workflow installs dependencies, checks that `app.py`
compiles, and then triggers this hook whenever a commit is pushed to the
`main` branch or the workflow is run manually. Ensure the secret is set,
otherwise the workflow will fail.

> If you face any issues: increase instance memory, check logs, or email dev@sharpeconomy.org
