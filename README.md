# Time Tracker App (Render-Ready)

This is a simple Flask + Dash time tracking app using CSV as backend.

## Features
- User signup (name & email)
- Time tracking (with from–to time, task, and description)
- Daily log viewer
- Weekly report in charts (Dash)
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
5. Done ✅

> If you face any issues: increase instance memory, check logs, or email dev@sharpeconomy.org
