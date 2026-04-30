from groq import Groq
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def get_connection():
    conn = sqlite3.connect('neev.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_student_context(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name, year, branch FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()

    cursor.execute("SELECT AVG(score) as avg FROM marks WHERE student_id = ?", (student_id,))
    marks = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(*) as total, SUM(present) as attended
        FROM attendance WHERE student_id = ?
    """, (student_id,))
    att = cursor.fetchone()

    cursor.execute("""
        SELECT s.name as subject_name, AVG(m.score) as avg_score
        FROM marks m
        JOIN subjects s ON m.subject_id = s.id
        WHERE m.student_id = ?
        GROUP BY m.subject_id
        ORDER BY avg_score ASC
        LIMIT 3
    """, (student_id,))
    weak_subjects = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*) as total, SUM(completed) as done
        FROM roadmap_progress WHERE student_id = ?
    """, (student_id,))
    roadmap = cursor.fetchone()

    conn.close()

    attendance_pct = round((att['attended'] / att['total'] * 100), 1) if att['total'] > 0 else 0
    roadmap_pct = round((roadmap['done'] / roadmap['total'] * 100), 1) if roadmap['total'] > 0 else 0
    weak_list = [f"{row['subject_name']} ({round(row['avg_score'], 1)}%)" for row in weak_subjects]

    context = f"""
Student name: {student['name']}
Year: {student['year']} (BTech {student['branch']})
Average marks: {round(marks['avg'], 1)}%
Attendance: {attendance_pct}%
Weakest subjects: {', '.join(weak_list)}
Roadmap completion: {roadmap_pct}%
"""
    return context


# ─────────────────────────────────────────
# FUNCTION 1 — Anonymous counselor chat
# No student data here — fully anonymous
# ─────────────────────────────────────────
def counselor_chat(message):
    system_prompt = """
You are Neev's anonymous AI counselor for BTech college students in India.
Your name is Nova.
You speak in warm, casual Gen Z language — using words like no cap, lowkey, fr, bestie, hits different, understood the assignment.
You are empathetic, never dismissive, and never judgmental.
This chat is completely anonymous — the student has no identity here.
Your job is to listen, reduce stress, and gently help them think through their problems.
Never give medical advice.
If someone seems severely distressed, kindly suggest they speak to a college counselor or trusted adult.
Keep responses short — 3 to 4 sentences maximum.
Always end with a question or a gentle nudge forward.
"""

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        model="llama-3.3-70b-versatile",
        max_tokens=200
    )

    return response.choices[0].message.content


# ─────────────────────────────────────────
# FUNCTION 2 — Personalized weekly study plan
# Uses student's actual weak subjects and stress
# ─────────────────────────────────────────
def get_study_plan(student_id):
    context = get_student_context(student_id)

    system_prompt = """
You are Neev, an AI academic guide for BTech students in India.
You speak in friendly Gen Z language — casual but helpful.
Generate a realistic weekly study plan based on the student data provided.
Format it as Monday to Sunday with specific subjects and time durations.
Keep it achievable — not overwhelming.
Focus on the weakest subjects first.
Add one motivational line at the end.
Keep the total response under 250 words.
"""

    user_message = f"""
Here is the student's current academic situation:
{context}

Generate a personalized weekly study plan for this student.
Make it specific, realistic, and in Gen Z tone.
"""

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        model="llama-3.3-70b-versatile",
        max_tokens=400
    )

    return response.choices[0].message.content


# ─────────────────────────────────────────
# FUNCTION 3 — Year-wise roadmap gap report
# Tells student exactly what they are missing
# ─────────────────────────────────────────
def get_roadmap_gap(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT year FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    year = student['year']

    cursor.execute("""
        SELECT item, completed
        FROM roadmap_progress
        WHERE student_id = ?
    """, (student_id,))
    progress = cursor.fetchall()
    conn.close()

    completed_items = [row['item'] for row in progress if row['completed'] == 1]
    pending_items = [row['item'] for row in progress if row['completed'] == 0]

    context = get_student_context(student_id)

    system_prompt = """
You are Neev, an honest but supportive AI guide for BTech students.
You speak in Gen Z language — direct, warm, no sugarcoating.
Your job is to tell the student exactly what gaps exist in their academic journey.
Be specific. Be honest. But never harsh.
Give a clear 3 step action plan at the end.
Keep response under 200 words.
"""

    user_message = f"""
Student is in Year {year} of BTech.

Academic context:
{context}

Completed roadmap items: {', '.join(completed_items) if completed_items else 'None yet'}
Pending roadmap items: {', '.join(pending_items) if pending_items else 'All done'}

Write an honest gap report for this student.
Tell them what they should have done by now, what is missing, and what to do next.
Use Gen Z language — direct but caring.
"""

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        model="llama-3.3-70b-versatile",
        max_tokens=350
    )

    return response.choices[0].message.content


# ─────────────────────────────────────────
# FUNCTION 4 — Career guidance
# Based on year and subject scores
# ─────────────────────────────────────────
def get_career_advice(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT year FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    year = student['year']

    cursor.execute("""
        SELECT s.name as subject_name, AVG(m.score) as avg_score
        FROM marks m
        JOIN subjects s ON m.subject_id = s.id
        WHERE m.student_id = ?
        GROUP BY m.subject_id
        ORDER BY avg_score DESC
    """, (student_id,))
    subject_scores = cursor.fetchall()
    conn.close()

    scores_text = '\n'.join([f"{row['subject_name']}: {round(row['avg_score'], 1)}%" for row in subject_scores])

    year_context = {
        1: "1st year student — still exploring, no pressure to choose yet",
        2: "2nd year student — time to pick a direction and start building skills",
        3: "3rd year student — needs to focus on internships and real projects",
        4: "4th year student — placement preparation is the top priority right now"
    }

    system_prompt = """
You are Neev, a career guidance AI for BTech students in India.
You speak in Gen Z language — honest, direct, supportive.
Suggest the most suitable career paths based on the student's subject performance.
Be specific about what they should do next based on their year.
Mention specific skills, platforms, or resources they should explore.
Keep response under 250 words.
"""

    user_message = f"""
Student situation: {year_context.get(year, 'BTech student')}

Subject scores:
{scores_text}

Give honest career guidance for this student.
Which career paths suit them based on their scores?
What should they do in the next 30 days?
"""

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        model="llama-3.3-70b-versatile",
        max_tokens=400
    )

    return response.choices[0].message.content


# ─────────────────────────────────────────
# TEST — Run directly to test all 4 functions
# ─────────────────────────────────────────
if __name__ == '__main__':
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM students WHERE roll_number = 'CS2002'")
    arjun = cursor.fetchone()
    conn.close()

    if arjun:
        student_id = arjun['id']

        print("\n--- Testing counselor chat ---")
        print(counselor_chat("I am so stressed about exams and I don't know where to start"))

        print("\n--- Testing study plan ---")
        print(get_study_plan(student_id))

        print("\n--- Testing roadmap gap ---")
        print(get_roadmap_gap(student_id))

        print("\n--- Testing career advice ---")
        print(get_career_advice(student_id))