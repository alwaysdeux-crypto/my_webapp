import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require', cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS todos')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saju_profiles (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            gender TEXT DEFAULT '남',
            birth_date TEXT NOT NULL,
            birth_time TEXT,
            memo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_all_profiles(search=''):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM saju_profiles WHERE 1=1'
    params = []

    if search:
        query += ' AND name LIKE %s'
        params.append(f'%{search}%')

    query += ' ORDER BY created_at DESC'

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_profile_by_id(profile_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM saju_profiles WHERE id = %s', (profile_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_profile(name, gender, birth_date, birth_time, memo):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO saju_profiles (name, gender, birth_date, birth_time, memo)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    ''', (name, gender, birth_date, birth_time, memo))
    profile_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()
    return get_profile_by_id(profile_id)

def update_profile(profile_id, name, gender, birth_date, birth_time, memo):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE saju_profiles
        SET name = %s, gender = %s, birth_date = %s, birth_time = %s, memo = %s
        WHERE id = %s
    ''', (name, gender, birth_date, birth_time, memo, profile_id))
    conn.commit()
    conn.close()
    return get_profile_by_id(profile_id)

def delete_profile(profile_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM saju_profiles WHERE id = %s', (profile_id,))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as total FROM saju_profiles')
    total = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as male FROM saju_profiles WHERE gender = '남'")
    male = cursor.fetchone()['male']

    cursor.execute("SELECT COUNT(*) as female FROM saju_profiles WHERE gender = '여'")
    female = cursor.fetchone()['female']

    conn.close()

    return {
        'total': total,
        'male': male,
        'female': female,
    }
