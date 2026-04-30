import sqlite3
import numpy as np
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

def get_connection():
    conn = sqlite3.connect('neev.db')
    conn.row_factory = sqlite3.Row
    return conn

# ─────────────────────────────────────────
# FUNCTION 1 — Predict next exam score
# Uses Linear Regression on past exam scores
# ─────────────────────────────────────────
def predict_next_score(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.name as subject_name, m.exam_type, m.score, m.exam_date
        FROM marks m
        JOIN subjects s ON m.subject_id = s.id
        WHERE m.student_id = ?
        ORDER BY s.id, m.exam_date
    """, (student_id,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {}

    # Group scores by subject
    subjects = {}
    for row in rows:
        name = row['subject_name']
        if name not in subjects:
            subjects[name] = []
        subjects[name].append(row['score'])

    predictions = {}

    for subject_name, scores in subjects.items():
        if len(scores) < 2:
            predictions[subject_name] = {
                'past_scores': scores,
                'predicted': round(scores[-1], 1),
                'trend': 'stable'
            }
            continue

        # Train Linear Regression
        X = np.array(range(len(scores))).reshape(-1, 1)
        y = np.array(scores)
        model = LinearRegression()
        model.fit(X, y)

        # Predict next exam
        next_index = np.array([[len(scores)]])
        predicted = float(model.predict(next_index)[0])
        predicted = max(0, min(100, round(predicted, 1)))

        # Calculate trend
        if scores[-1] > scores[0] + 5:
            trend = 'improving'
        elif scores[-1] < scores[0] - 5:
            trend = 'declining'
        else:
            trend = 'stable'

        predictions[subject_name] = {
            'past_scores': scores,
            'predicted': predicted,
            'trend': trend
        }

    return predictions


# ─────────────────────────────────────────
# FUNCTION 2 — Calculate attendance percentage
# Returns attendance per subject
# ─────────────────────────────────────────
def get_attendance(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.name as subject_name,
               COUNT(*) as total_classes,
               SUM(a.present) as attended
        FROM attendance a
        JOIN subjects s ON a.subject_id = s.id
        WHERE a.student_id = ?
        GROUP BY a.subject_id
    """, (student_id,))

    rows = cursor.fetchall()
    conn.close()

    attendance = {}
    for row in rows:
        total = row['total_classes']
        attended = row['attended']
        percentage = round((attended / total) * 100, 1) if total > 0 else 0
        can_miss = 0

        # Calculate how many more classes student can miss
        # and still stay above 75%
        if percentage > 75:
            # Formula: (attended - 0.75 * (total + x)) = 0
            # Solving for x gives how many they can miss
            can_miss = int((attended - 0.75 * total) / 0.75)
            can_miss = max(0, can_miss)

        attendance[row['subject_name']] = {
            'percentage': percentage,
            'attended': int(attended),
            'total': total,
            'can_miss': can_miss,
            'danger': percentage < 75
        }

    return attendance


# ─────────────────────────────────────────
# FUNCTION 3 — Calculate risk zone
# Strong / Weak / At-risk / Drop-risk
# ─────────────────────────────────────────
def get_risk_zone(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Get average marks
    cursor.execute("""
        SELECT AVG(score) as avg_score
        FROM marks
        WHERE student_id = ?
    """, (student_id,))
    result = cursor.fetchone()
    avg_marks = result['avg_score'] if result['avg_score'] else 0

    # Get average attendance
    cursor.execute("""
        SELECT COUNT(*) as total, SUM(present) as attended
        FROM attendance
        WHERE student_id = ?
    """, (student_id,))
    att = cursor.fetchone()
    avg_attendance = (att['attended'] / att['total'] * 100) if att['total'] > 0 else 0

    conn.close()

    # Classify into zones
    if avg_marks >= 70 and avg_attendance >= 80:
        zone = 'Strong'
        color = 'green'
        message = 'no cap you are absolutely killing it 🔥'
    elif avg_marks >= 55 and avg_attendance >= 75:
        zone = 'Weak'
        color = 'yellow'
        message = 'lowkey you can do better — small tweaks needed bestie'
    elif avg_marks >= 40 and avg_attendance >= 65:
        zone = 'At-risk'
        color = 'orange'
        message = 'this is giving concern — time to lock in fr'
    else:
        zone = 'Drop-risk'
        color = 'red'
        message = 'we need to talk rn — critical situation no cap'

    return {
        'zone': zone,
        'color': color,
        'message': message,
        'avg_marks': round(avg_marks, 1),
        'avg_attendance': round(avg_attendance, 1)
    }


# ─────────────────────────────────────────
# FUNCTION 4 — Calculate Slay Score
# Single 0-100 number combining everything
# ─────────────────────────────────────────
def get_slay_score(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Get average marks percentage
    cursor.execute("SELECT AVG(score) as avg FROM marks WHERE student_id = ?", (student_id,))
    marks_result = cursor.fetchone()
    marks_pct = marks_result['avg'] if marks_result['avg'] else 0

    # Get attendance percentage
    cursor.execute("""
        SELECT COUNT(*) as total, SUM(present) as attended
        FROM attendance WHERE student_id = ?
    """, (student_id,))
    att = cursor.fetchone()
    att_pct = (att['attended'] / att['total'] * 100) if att['total'] > 0 else 0

    # Get roadmap completion percentage
    cursor.execute("""
        SELECT COUNT(*) as total, SUM(completed) as done
        FROM roadmap_progress WHERE student_id = ?
    """, (student_id,))
    road = cursor.fetchone()
    roadmap_pct = (road['done'] / road['total'] * 100) if road['total'] > 0 else 0

    conn.close()

    # Mental wellness — we use a default of 60 since mood is anonymous
    # In real usage this would come from mood logs
    mental_pct = 60

    # Weighted formula
    # Marks 30% + Attendance 25% + Mental 30% + Roadmap 15%
    weights = np.array([0.30, 0.25, 0.30, 0.15])
    values = np.array([marks_pct, att_pct, mental_pct, roadmap_pct])
    slay_score = round(float(np.dot(weights, values)), 1)

    return {
        'slay_score': slay_score,
        'marks_pct': round(marks_pct, 1),
        'attendance_pct': round(att_pct, 1),
        'mental_pct': mental_pct,
        'roadmap_pct': round(roadmap_pct, 1)
    }


# ─────────────────────────────────────────
# FUNCTION 5 — Calculate burnout score
# Higher score = higher burnout risk
# ─────────────────────────────────────────
def get_burnout_score(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Check recent attendance drop
    # Compare last 2 weeks vs previous 2 weeks
    cursor.execute("""
        SELECT
            SUM(CASE WHEN date >= date('now', '-14 days') THEN present ELSE 0 END) as recent_attended,
            SUM(CASE WHEN date >= date('now', '-14 days') THEN 1 ELSE 0 END) as recent_total,
            SUM(CASE WHEN date < date('now', '-14 days') AND date >= date('now', '-28 days') THEN present ELSE 0 END) as prev_attended,
            SUM(CASE WHEN date < date('now', '-14 days') AND date >= date('now', '-28 days') THEN 1 ELSE 0 END) as prev_total
        FROM attendance
        WHERE student_id = ?
    """, (student_id,))

    att = cursor.fetchone()
    recent_att = (att['recent_attended'] / att['recent_total'] * 100) if att['recent_total'] > 0 else 75
    prev_att = (att['prev_attended'] / att['prev_total'] * 100) if att['prev_total'] > 0 else 75
    attendance_drop = max(0, prev_att - recent_att)

    # Check marks trend — is latest score lower than first score
    cursor.execute("""
        SELECT score FROM marks
        WHERE student_id = ?
        ORDER BY exam_date ASC
        LIMIT 1
    """, (student_id,))
    first = cursor.fetchone()

    cursor.execute("""
        SELECT score FROM marks
        WHERE student_id = ?
        ORDER BY exam_date DESC
        LIMIT 1
    """, (student_id,))
    latest = cursor.fetchone()

    marks_drop = 0
    if first and latest:
        marks_drop = max(0, first['score'] - latest['score'])

    conn.close()

    # Burnout formula
    # Attendance drop contributes 50%, marks drop contributes 50%
    burnout_score = min(100, round(
        (attendance_drop * 0.5) + (marks_drop * 0.5), 1
    ))

    if burnout_score >= 60:
        status = 'high'
        message = 'burnout detected — switching to recovery mode 💙'
    elif burnout_score >= 35:
        status = 'moderate'
        message = 'showing early signs — let us check in on you'
    else:
        status = 'low'
        message = 'you are holding up well fr'

    return {
        'burnout_score': burnout_score,
        'status': status,
        'message': message,
        'attendance_drop': round(attendance_drop, 1),
        'marks_drop': round(marks_drop, 1)
    }


# ─────────────────────────────────────────
# TEST — Run this file directly to test
# ─────────────────────────────────────────
if __name__ == '__main__':
    # Test with Arjun — roll CS2002, should show burnout and at-risk
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM students WHERE roll_number = 'CS2002'")
    arjun = cursor.fetchone()
    conn.close()

    if arjun:
        student_id = arjun['id']
        print("\n--- Testing with Arjun (CS2002) ---")

        print("\nSlay Score:")
        print(get_slay_score(student_id))

        print("\nRisk Zone:")
        print(get_risk_zone(student_id))

        print("\nBurnout Score:")
        print(get_burnout_score(student_id))

        print("\nPredictions (first 2 subjects):")
        predictions = predict_next_score(student_id)
        for i, (subject, data) in enumerate(predictions.items()):
            if i >= 2:
                break
            print(f"{subject}: past={data['past_scores']} predicted={data['predicted']} trend={data['trend']}")
    else:
        print("Arjun not found — make sure fake_data.py was run first")