# Time Tracker App (Render-Ready)

This is a lightweight Flask time tracking app that stores entries in a Supabase
table. Column names may use spaces (e.g. `"From Time"`) or snake case
(e.g. `from_time`)—the app will convert automatically. Charts are rendered
client-side with Chart.js.

## Features
- User signup (name & email)
- Time tracking (with from–to time, task, and description)
- Daily log viewer
- Weekly report using Chart.js with day-by-day bars
- Accordion daily log view with inline charts
- Inline editing popup
- CSV download (raw + weekly)
- Sharp Economy branding
- Simple, CSV-only storage without a "Completed" column

## File Structure
```
.
├── app.py
├── render.yaml
├── requirements.txt
├── time_log.csv
├── static/
│   ├── style.css
│   └── logo.png
└── templates/
    ├── index.html
    └── report.html
```

Copy `.env.sample` to `.env` and fill in `SUPABASE_DB_URL` and `FLASK_SECRET_KEY` before running the app. Run `python migrate_to_supabase.py` once to create the database table and import the sample CSV.

## Deployment on Render
1. Push to a Git repo
2. Connect to [Render.com](https://render.com/)
3. Choose "Web Service"
4. Select `render.yaml` as setup guide
5. Ensure the Python version is pinned (e.g., `runtime.txt` with `python-3.11.9`)
6. Done ✅

> If you face any issues: increase instance memory, check logs, or email dev@sharpeconomy.org
