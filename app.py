import os
import json
import uuid
import random
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


# =========================
# OOP: RESULT ANALYZER
# =========================

class ResultAnalyzer:
    def __init__(self, scores, categories):
        self.scores = np.array(scores)
        self.categories = categories

    def calculate_total(self):
        if len(self.scores) == 0:
            return 0
        return int(np.sum(self.scores))

    def generate_radar_chart(self, filename):
        if not self.categories:
            self.categories = {"Unknown": 0}
            
        labels = list(self.categories.keys())
        values = list(self.categories.values())

        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor('#0a0a0a')
        ax.set_facecolor('#111')

        ax.fill(angles, values, color='#ff007f', alpha=0.25)
        ax.plot(angles, values, color='#ff007f', linewidth=2)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, color='white', size=10)
        ax.set_yticklabels([])
        ax.spines['polar'].set_color('#333')

        chart_path = os.path.join('static', 'charts', filename)
        os.makedirs(os.path.dirname(chart_path), exist_ok=True)
        plt.savefig(chart_path, transparent=True)
        plt.close()

        return filename


# =========================
# OOP: LEADERBOARD
# =========================

from datetime import datetime

class LeaderboardManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self._ensure_monthly_refresh()

    def _ensure_monthly_refresh(self):
        current_month = datetime.now().strftime("%Y-%m")
        meta_path = self.file_path + ".meta"
        
        last_refresh = ""
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                last_refresh = f.read().strip()
        
        if last_refresh != current_month:
            # Reset leaderboard for the new month
            df = pd.DataFrame(columns=['Name', 'Score'])
            df.to_csv(self.file_path, index=False)
            with open(meta_path, 'w') as f:
                f.write(current_month)

    def add_score(self, name, score):
        self._ensure_monthly_refresh()
        try:
            df = pd.read_csv(self.file_path)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df = pd.DataFrame(columns=['Name', 'Score'])
            
        new_entry = pd.DataFrame([[name, score]], columns=['Name', 'Score'])
        df = pd.concat([df, new_entry], ignore_index=True)
        # Sort by score descending (higher is better? User said sigma focus god is 35-40, brainrot zombie is 10-18. So higher score = better focus.)
        # Actually in brainrot app, usually higher score = more brainrot.
        # But user said A=1, B=2, C=3, D=4. D is Sigma Focus God (low brainrot).
        # So score 40 = 0% brainrot. Score 10 = 100% brainrot.
        # If it's a "Brainrot Score", 40 should be the "best" in terms of sigma, but 10 is "best" in terms of brainrot.
        # Usually leaderboards show the "best" performers. 
        # User said "Sigma Focus God" is the top tier. So higher score is better.
        df = df.sort_values(by='Score', ascending=False).head(10)
        df.to_csv(self.file_path, index=False)

    def get_top_10(self):
        self._ensure_monthly_refresh()
        try:
            return pd.read_csv(self.file_path).to_dict(orient='records')
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return []


# =========================
# UTIL
# =========================

def load_json(path):
    with open(os.path.join('data', path), 'r', encoding='utf-8') as f:
        return json.load(f)


# =========================
# ROUTES
# =========================

@app.route('/')
def index():
    config = load_json('config.json')
    lb = LeaderboardManager('data/leaderboard.csv')
    return render_template('index.html', config=config, leaderboard=lb.get_top_10())


@app.route('/quiz')
def quiz():
    questions = load_json('questions.json')
    return render_template('quiz.html', questions=questions)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/signin')
def signin():
    return render_template('signin.html')

@app.route('/result')
def result():
    score = request.args.get('score', 0)
    chart = request.args.get('chart', '')
    
    memes = load_json('memes.json')
    try:
        score_val = int(score)
    except ValueError:
        score_val = 0
        
    selected_meme = max(
        (m for m in memes if score_val >= m['min_score']),
        key=lambda x: x['min_score']
    )
    
    roast = random.choice(selected_meme["roasts"])
    # Just grab all the poetry lines from the array (it's 2 lines now)
    poetry_lines = selected_meme["poetry"]

    final_meme = {
        "label": selected_meme["label"],
        "roast": roast,
        "poetry": "\n".join(poetry_lines),
        "sound": selected_meme["sound"]
    }

    brainrot_pct = max(0, min(100, int(((40 - score_val) / 30.0) * 100)))

    return render_template('result.html', score=score, chart=chart, meme=final_meme, pct=brainrot_pct)


@app.route('/submit', methods=['POST'])
def submit():
    data = request.json

    username = data.get('username', 'Anonymous')
    answers = data.get('answers', [])
    category_scores = data.get('categories', {})

    analyzer = ResultAnalyzer(answers, category_scores)
    final_score = analyzer.calculate_total()

    chart_file = f"chart_{uuid.uuid4().hex}.png"
    analyzer.generate_radar_chart(chart_file)

    # Leaderboard update
    lb = LeaderboardManager('data/leaderboard.csv')
    lb.add_score(username, final_score)

    # Load memes (tiers)
    memes = load_json('memes.json')

    # ✅ CORRECT tier selection (highest min_score match)
    selected_meme = max(
        (m for m in memes if final_score >= m['min_score']),
        key=lambda x: x['min_score']
    )

    # ✅ RANDOMIZATION
    roast = random.choice(selected_meme["roasts"])
    poetry_lines = random.sample(selected_meme["poetry"], 2)

    # Pack final meme object
    final_meme = {
        "label": selected_meme["label"],
        "roast": roast,
        "poetry": "\n".join(poetry_lines),
        "sound": selected_meme["sound"]
    }

    return jsonify({
        "score": final_score,
        "chart": chart_file,
        "meme": final_meme
    })


# =========================
# RUN
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)