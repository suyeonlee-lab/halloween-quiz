from flask import Flask, render_template, request, jsonify
import sqlite3
import json

app = Flask(__name__)

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    user_name = data.get('user_name')
    score = data.get('score')
    total_time = data.get('total_time')
    answers = json.dumps(data.get('answers'))

    conn = sqlite3.connect('quiz_results.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO responses (user_name, score, total_time, answers)
        VALUES (?, ?, ?, ?)
    ''', (user_name, score, total_time, answers))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

@app.route('/api/stats')
def get_stats():
    conn = sqlite3.connect('quiz_results.db')
    c = conn.cursor()
    c.execute('SELECT user_name, score, total_time, answers, created_at FROM responses ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()

    total_count = len(rows)
    if total_count == 0:
        return jsonify({
            "total_count": 0,
            "avg_time": 0,
            "question_stats": {},
            "user_responses": []
        })

    avg_time = round(sum(r[2] for r in rows) / total_count, 1)

    # 10문제 집계 (1번부터 10번 문제까지)
    question_stats = {q: {1: 0, 2: 0, 3: 0, 4: 0} for q in range(1, 11)}
    user_responses = []

    for row in rows:
        u_name, score, t_time, ans_json, created_at = row
        ans_list = json.loads(ans_json) if ans_json else []

        for q_idx, selected_opt in enumerate(ans_list):
            q_num = q_idx + 1
            if q_num in question_stats and selected_opt in question_stats[q_num]:
                question_stats[q_num][selected_opt] += 1

        user_responses.append({
            "name": u_name,
            "score": score,
            "time": t_time,
            "answers": ans_list,
            "date": created_at
        })

    return jsonify({
        "total_count": total_count,
        "avg_time": avg_time,
        "question_stats": question_stats,
        "user_responses": user_responses
    })

@app.route('/admin')
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
