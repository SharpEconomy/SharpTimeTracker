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
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "replace-me")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, 'time_log.csv')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
FIELDNAMES = [
    'Name',
    'Date',
    'From Time',
    'To Time',
    'Task',
    'Description',
    'File',
    'Created At',
]

DB_URL = os.environ.get('SUPABASE_DB_URL') or os.environ.get('DATABASE_URL')
TABLE_NAME = 'time_entries'

def get_conn():
    if not DB_URL:
        return None
    return psycopg2.connect(DB_URL)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def _map_row(row: dict) -> dict:
    key_map = {
        'name': 'Name',
        'date': 'Date',
        'from_time': 'From Time',
        'to_time': 'To Time',
        'task': 'Task',
        'description': 'Description',
        'file': 'File',
        'created_at': 'Created At',
        'created at': 'Created At',
    }
    out = {}
    for k, v in row.items():
        kk = k.lower().replace(' ', '_')
        if kk in key_map:
            out[key_map[kk]] = v
        else:
            out[k] = v
    for f in FIELDNAMES:
        out.setdefault(f, '')
    return out

def _read_entries():
    if DB_URL:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM {TABLE_NAME} ORDER BY date, from_time")
                rows = cur.fetchall()

        entries = []
        for row in rows:
            mapped = _map_row(row)
            mapped['id'] = row.get('id')
            mapped['Date'] = _canonical_date(mapped['Date'])
            entries.append(mapped)
        return entries
    entries = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                row['Date'] = _canonical_date(row['Date'])
                entries.append(row)
    return entries

def _hours(from_t, to_t):
    fmt = '%H:%M'
    return (datetime.strptime(to_t, fmt) - datetime.strptime(from_t, fmt)).seconds / 3600

def _hm(hours: float) -> str:
    hrs = int(hours)
    mins = int(round((hours - hrs) * 60))
    return f"{hrs}:{mins:02d}"

def _parse_date(date_str):
    formats = ['%Y-%m-%d', '%m-%d-%Y', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return datetime.now()

def _canonical_date(date_str):
    return _parse_date(date_str).strftime('%Y-%m-%d')

def _format_date(date_str, show_year=False):
    dt = _parse_date(date_str)
    return dt.strftime('%m/%d/%Y' if show_year else '%m/%d')

def _format_date_long(date_str):
    dt = _parse_date(date_str)
    return dt.strftime('%-d %B')

@app.template_filter('linkify')
def _linkify(text):
    url_pattern = r'(https?://[\w\.-/]+)'
    return re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)

def _weekly_summary(entries):
    weekly = defaultdict(lambda: defaultdict(float))
    for row in entries:
        dt = _parse_date(row['Date'])
        week_start = dt - timedelta(days=dt.weekday())
        key = week_start.strftime('%Y-%m-%d')
        weekly[key][row['Name']] += _hours(row['From Time'], row['To Time'])
    return weekly

def _daily_summary(entries):
    daily = defaultdict(lambda: defaultdict(float))
    for row in entries:
        key = _canonical_date(row['Date'])
        daily[key][row['Name']] += _hours(row['From Time'], row['To Time'])
    return daily

def _weekday_summary(entries):
    days = defaultdict(lambda: defaultdict(float))
    labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for row in entries:
        dt = _parse_date(row['Date'])
        key = labels[dt.weekday()]
        days[key][row['Name']] += _hours(row['From Time'], row['To Time'])
    return days

def _week_list(entries):
    weeks = sorted(_weekly_summary(entries).keys())
    return weeks


@app.route('/')
def index():
    entries = _read_entries()
    years = {_parse_date(e['Date']).year for e in entries}
    show_year = any(year != 2025 for year in years)
    for i, e in enumerate(entries):
        e['index'] = i
        e['hours'] = _hours(e['From Time'], e['To Time'])
        hrs = int(e['hours'])
        mins = int(round((e['hours'] - hrs) * 60))
        e['duration_str'] = f"{hrs}h {mins}m"
        e['duration_hm'] = f"{hrs}:{mins:02d}"
        e['date_display'] = _format_date(e['Date'], show_year)

    grouped = defaultdict(list)
    totals = {}
    for e in entries:
        key = _canonical_date(e['Date'])
        grouped[key].append(e)
    for date, rows in grouped.items():
        per = defaultdict(float)
        for r in rows:
            per[r['Name']] += r['hours']
        totals[date] = per

    ordered = dict(sorted(grouped.items()))
    return render_template(
        'index.html',
        grouped=ordered,
        totals=totals,
        show_year=show_year,
        format_date=_format_date,
    )

@app.route('/add', methods=['POST'])
def add():
    today = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    today = _canonical_date(today)
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
    row = {
        'Name': request.form['name'],
        'Date': today,
        'From Time': request.form['from_time'],
        'To Time': request.form['to_time'],
        'Task': request.form['task'],
        'Description': request.form.get('description', ''),
        'File': filename,
        'Created At': datetime.now().isoformat(),
    }
    if DB_URL:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {TABLE_NAME} (name, date, from_time, to_time, task, description, file, created_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        row['Name'],
                        row['Date'],
                        row['From Time'],
                        row['To Time'],
                        row['Task'],
                        row['Description'],
                        row['File'],
                        row['Created At'],
                    ),
                )
                conn.commit()

    else:
        with open(CSV_FILE, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writerow(row)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        hours = _hours(row['From Time'], row['To Time'])
        years = {_parse_date(r['Date']).year for r in _read_entries()}
        show_year = any(y != 2025 for y in years)
        return jsonify(
            {
                'name': row['Name'],
                'date_display': _format_date(row['Date'], show_year),
                'hours': hours,
                'duration_str': f"{int(hours)}h {int(round((hours-int(hours))*60))}m",
                'duration_hm': f"{int(hours)}:{int(round((hours-int(hours))*60)):02d}",
                'task': row['Task'],
                'description_html': _linkify(row['Description']),
                'file_link': f'<a href="/uploads/{filename}" download target="_blank">{filename}</a>' if filename else '',
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
    years = {_parse_date(w).year for w in weeks}
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

@app.route('/weekdays-data')
def weekdays_data():
    days = _weekday_summary(_read_entries())
    labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    names = sorted({n for d in days.values() for n in d.keys()})
    hours = {name: [days[lab].get(name, 0) for lab in labels] for name in names}
    return jsonify({'days': labels, 'names': names, 'hours': hours})

@app.route('/week-list')
def week_list():
    weeks = _week_list(_read_entries())
    return jsonify({'weeks': weeks})

@app.route('/week-data')
def week_data():
    start = request.args.get('start')
    if not start:
        return jsonify({'error': 'missing start'}), 400
    dt = _parse_date(start)
    days = [(dt + timedelta(days=i)) for i in range(7)]
    day_keys = [d.strftime('%Y-%m-%d') for d in days]
    labels = [_format_date_long(d.strftime('%Y-%m-%d')) for d in days]
    entries = [e for e in _read_entries() if _canonical_date(e['Date']) in day_keys]
    data = defaultdict(lambda: defaultdict(float))
    weekday_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for e in entries:
        d = _parse_date(e['Date']).weekday()
        key = weekday_labels[d]
        data[key][e['Name']] += _hours(e['From Time'], e['To Time'])
    names = sorted({n for d in data.values() for n in d.keys()})
    hours = {name: [data[weekday_labels[i]].get(name, 0) for i in range(7)] for name in names}
    return jsonify({'days': labels, 'names': names, 'hours': hours})

@app.route('/download')
def download():
    entries = _read_entries()
    file = 'entries.csv'
    with open(file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Name',
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
                e.get('Name', ''),
                e['Date'],
                e['From Time'],
                e['To Time'],
                _hm(_hours(e['From Time'], e['To Time'])),
                e['Task'],
                e['Description'],
                e['File'],
            ])
    return send_file(file, as_attachment=True, download_name='Sharp Time Tracker.csv')

@app.route('/weekly-download')
def weekly_download():
    weekly = _weekly_summary(_read_entries())
    weeks = sorted(weekly.keys())
    years = {_parse_date(w).year for w in weeks}
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
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'expired'}), 400
        flash('Editing period expired')
        return redirect(url_for('index'))
    if request.method == 'POST':
        row['Date'] = _canonical_date(request.form['date'])
        row['From Time'] = request.form['from_time']
        row['To Time'] = request.form['to_time']
        row['Task'] = request.form['task']
        row['Description'] = request.form.get('description', '')
        entries[index] = row
        if DB_URL:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"UPDATE {TABLE_NAME} SET date=%s, from_time=%s, to_time=%s, task=%s, description=%s WHERE id=%s",
                        (
                            row['Date'],
                            row['From Time'],
                            row['To Time'],
                            row['Task'],
                            row['Description'],
                            row.get('id'),
                        ),
                    )
                    conn.commit()

        else:
            with open(CSV_FILE, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                writer.writeheader()
                writer.writerows(entries)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
        flash('Entry updated')
        return redirect(url_for('index'))
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = dict(row)
        data['index'] = index
        return jsonify(data)
    return render_template('edit.html', row=row, index=index)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
