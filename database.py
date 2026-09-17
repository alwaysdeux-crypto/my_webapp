import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join('/tmp', 'todos.db') if os.environ.get('VERCEL') else os.path.join(os.path.dirname(__file__), 'todos.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT '업무',
            priority TEXT DEFAULT '보통',
            due_date TEXT,
            completed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    
    # Check if empty, seed initial sample data
    cursor.execute('SELECT COUNT(*) as count FROM todos')
    count = cursor.fetchone()['count']
    
    if count == 0:
        today = datetime.now()
        sample_todos = [
            (
                'AI Agent 기반 Flask 웹앱 검증하기',
                'Flask 서버 구동 후 API 엔드포인트 및 UI 기능 동작 상태 테스트하기',
                '업무',
                '긴급',
                (today + timedelta(days=1)).strftime('%Y-%m-%d'),
                0
            ),
            (
                '할일 관리 애플리케이션 디자인 고도화',
                'Glassmorphism 스타일 및 다크 모드 테마 CSS 미세 조정하기',
                '디자인',
                '높음',
                (today + timedelta(days=2)).strftime('%Y-%m-%d'),
                1
            ),
            (
                '주간 업무 일정 및 목표 작성',
                '다음 주 프로젝트 마일스톤 및 핵심 과제 정리하기',
                '기획',
                '보통',
                (today + timedelta(days=3)).strftime('%Y-%m-%d'),
                0
            ),
            (
                '팀 개발 문서 업데이트 및 리뷰',
                '최신 API 명세서 및 시스템 아키텍처 다이어그램 업데이트',
                '업무',
                '낮음',
                (today + timedelta(days=5)).strftime('%Y-%m-%d'),
                0
            )
        ]
        
        cursor.executemany('''
            INSERT INTO todos (title, description, category, priority, due_date, completed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_todos)
        conn.commit()
        
    conn.close()

def get_all_todos(status='all', category='all', priority='all', search='', sort_by='due_date'):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM todos WHERE 1=1'
    params = []
    
    if status == 'active':
        query += ' AND completed = 0'
    elif status == 'completed':
        query += ' AND completed = 1'
        
    if category != 'all' and category:
        query += ' AND category = ?'
        params.append(category)
        
    if priority != 'all' and priority:
        query += ' AND priority = ?'
        params.append(priority)
        
    if search:
        query += ' AND (title LIKE ? OR description LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param])
        
    if sort_by == 'due_date':
        query += ' ORDER BY completed ASC, due_date ASC, created_at DESC'
    elif sort_by == 'priority':
        query += ''' ORDER BY completed ASC, 
            CASE priority 
                WHEN '긴급' THEN 1 
                WHEN '높음' THEN 2 
                WHEN '보통' THEN 3 
                WHEN '낮음' THEN 4 
                ELSE 5 
            END ASC, created_at DESC'''
    else:
        query += ' ORDER BY completed ASC, created_at DESC'
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_todo_by_id(todo_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM todos WHERE id = ?', (todo_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_todo(title, description, category, priority, due_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO todos (title, description, category, priority, due_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, description, category, priority, due_date))
    conn.commit()
    todo_id = cursor.lastrowid
    conn.close()
    return get_todo_by_id(todo_id)

def update_todo(todo_id, title, description, category, priority, due_date, completed):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE todos
        SET title = ?, description = ?, category = ?, priority = ?, due_date = ?, completed = ?
        WHERE id = ?
    ''', (title, description, category, priority, due_date, completed, todo_id))
    conn.commit()
    conn.close()
    return get_todo_by_id(todo_id)

def toggle_todo(todo_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT completed FROM todos WHERE id = ?', (todo_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    new_status = 1 if row['completed'] == 0 else 0
    cursor.execute('UPDATE todos SET completed = ? WHERE id = ?', (new_status, todo_id))
    conn.commit()
    conn.close()
    return get_todo_by_id(todo_id)

def delete_todo(todo_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total FROM todos')
    total = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as completed FROM todos WHERE completed = 1')
    completed = cursor.fetchone()['completed']
    
    pending = total - completed
    rate = round((completed / total * 100), 1) if total > 0 else 0
    
    # Priority breakdown
    cursor.execute('''
        SELECT priority, COUNT(*) as count 
        FROM todos 
        WHERE completed = 0 
        GROUP BY priority
    ''')
    priority_rows = cursor.fetchall()
    priorities = {row['priority']: row['count'] for row in priority_rows}
    
    conn.close()
    
    return {
        'total': total,
        'completed': completed,
        'pending': pending,
        'rate': rate,
        'priorities': priorities
    }
