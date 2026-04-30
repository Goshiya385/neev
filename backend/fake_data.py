import sqlite3
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('en_IN')

def get_connection():
    conn = sqlite3.connect('neev.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_students():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] > 0:
        print("Students already exist — skipping")
        conn.close()
        return

    students = []
    roll = 1001

    for year in range(1, 5):
        for i in range(12):
            name = fake.name()
            email = fake.email()
            roll_number = f"CS{roll}"
            password = "password123"
            students.append((roll_number, name, email, year, 'Computer Science', password))
            roll += 1

    students.append(("CS2001", "Riya Sharma", "riya@email.com", 3, "Computer Science", "password123"))
    students.append(("CS2002", "Arjun Mehta", "arjun@email.com", 2, "Computer Science", "password123"))
    students.append(("CS2003", "Priya Singh", "priya@email.com", 4, "Computer Science", "password123"))

    cursor.executemany(
        "INSERT INTO students (roll_number, name, email, year, branch, password) VALUES (?, ?, ?, ?, ?, ?)",
        students
    )

    conn.commit()
    conn.close()
    print("Students created successfully")

def generate_marks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM marks")
    if cursor.fetchone()[0] > 0:
        print("Marks already exist — skipping")
        conn.close()
        return

    cursor.execute("SELECT id, year FROM students")
    students = cursor.fetchall()

    exam_types = ['Unit Test 1', 'Mid Sem', 'Unit Test 2', 'End Sem']

    for student in students:
        student_id = student['id']
        student_year = student['year']

        cursor.execute("SELECT id FROM subjects WHERE year = ?", (student_year,))
        subjects = cursor.fetchall()

        pattern = random.choice([1, 2, 3, 4])

        for subject in subjects:
            subject_id = subject['id']
            base_score = random.randint(45, 85)

            for i, exam_type in enumerate(exam_types):
                if pattern == 1:
                    score = min(100, base_score + (i * random.randint(3, 8)))
                elif pattern == 2:
                    score = max(20, base_score - (i * random.randint(3, 8)))
                elif pattern == 3:
                    score = random.randint(70, 95)
                else:
                    score = random.randint(25, 50)

                exam_date = (datetime.now() - timedelta(days=(3 - i) * 45)).strftime('%Y-%m-%d')

                cursor.execute(
                    "INSERT INTO marks (student_id, subject_id, exam_type, score, max_score, exam_date) VALUES (?, ?, ?, ?, ?, ?)",
                    (student_id, subject_id, exam_type, round(score, 1), 100, exam_date)
                )

    cursor.execute("SELECT id FROM students WHERE roll_number = 'CS2001'")
    riya = cursor.fetchone()
    if riya:
        cursor.execute("SELECT id FROM subjects WHERE year = 3")
        subjects = cursor.fetchall()
        for subject in subjects:
            for i, exam_type in enumerate(exam_types):
                score = random.randint(78, 95)
                exam_date = (datetime.now() - timedelta(days=(3 - i) * 45)).strftime('%Y-%m-%d')
                cursor.execute(
                    "INSERT INTO marks (student_id, subject_id, exam_type, score, max_score, exam_date) VALUES (?, ?, ?, ?, ?, ?)",
                    (riya['id'], subject['id'], exam_type, score, 100, exam_date)
                )

    cursor.execute("SELECT id FROM students WHERE roll_number = 'CS2002'")
    arjun = cursor.fetchone()
    if arjun:
        cursor.execute("SELECT id FROM subjects WHERE year = 2")
        subjects = cursor.fetchall()
        scores = [72, 65, 54, 41]
        for subject in subjects:
            for i, exam_type in enumerate(exam_types):
                exam_date = (datetime.now() - timedelta(days=(3 - i) * 45)).strftime('%Y-%m-%d')
                cursor.execute(
                    "INSERT INTO marks (student_id, subject_id, exam_type, score, max_score, exam_date) VALUES (?, ?, ?, ?, ?, ?)",
                    (arjun['id'], subject['id'], exam_type, scores[i], 100, exam_date)
                )

    cursor.execute("SELECT id FROM students WHERE roll_number = 'CS2003'")
    priya = cursor.fetchone()
    if priya:
        cursor.execute("SELECT id FROM subjects WHERE year = 4")
        subjects = cursor.fetchall()
        for subject in subjects:
            for i, exam_type in enumerate(exam_types):
                score = random.randint(40, 60)
                exam_date = (datetime.now() - timedelta(days=(3 - i) * 45)).strftime('%Y-%m-%d')
                cursor.execute(
                    "INSERT INTO marks (student_id, subject_id, exam_type, score, max_score, exam_date) VALUES (?, ?, ?, ?, ?, ?)",
                    (priya['id'], subject['id'], exam_type, score, 100, exam_date)
                )

    conn.commit()
    conn.close()
    print("Marks generated successfully")

def generate_attendance():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM attendance")
    if cursor.fetchone()[0] > 0:
        print("Attendance already exist — skipping")
        conn.close()
        return

    cursor.execute("SELECT id, year FROM students")
    students = cursor.fetchall()

    for student in students:
        student_id = student['id']
        student_year = student['year']

        cursor.execute("SELECT id FROM subjects WHERE year = ?", (student_year,))
        subjects = cursor.fetchall()

        attendance_rate = random.uniform(0.65, 0.95)

        for subject in subjects:
            subject_id = subject['id']
            for day in range(60):
                date = (datetime.now() - timedelta(days=day)).strftime('%Y-%m-%d')
                present = 1 if random.random() < attendance_rate else 0
                cursor.execute(
                    "INSERT INTO attendance (student_id, subject_id, date, present) VALUES (?, ?, ?, ?)",
                    (student_id, subject_id, date, present)
                )

    cursor.execute("SELECT id FROM students WHERE roll_number = 'CS2002'")
    arjun = cursor.fetchone()
    if arjun:
        cursor.execute("DELETE FROM attendance WHERE student_id = ?", (arjun['id'],))
        cursor.execute("SELECT id FROM subjects WHERE year = 2")
        subjects = cursor.fetchall()
        for subject in subjects:
            for day in range(60):
                date = (datetime.now() - timedelta(days=day)).strftime('%Y-%m-%d')
                present = 1 if random.random() < 0.58 else 0
                cursor.execute(
                    "INSERT INTO attendance (student_id, subject_id, date, present) VALUES (?, ?, ?, ?)",
                    (arjun['id'], subject['id'], date, present)
                )

    conn.commit()
    conn.close()
    print("Attendance generated successfully")

def generate_mood_logs():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM mood_logs")
    if cursor.fetchone()[0] > 0:
        print("Mood logs already exist — skipping")
        conn.close()
        return

    for day in range(30):
        date = (datetime.now() - timedelta(days=day)).strftime('%Y-%m-%d')
        session_token = f"session_{day}_{random.randint(1000, 9999)}"
        mood_score = random.randint(1, 5)
        stress_score = random.randint(20, 90)
        cursor.execute(
            "INSERT INTO mood_logs (session_token, mood_score, stress_score, logged_at) VALUES (?, ?, ?, ?)",
            (session_token, mood_score, stress_score, date)
        )

    conn.commit()
    conn.close()
    print("Mood logs generated successfully")

def generate_roadmap_progress():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM roadmap_progress")
    if cursor.fetchone()[0] > 0:
        print("Roadmap progress already exists — skipping")
        conn.close()
        return

    roadmap_items = {
        1: ['Learn Python basics', 'Complete 1 mini project', 'Maintain 75% attendance', 'Join a coding club'],
        2: ['Start DSA', 'Solve 50 LeetCode problems', 'Build 1 project', 'Learn Git and GitHub'],
        3: ['Complete DBMS project', 'Apply for internship', 'Build portfolio website', 'Learn system design basics'],
        4: ['Update resume', 'Practice mock interviews', 'Apply to 10 companies', 'Complete final year project'],
    }

    cursor.execute("SELECT id, year FROM students")
    students = cursor.fetchall()

    for student in students:
        student_id = student['id']
        student_year = student['year']
        items = roadmap_items.get(student_year, [])

        for item in items:
            completed = 1 if random.random() > 0.5 else 0
            cursor.execute(
                "INSERT INTO roadmap_progress (student_id, year, item, completed) VALUES (?, ?, ?, ?)",
                (student_id, student_year, item, completed)
            )

    conn.commit()
    conn.close()
    print("Roadmap progress generated successfully")

if __name__ == '__main__':
    generate_students()
    generate_marks()
    generate_attendance()
    generate_mood_logs()
    generate_roadmap_progress()
    print("All fake data generated. Neev database is ready.")