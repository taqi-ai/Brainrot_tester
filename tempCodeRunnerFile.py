import os
import json
import uuid
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg') # Thread-safe for web apps
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

# --- OOP LOGIC ---

class ResultAnalyzer:
    def __init__(self, scores, categories):
        self.scores = np.array(scores)
        self.categories = categories

    def calculate_total(self):
        # Normalize score to 0-100 using NumPy
        return int(np.mean(self.scores))

    def generate_radar_chart(self, filename):
        labels = list(self.categories.keys())
        values = list(self.categories.values())
        
        # Close the loop for radar chart
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor('#0a0a0a')
        ax.set_facecolor('#111')

        # Draw plot
        ax.fill(angles, values, color='#ff007f', alpha=0.25)
        ax.plot(angles, values, color='#ff007f', linewidth=2)

        # Labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, color='white', size=10)
        ax.set_yticklabels([]) # Hide radial labels
        ax.spines['polar'].set_color('#333')
        
        chart_path = os.path.join('static/charts', filename)
        plt.savefig(chart_path, transparent=True)
        plt.close()
        return filename

class LeaderboardManager:
    def __init__(self, file_path):
        self.file_path = file_path

    def add_score(self, name, score):
        df = pd.read_csv(self.file_path)
        new_entry = pd.DataFrame([[name, score]], columns=['Name', 'Score'])
        df = pd.concat([df, new_entry], ignore_index=True)
        df = df.sort_values(by='Score', ascending=False).head(10)
        df.to_csv(self.file_path, index=False)

    def get_top_10(self):
        return pd.read_csv(self.file_path).to_dict(orient='records')

# --- UTILS ---

def load_json(path):
    with open(os.path.join('data', path), 'r') as f:
        return json.load(f)

# --- ROUTES ---

@app.route('/')
def index():
    config = load_json('config.json')
    lb = LeaderboardManager('data/leaderboard.csv')
    return render_template('index.html', config=config, leaderboard=lb.get_top_10())

@app.route('/quiz')
def quiz():
    questions = load_json('questions.json')
    return render_template('quiz.html', questions=questions)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    username = data.get('username', 'Anonymous')
    answers = data.get('answers') # List of point values
    category_scores = data.get('categories') # Dict of category: score

    analyzer = ResultAnalyzer(answers, category_scores)
    final_score = analyzer.calculate_total()
    
    chart_file = f"chart_{uuid.uuid4().hex}.png"
    analyzer.generate_radar_chart(chart_file)

    lb = LeaderboardManager('data/leaderboard.csv')
    lb.add_score(username, final_score)

    # Determine meme based on score
    memes = load_json('memes.json')
    selected_meme = next(m for m in memes if final_score >= m['min_score'])

    return jsonify({
        "score": final_score,
        "chart": chart_file,
        "meme": selected_meme
    })

if __name__ == '__main__':
    app.run(debug=True)