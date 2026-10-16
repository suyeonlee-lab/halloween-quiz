from flask import Flask, render_template, request, jsonify
import sqlite3
import json
import time

app = Flask(__name__)

# 데이터베이스 초기화 (응답 데이터 저장용)
def init_db():
    conn = sqlite3.connect('quiz_results.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            score INTEGER,
            total_time REAL,
            answers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 1. 메인 퀴즈 페이지
@app.route('/')
def index():
    return render_template('index.html')

# 2. 퀴즈 제출 및 데이터 저장 API
@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    user_name = data.get('user_name')
    score = data.get('score')
    total_time = data.get('total_time') # 초 단위
    answers = json.dumps(data.get('answers')) # [1, 3, 2, ...] 형태

    conn = sqlite3.connect('quiz_results.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO responses (user_name, score, total_time, answers)
        VALUES (?, ?, ?, ?)
    ''', (user_name, score, total_time, answers))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

# 3. 결과 분석 및 통계 API (관리자/통계용)
@app.route('/api/stats')
def get_stats():
    conn = sqlite3.connect('quiz_results.db')
    c = conn.cursor()
    c.execute('SELECT score, total_time, answers FROM responses')
    rows = c.fetchall()
    conn.close()

    total_count = len(rows)
    if total_count == 0:
        return jsonify({
            "total_count": 0,
            "avg_time": 0,
            "question_stats": {}
        })

    avg_time = round(sum(r[1] for r in rows) / total_count, 1)

    # 15개 문제별 선택지 응답 집계
    # answers_stat = { 1: {1: 5, 2: 10, ...}, 2: {...} }
    question_stats = {q: {1: 0, 2: 0, 3: 0, 4: 0} for q in range(1, 16)}

    for row in rows:
        ans_list = json.loads(row[2]) # [q1_ans, q2_ans, ...]
        for q_idx, selected_opt in enumerate(ans_list):
            q_num = q_idx + 1
            if q_num in question_stats and selected_opt in question_stats[q_num]:
                question_stats[q_num][selected_opt] += 1

    return jsonify({
        "total_count": total_count,
        "avg_time": avg_time,
        "question_stats": question_stats
    })

# 4. 통계 화면 페이지
@app.route('/admin')
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)