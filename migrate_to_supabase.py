import os
import csv
from datetime import datetime
from supabase import create_client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_KEY')
if not url or not key:
    raise SystemExit('Missing SUPABASE_URL or SUPABASE_SERVICE_KEY')
client = create_client(url, key)
TABLE = 'time_entries'

with open('time_log.csv', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        row.setdefault('Created At', datetime.now().isoformat())
        client.table(TABLE).insert(row).execute()
