import csv
import os
from datetime import datetime
from collections import defaultdict
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify

app = Flask(__name__)
app.secret_key = 'secret123'
CSV_FILE = 'time_log.csv'

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'Email', 'Date', 'From Time', 'To Time', 'Task', 'Description'])

def _read_entries():
    entries = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                entries.append(row)
    return entries

def _hours(from_t, to_t):
    fmt = '%H:%M'
    return (datetime.strptime(to_t, fmt) - datetime.strptime(from_t, fmt)).seconds / 3600

def _daily_summary(entries):
    summary = defaultdict(float)
    for row in entries:
        key = (row['Name'], row['Date'])
        summary[key] += _hours(row['From Time'], row['To Time'])
    return [{'Name': k[0], 'Date': k[1], 'Hours': v} for k, v in summary.items()]

def _weekly_summary(entries):
    weekly = defaultdict(lambda: defaultdict(float))
    for row in entries:
        dt = datetime.strptime(row['Date'], '%Y-%m-%d')
        week = f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"
        weekly[week][row['Name']] += _hours(row['From Time'], row['To Time'])
    return weekly

@app.route('/')
def index():
    data = _daily_summary(_read_entries())
    return render_template('index.html', data=data)

@app.route('/add', methods=['POST'])
def add():
    row = [
        request.form['name'], request.form['email'], request.form['date'],
        request.form['from_time'], request.form['to_time'],
        request.form['task'], request.form['description']
    ]
    with open(CSV_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(row)
    flash('Time entry added successfully')
    return redirect(url_for('index'))

@app.route('/report')
def report():
    return render_template('report.html')

@app.route('/weekly-data')
def weekly_data():
    weekly = _weekly_summary(_read_entries())
    weeks = sorted(weekly.keys())
    names = sorted({name for w in weekly.values() for name in w.keys()})
    hours = {name: [weekly[w].get(name, 0) for w in weeks] for name in names}
    return jsonify({'weeks': weeks, 'names': names, 'hours': hours})

@app.route('/download')
def download():
    return send_file(CSV_FILE, as_attachment=True)

@app.route('/weekly-download')
def weekly_download():
    weekly = _weekly_summary(_read_entries())
    weeks = sorted(weekly.keys())
    names = sorted({name for w in weekly.values() for name in w.keys()})
    file = 'weekly_report.csv'
    with open(file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Week'] + names)
        for week in weeks:
            writer.writerow([week] + [weekly[week].get(name, 0) for name in names])
    return send_file(file, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
