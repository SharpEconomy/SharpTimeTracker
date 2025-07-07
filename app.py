import csv
import os
import re
import time
from datetime import datetime, timedelta
from collections import defaultdict
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    jsonify,
    send_from_directory,
    abort,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secret123'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, 'time_log.csv')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            'Name',
            'Date',
            'From Time',
            'To Time',
            'Task',
            'Description',
            'File',
            'Completed',
            'Created At',
        ])

def _read_entries():
    entries = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # handle files created with older headers
                if 'File' not in row:
                    row['File'] = ''
                if 'Description' not in row:
                    row['Description'] = ''
                if 'Completed' not in row:
                    row['Completed'] = '1'
                if 'Created At' not in row:
                    row['Created At'] = datetime.now().isoformat()
                entries.append(row)
    return entries

def _hours(from_t, to_t):
    fmt = '%H:%M'
    return (datetime.strptime(to_t, fmt) - datetime.strptime(from_t, fmt)).seconds / 3600

def _format_date(date_str, show_year=False):
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    return dt.strftime('%m/%d/%Y' if show_year else '%m/%d')

@app.template_filter('linkify')
def _linkify(text):
    url_pattern = r'(https?://[\w\.-/]+)'
    return re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)

def _weekly_summary(entries):
    weekly = defaultdict(lambda: defaultdict(float))
    for row in entries:
        dt = datetime.strptime(row['Date'], '%Y-%m-%d')
        week_start = dt - timedelta(days=dt.weekday())
        key = week_start.strftime('%Y-%m-%d')
        weekly[key][row['Name']] += _hours(row['From Time'], row['To Time'])
    return weekly

def _daily_summary(entries):
    daily = defaultdict(lambda: defaultdict(float))
    for row in entries:
        daily[row['Date']][row['Name']] += _hours(row['From Time'], row['To Time'])
    return daily


@app.route('/')
def index():
    entries = _read_entries()
    years = {datetime.strptime(e['Date'], '%Y-%m-%d').year for e in entries}
    show_year = any(year != 2025 for year in years)
    for i, e in enumerate(entries):
        e['index'] = i
        e['hours'] = _hours(e['From Time'], e['To Time'])
        hrs = int(e['hours'])
        mins = int(round((e['hours'] - hrs) * 60))
        e['duration_str'] = f"{hrs}h {mins}m"
        e['date_display'] = _format_date(e['Date'], show_year)
    return render_template('index.html', data=entries, show_year=show_year)

@app.route('/add', methods=['POST'])
def add():
    today = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    uploaded = request.files.get('file')
    filename = ''
    if uploaded and uploaded.filename:
        safe = secure_filename(uploaded.filename)
        fname = f"{int(time.time())}_{safe}"
        path = os.path.join(UPLOAD_FOLDER, fname)
        uploaded.save(path)
        filename = fname
    entries = _read_entries()
    index = len(entries)
    row = [
        request.form['name'],
        today,
        request.form['from_time'],
        request.form['to_time'],
        request.form['task'],
        request.form.get('description', ''),
        filename,
        request.form.get('completed', '1'),
        datetime.now().isoformat(),
    ]
    with open(CSV_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(row)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        hours = _hours(row[2], row[3])
        years = {datetime.strptime(r['Date'], '%Y-%m-%d').year for r in _read_entries()}
        show_year = any(y != 2025 for y in years)
        return jsonify(
            {
                'name': row[0],
                'date_display': _format_date(row[1], show_year),
                'hours': hours,
                'duration_str': f"{int(hours)}h {int(round((hours-int(hours))*60))}m",
                'task': row[4],
                'description_html': _linkify(row[5]),
                'file_link': f'<a href="/uploads/{filename}" download target="_blank">{filename}</a>' if filename else '',
                'completed': row[7],
                'index': index,
            }
        )

    flash('Time entry added successfully')
    return redirect(url_for('index'))

@app.route('/report')
def report():
    return render_template('report.html')

@app.route('/weekly-data')
def weekly_data():
    weekly = _weekly_summary(_read_entries())
    weeks = sorted(weekly.keys())
    years = {datetime.strptime(w, '%Y-%m-%d').year for w in weeks}
    show_year = any(y != 2025 for y in years)
    labels = [_format_date(w, show_year) for w in weeks]
    names = sorted({name for w in weekly.values() for name in w.keys()})
    hours = {name: [weekly[w].get(name, 0) for w in weeks] for name in names}
    return jsonify({'weeks': labels, 'names': names, 'hours': hours})

@app.route('/daily-data')
def daily_data():
    daily = _daily_summary(_read_entries())
    dates = sorted(daily.keys())
    names = sorted({n for d in daily.values() for n in d.keys()})
    hours = {name: [daily[date].get(name, 0) for date in dates] for name in names}
    return jsonify({'dates': dates, 'names': names, 'hours': hours})

@app.route('/download')
def download():
    entries = _read_entries()
    file = 'entries.csv'
    with open(file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Date',
            'From Time',
            'To Time',
            'Hours',
            'Task',
            'Description',
            'File',
        ])
        for e in entries:
            writer.writerow([
                e['Date'],
                e['From Time'],
                e['To Time'],
                round(_hours(e['From Time'], e['To Time']), 2),
                e['Task'],
                e['Description'],
                e['File'],
            ])
    return send_file(file, as_attachment=True, download_name='Sharp Time Tracker.csv')

@app.route('/weekly-download')
def weekly_download():
    weekly = _weekly_summary(_read_entries())
    weeks = sorted(weekly.keys())
    years = {datetime.strptime(w, '%Y-%m-%d').year for w in weeks}
    show_year = any(y != 2025 for y in years)
    labels = [_format_date(w, show_year) for w in weeks]
    names = sorted({name for w in weekly.values() for name in w.keys()})
    file = 'weekly_report.csv'
    with open(file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Week'] + names)
        for week, label in zip(weeks, labels):
            writer.writerow([label] + [weekly[week].get(name, 0) for name in names])
    return send_file(file, as_attachment=True)

@app.route('/uploads/<path:filename>')
def uploaded(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit(index):
    entries = _read_entries()
    if index < 0 or index >= len(entries):
        abort(404)
    row = entries[index]
    created_str = row.get('Created At', datetime.now().isoformat())
    if not isinstance(created_str, str):
        created_str = str(created_str)
    try:
        created = datetime.fromisoformat(created_str)
    except ValueError:
        created = datetime.now()
    if datetime.now() - created > timedelta(hours=24):
        flash('Editing period expired')
        return redirect(url_for('index'))
    if request.method == 'POST':
        row['Date'] = request.form['date']
        row['From Time'] = request.form['from_time']
        row['To Time'] = request.form['to_time']
        row['Task'] = request.form['task']
        row['Description'] = request.form.get('description', '')
        row['Completed'] = request.form.get('completed', '1')
        entries[index] = row
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=entries[0].keys())
            writer.writeheader()
            writer.writerows(entries)
        flash('Entry updated')
        return redirect(url_for('index'))
    return render_template('edit.html', row=row, index=index)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
