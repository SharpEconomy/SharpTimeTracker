import csv
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import plotly.graph_objs as go
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html

app = Flask(__name__)
app.secret_key = 'secret123'
CSV_FILE = 'time_log.csv'

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'Email', 'Date', 'From Time', 'To Time', 'Task', 'Description'])

@app.route('/')
def index():
    df = pd.read_csv(CSV_FILE)
    df['Hours'] = [
        (datetime.strptime(row['To Time'], '%H:%M') - datetime.strptime(row['From Time'], '%H:%M')).seconds / 3600
        for _, row in df.iterrows()
    ]
    summary = df.groupby(['Name', 'Date'])['Hours'].sum().reset_index()
    return render_template('index.html', data=summary.to_dict(orient='records'))

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

@app.route('/download')
def download():
    return send_file(CSV_FILE, as_attachment=True)

@app.route('/weekly-download')
def weekly_download():
    df = pd.read_csv(CSV_FILE)
    df['Hours'] = [
        (datetime.strptime(row['To Time'], '%H:%M') - datetime.strptime(row['From Time'], '%H:%M')).seconds / 3600
        for _, row in df.iterrows()
    ]
    df['Date'] = pd.to_datetime(df['Date'])
    df['Week'] = df['Date'].dt.to_period('W').astype(str)
    weekly = df.groupby(['Week', 'Name'])['Hours'].sum().unstack(fill_value=0).reset_index()
    file = 'weekly_report.csv'
    weekly.to_csv(file, index=False)
    return send_file(file, as_attachment=True)

def create_dash_app(flask_app):
    dash_app = Dash(__name__, server=flask_app, url_base_pathname='/dash/')

    def serve_layout():
        df = pd.read_csv(CSV_FILE)
        df['Hours'] = [
            (
                datetime.strptime(row['To Time'], '%H:%M')
                - datetime.strptime(row['From Time'], '%H:%M')
            ).seconds
            / 3600
            for _, row in df.iterrows()
        ]
        df['Date'] = pd.to_datetime(df['Date'])
        df['Week'] = df['Date'].dt.to_period('W').astype(str)
        weekly = (
            df.groupby(['Week', 'Name'])['Hours']
            .sum()
            .unstack(fill_value=0)
            .reset_index()
        )

        traces = [
            go.Bar(name=col, x=weekly['Week'], y=weekly[col])
            for col in weekly.columns
            if col != 'Week'
        ]

        return html.Div(
            children=[
                html.H2('Weekly Report'),
                dcc.Graph(
                    id='weekly-chart',
                    figure={
                        'data': traces,
                        'layout': go.Layout(
                            barmode='stack', title='Weekly Time Tracked'
                        ),
                    },
                ),
            ]
        )

    dash_app.layout = serve_layout
    return dash_app

create_dash_app(app)

if __name__ == '__main__':
    app.run(debug=True)
