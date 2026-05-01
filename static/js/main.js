/**
 * BrainRot Quiz Engine (FINAL)
 */

class BrainRotQuiz {
    constructor(questions) {
        this.questions = questions;
        this.currentIndex = 0;
        this.answers = [];  
        this.categoryScores = {};
        this.categoryCounts = {};

        this.quizContainer = document.getElementById('quiz-flow');
        this.progressBar = document.querySelector('.progress-fill');
        this.timerBar = null;
        this.timerInterval = null;
        this.timeLimit = 5000; // 5 seconds

        this.engagementTexts = ["Analyzing attention... 🧠", "Tracking dopamine hits... ⚡", "Detecting NPC behavior... 🤖", "Measuring brain rot... 💀"];
        this.memeMoments = ["Bro is cooked 💀", "Focus left the chat 🏃", "TikTok ruined you 😭"];

        this.init();
    }

    init() {
        this.renderQuestion();
        this.updateProgress();
    }

    playSound(type) {
        if (localStorage.getItem('br_sound') === 'off') return;
        const audio = new Audio(`/static/assets/sounds/${type}.mp3`);
        audio.volume = 0.4;
        audio.play().catch(() => {});
    }

    renderQuestion() {
        const q = this.questions[this.currentIndex];

        clearInterval(this.timerInterval);

        // Engagement Text Logic
        let engagementHtml = '';
        if (this.currentIndex > 0 && this.currentIndex % 3 === 0) {
            engagementHtml = `<div class="engagement-text highlight" style="font-size: 0.9rem; margin-bottom: 10px; animation: fadeInOut 2s ease-in-out;">${this.engagementTexts[Math.floor(Math.random() * this.engagementTexts.length)]}</div>`;
        }

        let memeHtml = '';
        if (this.currentIndex === 7) {
             memeHtml = `<div class="meme-moment highlight" style="font-size: 1.2rem; color: #ff007f; margin-bottom: 15px;">${this.memeMoments[Math.floor(Math.random() * this.memeMoments.length)]}</div>`;
        }

        this.quizContainer.style.opacity = 0;
        this.quizContainer.style.transform = "scale(0.95)";

        setTimeout(() => {
            this.quizContainer.innerHTML = `
                <div class="question-card" style="transition: all 0.3s ease;">
                    <div class="quiz-header-info">
                        <span class="category-tag glow-effect">${q.category}</span>
                        <span class="question-counter" style="font-family: 'Press Start 2P', cursive; font-size: 0.7rem; color: #888;">Q: ${this.currentIndex + 1}/${this.questions.length}</span>
                    </div>

                    ${engagementHtml}
                    ${memeHtml}
                    
                    <h2 style="font-size: 1.8rem; margin-bottom: 25px; line-height: 1.3;">${q.question}</h2>

                    <!-- Timer Bar -->
                    <div class="timer-container" style="width: 100%; height: 6px; background: #222; border-radius: 10px; margin-bottom: 30px; overflow: hidden;">
                        <div id="quiz-timer" style="height: 100%; width: 100%; background: #00ffcc; transition: width 0.1s linear;"></div>
                    </div>

                    <div class="options-grid">
                        ${q.options.map(opt => `
                            <button class="option-btn pulse-hover"
                                onclick="quiz.handleAnswer(${opt.weight}, '${q.category}', this)">
                                ${opt.text}
                            </button>
                        `).join('')}
                    </div>
                </div>
            `;

            this.quizContainer.style.opacity = 1;
            this.quizContainer.style.transform = "scale(1)";
            
            this.startTimer(q.category);

        }, 200); // Fast transition
    }

    startTimer(category) {
        let timeLeft = this.timeLimit;
        const timerEl = document.getElementById('quiz-timer');
        
        this.timerInterval = setInterval(() => {
            timeLeft -= 100;
            if (timerEl) {
                timerEl.style.width = `${(timeLeft / this.timeLimit) * 100}%`;
                if (timeLeft < 2000) timerEl.style.background = '#ff007f'; // turn red
            }
            
            if (timeLeft <= 0) {
                clearInterval(this.timerInterval);
                this.playSound('wrong'); // buzzer for running out of time
                // Auto-answer with max brainrot (weight 1)
                this.answers.push(1);
                this.categoryScores[category] = (this.categoryScores[category] || 0) + 1;
                this.categoryCounts[category] = (this.categoryCounts[category] || 0) + 1;
                this.nextQuestion();
            }
        }, 100);
    }

    nextQuestion() {
        if (this.currentIndex < this.questions.length - 1) {
            this.currentIndex++;
            this.renderQuestion();
            this.updateProgress();
        } else {
            this.submitResults();
        }
    }

    handleAnswer(weight, category, btn) {
        clearInterval(this.timerInterval);
        this.playSound('click');

        // Visual Feedback
        btn.style.transform = "scale(0.95)";
        btn.style.background = "var(--neon-pink)";
        btn.style.color = "#fff";

        // Disable all buttons instantly
        document.querySelectorAll('.option-btn').forEach(b => b.disabled = true);

        // Save score
        this.answers.push(weight);
        this.categoryScores[category] = (this.categoryScores[category] || 0) + weight;
        this.categoryCounts[category] = (this.categoryCounts[category] || 0) + 1;

        // Fast auto-next
        setTimeout(() => {
            this.nextQuestion();
        }, 300);
    }

    updateProgress() {
        const progress = ((this.currentIndex + 1) / this.questions.length) * 100;
        if (this.progressBar) {
            this.progressBar.style.width = `${progress}%`;
        }
    }

    async submitResults() {
        this.playSound('wrong'); // Play wrong sound right before submitting final

        this.quizContainer.innerHTML = `
            <div class="analyzing-state" style="text-align: center; padding: 50px 0;">
                <h2 class="analyzing-title" style="margin-bottom: 20px;">Analyzing brain patterns… 🧠</h2>
                <div class="progress-container" style="width: 80%; margin: 0 auto; height: 10px; background: #222; border-radius: 10px; overflow: hidden;">
                    <div id="analyze-bar" style="height: 100%; width: 0%; background: #ff007f; transition: width 1.5s ease-out;"></div>
                </div>
            </div>
        `;

        setTimeout(() => {
            document.getElementById('analyze-bar').style.width = '100%';
        }, 50);

        const normalizedCategories = {};

        for (let cat in this.categoryScores) {
            normalizedCategories[cat] = Math.round(
                this.categoryScores[cat] / this.categoryCounts[cat]
            );
        }

        const username = localStorage.getItem('br_username') || "Anonymous";

        try {
            const response = await fetch('/submit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    username: username,
                    answers: this.answers,
                    categories: normalizedCategories
                })
            });

            const result = await response.json();

            localStorage.setItem('last_result', JSON.stringify(result));
            
            // Wait for fake analysis animation to finish
            setTimeout(() => {
                window.location.href = `/result?score=${result.score}&chart=${result.chart}`;
            }, 1500);

        } catch (err) {
            console.error("Submission failed:", err);
            this.quizContainer.innerHTML = '<h3>Error analyzing brain rot. You might be too far gone. Try refreshing.</h3>';
        }
    }
}


/* HOVER SOUND */
function playHoverSound() {
    if (localStorage.getItem('br_sound') === 'off') return;
    const audio = new Audio('/static/assets/sounds/hover.mp3');
    audio.volume = 0.2;
    audio.play().catch(() => {});
}


/* DOWNLOAD RESULT */
function downloadResult() {
    const link = document.createElement('a');
    link.href = document.getElementById('radar-chart').src;
    link.download = 'BrainRotScore.png';
    link.click();
}
