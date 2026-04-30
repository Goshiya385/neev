from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
import os
from dotenv import load_dotenv
from models import predict_next_score, get_attendance, get_risk_zone, get_slay_score, get_burnout_score
from groq_ai import counselor_chat, get_study_plan, get_roadmap_gap, get_career_advice

load_dotenv()

app = Flask(__name__)
app.secret_key = 'neev_secret_key_2024'
CORS(app, supports_credentials=True)

def get_connection():
    conn = sqlite3.connect('neev.db')
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────
# ROUTE 1 — Login
# POST /api/login
# ─────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    roll_number = data.get('roll_number')
    password = data.get('password')

    if not roll_number or not password:
        return jsonify({'error': 'Roll number and password required'}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, year, branch FROM students WHERE roll_number = ? AND password = ?",
        (roll_number, password)
    )
    student = cursor.fetchone()
    conn.close()

    if not student:
        return jsonify({'error': 'Invalid roll number or password'}), 401

    session['student_id'] = student['id']

    return jsonify({
        'success': True,
        'student_id': student['id'],
        'name': student['name'],
        'year': student['year'],
        'branch': student['branch']
    })


# ─────────────────────────────────────────
# ROUTE 2 — Dashboard
# GET /api/dashboard/<student_id>
# ─────────────────────────────────────────
@app.route('/api/dashboard/<int:student_id>', methods=['GET'])
def dashboard(student_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, year, branch FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    conn.close()

    if not student:
        return jsonify({'error': 'Student not found'}), 404

    slay = get_slay_score(student_id)
    risk = get_risk_zone(student_id)
    burnout = get_burnout_score(student_id)

    return jsonify({
        'name': student['name'],
        'year': student['year'],
        'branch': student['branch'],
        'slay_score': slay['slay_score'],
        'slay_breakdown': slay,
        'risk_zone': risk['zone'],
        'risk_color': risk['color'],
        'risk_message': risk['message'],
        'burnout_score': burnout['burnout_score'],
        'burnout_status': burnout['status'],
        'burnout_message': burnout['message']
    })


# ─────────────────────────────────────────
# ROUTE 3 — Performance
# GET /api/performance/<student_id>
# ─────────────────────────────────────────
@app.route('/api/performance/<int:student_id>', methods=['GET'])
def performance(student_id):
    predictions = predict_next_score(student_id)
    attendance = get_attendance(student_id)

    subjects = []
    for subject_name, pred_data in predictions.items():
        att_data = attendance.get(subject_name, {})
        subjects.append({
            'name': subject_name,
            'past_scores': pred_data['past_scores'],
            'predicted': pred_data['predicted'],
            'trend': pred_data['trend'],
            'attendance_pct': att_data.get('percentage', 0),
            'can_miss': att_data.get('can_miss', 0),
            'danger': att_data.get('danger', False)
        })

    return jsonify({'subjects': subjects})


# ─────────────────────────────────────────
# ROUTE 4 — Risk
# GET /api/risk/<student_id>
# ─────────────────────────────────────────
@app.route('/api/risk/<int:student_id>', methods=['GET'])
def risk(student_id):
    risk_data = get_risk_zone(student_id)
    burnout_data = get_burnout_score(student_id)

    return jsonify({
        'zone': risk_data['zone'],
        'color': risk_data['color'],
        'message': risk_data['message'],
        'avg_marks': risk_data['avg_marks'],
        'avg_attendance': risk_data['avg_attendance'],
        'burnout_score': burnout_data['burnout_score'],
        'burnout_status': burnout_data['status']
    })


# ─────────────────────────────────────────
# ROUTE 5 — Roadmap
# GET /api/roadmap/<student_id>
# ─────────────────────────────────────────
@app.route('/api/roadmap/<int:student_id>', methods=['GET'])
def roadmap(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT year FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()

    cursor.execute("""
        SELECT item, completed
        FROM roadmap_progress
        WHERE student_id = ?
    """, (student_id,))
    progress = cursor.fetchall()
    conn.close()

    checklist = [{'item': row['item'], 'completed': bool(row['completed'])} for row in progress]
    completed_count = sum(1 for item in checklist if item['completed'])
    total_count = len(checklist)
    completion_pct = round((completed_count / total_count * 100), 1) if total_count > 0 else 0

    gap_report = get_roadmap_gap(student_id)

    return jsonify({
        'year': student['year'],
        'checklist': checklist,
        'completed': completed_count,
        'total': total_count,
        'completion_pct': completion_pct,
        'gap_report': gap_report
    })


# ─────────────────────────────────────────
# ROUTE 6 — Anonymous counselor chat
# POST /api/chat
# ─────────────────────────────────────────
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message')

    if not message:
        return jsonify({'error': 'Message required'}), 400

    reply = counselor_chat(message)
    return jsonify({'reply': reply})


# ─────────────────────────────────────────
# ROUTE 7 — Study plan
# GET /api/studyplan/<student_id>
# ─────────────────────────────────────────
@app.route('/api/studyplan/<int:student_id>', methods=['GET'])
def studyplan(student_id):
    burnout = get_burnout_score(student_id)
    plan = get_study_plan(student_id)

    return jsonify({
        'plan': plan,
        'mode': 'chill' if burnout['status'] == 'high' else 'normal',
        'burnout_status': burnout['status']
    })


# ─────────────────────────────────────────
# ROUTE 8 — Career advice
# GET /api/career/<student_id>
# ─────────────────────────────────────────
@app.route('/api/career/<int:student_id>', methods=['GET'])
def career(student_id):
    advice = get_career_advice(student_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT year FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    conn.close()

    return jsonify({
        'year': student['year'],
        'advice': advice
    })


# ─────────────────────────────────────────
# ROUTE 9 — Admin class overview
# GET /api/admin/class
# ─────────────────────────────────────────
@app.route('/api/admin/class', methods=['GET'])
def admin_class():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, roll_number, year FROM students ORDER BY year, name")
    students = cursor.fetchall()
    conn.close()

    result = []
    for student in students:
        slay = get_slay_score(student['id'])
        risk = get_risk_zone(student['id'])
        result.append({
            'id': student['id'],
            'name': student['name'],
            'roll_number': student['roll_number'],
            'year': student['year'],
            'slay_score': slay['slay_score'],
            'risk_zone': risk['zone'],
            'risk_color': risk['color']
        })

    return jsonify({'students': result})


# ─────────────────────────────────────────
# ROUTE 10 — Admin nightly check
# POST /api/admin/nightcheck
# ─────────────────────────────────────────
@app.route('/api/admin/nightcheck', methods=['POST'])
def nightcheck():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()
    conn.close()

    flagged = []
    for student in students:
        burnout = get_burnout_score(student['id'])
        risk = get_risk_zone(student['id'])

        if burnout['status'] == 'high' or risk['zone'] in ['At-risk', 'Drop-risk']:
            flagged.append({
                'name': student['name'],
                'burnout_status': burnout['status'],
                'risk_zone': risk['zone']
            })

    return jsonify({
        'checked': len(students),
        'flagged_count': len(flagged),
        'flagged': flagged
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)