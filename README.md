# Time Tracker App (Render-Ready)

This is a lightweight Flask time tracking app using a CSV file as the backend.
Dash and pandas have been removed so installs on Render are much faster. Charts
are now rendered client-side with Chart.js. All entries are written to and read
from `time_log.csv`, so your data persists across restarts.

## Features
- User signup (name & email)
- Time tracking (with from–to time, task, and description)
- Daily log viewer
- Weekly report using Chart.js
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
