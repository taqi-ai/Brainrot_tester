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
        # Load scoring configuration (max score range and tier definitions)
        config_path = os.path.join('data', 'score_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.raw_max_score = self.config.get('raw_max_score', 40)
        self.max_score = self.config.get('max_score', 100)

    def calculate_total(self):
        if len(self.scores) == 0:
            return 0
        return int(np.sum(self.scores))

    def scaled_total(self, raw_total: int) -> int:
        """Scale raw total to the configured max_score range."""
        if self.raw_max_score == 0:
            return 0
        return int(round(raw_total * (self.max_score / self.raw_max_score)))

    def percentage(self, score: int, is_scaled: bool = False) -> int:
        """Compute brainrot percentage where 0% = perfect focus (max_score) and 100% = worst (0)."""
        scaled = score if is_scaled else self.scaled_total(score)
        return int(max(0, min(100, ((self.max_score - scaled) / self.max_score) * 100)))

    def tier_for_score(self, score: int, is_scaled: bool = False):
        """Return the tier dict matching the current percentage."""
        pct = self.percentage(score, is_scaled=is_scaled)
        for tier in self.config.get('tiers', []):
            if tier['min_pct'] <= pct <= tier['max_pct']:
                return tier
        return self.config.get('tiers', [])[-1]



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

        # Fix auto-scaling so max radius is always 4 (max option weight)
        ax.set_ylim(0, 4)

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
    
    # Select 10 random questions if the pool is larger than 10
    if len(questions) > 10:
        questions = random.sample(questions, 10)
        
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

    # Use new scoring config to determine tier and percentage
    analyzer_dummy = ResultAnalyzer([], {})
    tier = analyzer_dummy.tier_for_score(score_val, is_scaled=True)
    brainrot_pct = analyzer_dummy.percentage(score_val, is_scaled=True)

    # Find meme block matching the tier label
    selected_meme = next((m for m in memes if m['label'] == tier['label']), None)
    if not selected_meme:
        selected_meme = memes[0]

    roast = random.choice(selected_meme["roasts"])
    # Randomly pick up to two poetry lines
    poetry_lines = random.sample(selected_meme["poetry"], min(2, len(selected_meme["poetry"])) )

    final_meme = {
        "label": selected_meme["label"],
        "roast": roast,
        "poetry": "\n".join(poetry_lines),
        "sound": selected_meme["sound"]
    }

    return render_template('result.html', score=score, chart=chart, meme=final_meme, pct=brainrot_pct, max_score=analyzer_dummy.max_score)


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

    # Load memes (tiers)
    memes = load_json('memes.json')

    # Use new scoring config to determine tier and percentage
    tier = analyzer.tier_for_score(final_score)
    brainrot_pct = analyzer.percentage(final_score)

    # Find meme block matching the tier label
    selected_meme = next((m for m in memes if m['label'] == tier['label']), None)
    if not selected_meme:
        selected_meme = memes[0]

    # ✅ RANDOMIZATION
    roast = random.choice(selected_meme["roasts"])
    poetry_lines = random.sample(selected_meme["poetry"], min(2, len(selected_meme["poetry"])) )

    # Pack final meme object
    final_meme = {
        "label": selected_meme["label"],
        "roast": roast,
        "poetry": "\n".join(poetry_lines),
        "sound": selected_meme["sound"]
    }

    # Store scaled score in leaderboard instead of raw if needed
    scaled_score = analyzer.scaled_total(final_score)
    lb = LeaderboardManager('data/leaderboard.csv')
    lb.add_score(username, scaled_score)

    return jsonify({
        "score": scaled_score,
        "chart": chart_file,
        "meme": final_meme
    })


# =========================
# RUN
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
