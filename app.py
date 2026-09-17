import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import database

app = Flask(__name__)

# Initialize SQLite database schema & sample data
database.init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'app': 'Flask To-Do Application',
        'time': datetime.now().isoformat()
    })

@app.route('/api/todos', methods=['GET'])
def list_todos():
    status = request.args.get('status', 'all')
    category = request.args.get('category', 'all')
    priority = request.args.get('priority', 'all')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'due_date')
    
    todos = database.get_all_todos(
        status=status,
        category=category,
        priority=priority,
        search=search,
        sort_by=sort_by
    )
    return jsonify(todos)

@app.route('/api/todos', methods=['POST'])
def create_todo():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    
    if not title:
        return jsonify({'error': '제목은 필수 입력 사항입니다.'}), 400
        
    description = data.get('description', '').strip()
    category = data.get('category', '업무').strip()
    priority = data.get('priority', '보통').strip()
    due_date = data.get('due_date', '').strip() or None
    
    new_todo = database.add_todo(title, description, category, priority, due_date)
    return jsonify(new_todo), 201

@app.route('/api/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    todo = database.get_todo_by_id(todo_id)
    if not todo:
        return jsonify({'error': '해당 할일을 찾을 수 없습니다.'}), 404
    return jsonify(todo)

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': '제목은 필수 입력 사항입니다.'}), 400
        
    description = data.get('description', '').strip()
    category = data.get('category', '업무').strip()
    priority = data.get('priority', '보통').strip()
    due_date = data.get('due_date', '').strip() or None
    completed = 1 if data.get('completed') else 0
    
    updated = database.update_todo(todo_id, title, description, category, priority, due_date, completed)
    if not updated:
        return jsonify({'error': '해당 할일을 찾을 수 없습니다.'}), 404
    return jsonify(updated)

@app.route('/api/todos/<int:todo_id>/toggle', methods=['PATCH'])
def toggle_todo_status(todo_id):
    toggled = database.toggle_todo(todo_id)
    if not toggled:
        return jsonify({'error': '해당 할일을 찾을 수 없습니다.'}), 404
    return jsonify(toggled)

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    success = database.delete_todo(todo_id)
    if not success:
        return jsonify({'error': '해당 할일을 찾을 수 없습니다.'}), 404
    return jsonify({'success': True, 'id': todo_id})

@app.route('/api/stats', methods=['GET'])
def stats():
    return jsonify(database.get_stats())

if __name__ == '__main__':
    # Listen on localhost port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
