from datetime import datetime
from flask import Flask, render_template, request, jsonify
import database
import saju

app = Flask(__name__)

database.init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'app': '사주관리앱',
        'time': datetime.now().isoformat()
    })

def _with_saju(profile):
    pillars, elements = saju.calculate_saju(profile['birth_date'], profile.get('birth_time'))
    profile['pillars'] = pillars
    profile['elements'] = elements
    return profile

@app.route('/api/profiles', methods=['GET'])
def list_profiles():
    search = request.args.get('search', '')
    profiles = database.get_all_profiles(search=search)
    return jsonify([_with_saju(p) for p in profiles])

@app.route('/api/profiles', methods=['POST'])
def create_profile():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    birth_date = data.get('birth_date', '').strip()

    if not name:
        return jsonify({'error': '이름은 필수 입력 사항입니다.'}), 400
    if not birth_date:
        return jsonify({'error': '생년월일은 필수 입력 사항입니다.'}), 400

    gender = data.get('gender', '남').strip()
    birth_time = data.get('birth_time', '').strip() or None
    memo = data.get('memo', '').strip()

    try:
        saju.calculate_saju(birth_date, birth_time)
    except Exception:
        return jsonify({'error': '생년월일/시간 형식이 올바르지 않습니다.'}), 400

    new_profile = database.add_profile(name, gender, birth_date, birth_time, memo)
    return jsonify(_with_saju(new_profile)), 201

@app.route('/api/profiles/<int:profile_id>', methods=['GET'])
def get_profile(profile_id):
    profile = database.get_profile_by_id(profile_id)
    if not profile:
        return jsonify({'error': '해당 프로필을 찾을 수 없습니다.'}), 404
    return jsonify(_with_saju(profile))

@app.route('/api/profiles/<int:profile_id>', methods=['PUT'])
def update_profile(profile_id):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    birth_date = data.get('birth_date', '').strip()

    if not name:
        return jsonify({'error': '이름은 필수 입력 사항입니다.'}), 400
    if not birth_date:
        return jsonify({'error': '생년월일은 필수 입력 사항입니다.'}), 400

    gender = data.get('gender', '남').strip()
    birth_time = data.get('birth_time', '').strip() or None
    memo = data.get('memo', '').strip()

    try:
        saju.calculate_saju(birth_date, birth_time)
    except Exception:
        return jsonify({'error': '생년월일/시간 형식이 올바르지 않습니다.'}), 400

    updated = database.update_profile(profile_id, name, gender, birth_date, birth_time, memo)
    if not updated:
        return jsonify({'error': '해당 프로필을 찾을 수 없습니다.'}), 404
    return jsonify(_with_saju(updated))

@app.route('/api/profiles/<int:profile_id>', methods=['DELETE'])
def delete_profile(profile_id):
    success = database.delete_profile(profile_id)
    if not success:
        return jsonify({'error': '해당 프로필을 찾을 수 없습니다.'}), 404
    return jsonify({'success': True, 'id': profile_id})

@app.route('/api/stats', methods=['GET'])
def stats():
    return jsonify(database.get_stats())

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
