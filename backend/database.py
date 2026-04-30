import sqlite3
import os

# This function connects to our database file
# If the file doesn't exist, it creates it automatically
def get_connection():
    conn = sqlite3.connect('neev.db')
    conn.row_factory = sqlite3.Row
    return conn

# This function creates all 6 tables
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # TABLE 1: students
    # Stores every student's basic information
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            year INTEGER NOT NULL,
            branch TEXT DEFAULT 'Computer Science',
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # TABLE 2: subjects
    # Stores all subjects for each year
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            year INTEGER NOT NULL,
            credits INTEGER DEFAULT 3
        )
    ''')

    # TABLE 3: marks
    # Stores every exam score for every student
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            exam_type TEXT NOT NULL,
            score REAL NOT NULL,
            max_score REAL DEFAULT 100,
            exam_date TEXT,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        )
    ''')

    # TABLE 4: attendance
    # Stores daily attendance for every student in every subject
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            present INTEGER DEFAULT 1,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        )
    ''')

    # TABLE 5: mood_logs
    # Stores anonymous mental health check-ins
    # Notice: no student_id here — this is fully anonymous
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT NOT NULL,
            mood_score INTEGER NOT NULL,
            stress_score INTEGER NOT NULL,
            note TEXT,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # TABLE 6: roadmap_progress
    # Tracks what each student has completed in their year-wise roadmap
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roadmap_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            item TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            completed_at TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("All 6 tables created successfully")

# This function adds all subjects for all 4 years
def seed_subjects():
    conn = get_connection()
    cursor = conn.cursor()

    # Check if subjects already exist
    cursor.execute("SELECT COUNT(*) FROM subjects")
    count = cursor.fetchone()[0]
    if count > 0:
        print("Subjects already exist — skipping")
        conn.close()
        return

    subjects = [
        # 1st Year subjects
        ('Mathematics I', 'MATH101', 1, 4),
        ('Physics', 'PHY101', 1, 3),
        ('Programming Fundamentals', 'CS101', 1, 4),
        ('English Communication', 'ENG101', 1, 2),
        ('Engineering Drawing', 'ME101', 1, 2),

        # 2nd Year subjects
        ('Data Structures', 'CS201', 2, 4),
        ('Mathematics III', 'MATH201', 2, 4),
        ('Digital Electronics', 'EC201', 2, 3),
        ('Object Oriented Programming', 'CS202', 2, 4),
        ('Discrete Mathematics', 'MATH202', 2, 3),

        # 3rd Year subjects
        ('Database Management Systems', 'CS301', 3, 4),
        ('Operating Systems', 'CS302', 3, 4),
        ('Computer Networks', 'CS303', 3, 4),
        ('Software Engineering', 'CS304', 3, 3),
        ('Machine Learning', 'CS305', 3, 3),

        # 4th Year subjects
        ('Artificial Intelligence', 'CS401', 4, 4),
        ('Cloud Computing', 'CS402', 4, 3),
        ('Cyber Security', 'CS403', 4, 3),
        ('Project Work', 'CS404', 4, 6),
        ('Professional Ethics', 'CS405', 4, 2),
    ]

    cursor.executemany(
        "INSERT INTO subjects (name, code, year, credits) VALUES (?, ?, ?, ?)",
        subjects
    )

    conn.commit()
    conn.close()
    print("All subjects added successfully")

# Run everything
if __name__ == '__main__':
    create_tables()
    seed_subjects()
    print("Database is ready")