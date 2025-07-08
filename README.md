# Time Tracker App (Render-Ready)

This is a lightweight Flask time tracking app using a CSV file as the default
backend. You can optionally set `SUPABASE_URL` and `SUPABASE_KEY` environment
variables to store time entries in a Supabase Postgres table (defaults to
`time_logs`). Charts are rendered client-side with Chart.js. All entries are
written to and read from `time_log.csv` when no database credentials are
provided, so your data persists across restarts.

## Features
- User signup (name & email)
- Time tracking (with from–to time, task, and description)
- Daily log viewer
- Weekly report using Chart.js with day-by-day bars
- Accordion daily log view with inline charts
- Inline editing popup
- CSV download (raw + weekly)
- Sharp Economy branding

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

## Deployment on Render
1. Push to a Git repo
2. Connect to [Render.com](https://render.com/)
3. Choose "Web Service"
4. Select `render.yaml` as setup guide
5. Ensure the Python version is pinned (e.g., `runtime.txt` with `python-3.11.9`)
6. Done ✅

> If you face any issues: increase instance memory, check logs, or email dev@sharpeconomy.org
