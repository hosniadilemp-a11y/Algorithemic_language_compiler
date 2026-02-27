class QuizController {
    constructor(courseController) {
        this.course = courseController;
        this.quizData = [];
        this.currentQuestionIndex = 0;
        this.score = 0;
        this.conceptAnalysis = {};

        this.modal = null;
        this.initDOM();
    }

    initDOM() {
        // Create Quiz Modal Container
        this.modal = document.createElement('div');
        this.modal.className = 'quiz-modal';
        this.modal.innerHTML = `
            <div class="quiz-modal-content">
                <div class="quiz-header">
                    <div class="quiz-progress-text">Question <span id="quiz-current-num">1</span> / <span id="quiz-total-num">20</span></div>
                    <div class="quiz-progress-bar"><div id="quiz-progress-fill"></div></div>
                    <button class="quiz-close-btn"><i class="fas fa-times"></i></button>
                </div>
                <div id="quiz-body" class="quiz-body">
                    <!-- Dynamic Content -->
                </div>
                <div class="quiz-footer">
                    <button id="quiz-next-btn" class="quiz-btn primary" disabled>Question suivante <i class="fas fa-arrow-right"></i></button>
                    <button id="quiz-finish-btn" class="quiz-btn success" style="display: none;">Voir les résultats <i class="fas fa-chart-pie"></i></button>
                </div>
            </div>
        `;
        document.body.appendChild(this.modal);

        this.modal.querySelector('.quiz-close-btn').addEventListener('click', () => this.closeQuiz());
        this.modal.querySelector('#quiz-next-btn').addEventListener('click', () => this.nextQuestion());
        this.modal.querySelector('#quiz-finish-btn').addEventListener('click', () => this.showResults());
    }

    async startQuiz(chapterIdentifier, chapterTitle) {
        this.chapterIdentifier = chapterIdentifier;
        this.chapterTitle = chapterTitle;
        this.currentQuestionIndex = 0;
        this.score = 0;
        this.conceptAnalysis = {};

        const body = this.modal.querySelector('#quiz-body');
        body.innerHTML = `<div class="quiz-loading"><i class="fas fa-circle-notch fa-spin"></i> Chargement du quiz...</div>`;
        this.modal.classList.add('active');

        try {
            const response = await fetch(`/api/quiz/${chapterIdentifier}`);
            const data = await response.json();

            if (data.error) throw new Error(data.error);

            this.quizData = data.questions;
            if (this.quizData.length === 0) {
                body.innerHTML = `<div class="quiz-error">Aucune question disponible pour ce chapitre.</div>`;
                return;
            }

            // Initialize Analysis Trackers
            this.quizData.forEach(q => {
                if (!this.conceptAnalysis[q.concept]) {
                    this.conceptAnalysis[q.concept] = { total: 0, correct: 0 };
                }
                this.conceptAnalysis[q.concept].total += 1;
            });

            this.modal.querySelector('#quiz-total-num').textContent = this.quizData.length;
            this.renderQuestion();

        } catch (error) {
            body.innerHTML = `<div class="quiz-error">Erreur de chargement: ${error.message}</div>`;
        }
    }

    renderQuestion() {
        const q = this.quizData[this.currentQuestionIndex];
        const body = this.modal.querySelector('#quiz-body');
        const progressFill = this.modal.querySelector('#quiz-progress-fill');
        const nextBtn = this.modal.querySelector('#quiz-next-btn');
        const finishBtn = this.modal.querySelector('#quiz-finish-btn');

        // Update Progress
        this.modal.querySelector('#quiz-current-num').textContent = this.currentQuestionIndex + 1;
        progressFill.style.width = `${((this.currentQuestionIndex) / this.quizData.length) * 100}%`;

        // Buttons state
        nextBtn.style.display = this.currentQuestionIndex === this.quizData.length - 1 ? 'none' : 'inline-block';
        nextBtn.disabled = true;
        finishBtn.style.display = this.currentQuestionIndex === this.quizData.length - 1 ? 'inline-block' : 'none';
        finishBtn.disabled = true;

        // Difficulty Badges
        const diffColors = {
            'Easy': '<span class="quiz-badge badge-easy">Facile</span>',
            'Medium': '<span class="quiz-badge badge-medium">Moyen</span>',
            'Hard': '<span class="quiz-badge badge-hard">Difficile</span>'
        };

        let choicesHtml = q.choices.map(c => `
            <button class="quiz-choice" data-id="${c.id}" data-correct="${c.is_correct}">
                <div class="quiz-choice-text">${this.escapeHtml(c.text)}</div>
                <div class="quiz-choice-icon"><i class="fas fa-circle"></i></div>
            </button>
        `).join('');

        body.innerHTML = `
            <div class="quiz-question-meta">
                ${diffColors[q.difficulty]}
                <span class="quiz-badge badge-concept">${q.concept}</span>
            </div>
            <h3 class="quiz-question-text">${this.escapeHtml(q.text)}</h3>
            <div class="quiz-choices-container">
                ${choicesHtml}
            </div>
            <div id="quiz-feedback" class="quiz-feedback" style="display: none;">
                <div class="quiz-feedback-icon"></div>
                <div class="quiz-feedback-content">
                    <h4 class="quiz-feedback-title"></h4>
                    <p class="quiz-feedback-expl">${this.escapeHtml(q.explanation)}</p>
                </div>
            </div>
        `;

        // Bind Choices
        const choiceBtns = body.querySelectorAll('.quiz-choice');
        choiceBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleAnswer(e.currentTarget, choiceBtns, q));
        });

        // Render markdown in code chunks if any
        this.formatCodeInQuiz(body);
    }

    handleAnswer(selectedBtn, allBtns, questionData) {
        // Disable all buttons to prevent double answers
        allBtns.forEach(b => b.disabled = true);

        const isCorrect = selectedBtn.dataset.correct === 'true';
        const feedback = this.modal.querySelector('#quiz-feedback');
        const fTitle = feedback.querySelector('.quiz-feedback-title');
        const fIcon = feedback.querySelector('.quiz-feedback-icon');

        if (isCorrect) {
            this.score++;
            this.conceptAnalysis[questionData.concept].correct++;
            selectedBtn.classList.add('correct');
            selectedBtn.querySelector('.quiz-choice-icon i').className = 'fas fa-check-circle';

            feedback.className = 'quiz-feedback feedback-success';
            fIcon.innerHTML = '<i class="fas fa-check"></i>';
            fTitle.textContent = 'Excellente réponse !';
        } else {
            selectedBtn.classList.add('wrong');
            selectedBtn.querySelector('.quiz-choice-icon i').className = 'fas fa-times-circle';

            // Highlight the correct one
            allBtns.forEach(b => {
                if (b.dataset.correct === 'true') {
                    b.classList.add('correct-missed');
                    b.querySelector('.quiz-choice-icon i').className = 'fas fa-check-circle';
                }
            });

            feedback.className = 'quiz-feedback feedback-error';
            fIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
            fTitle.textContent = 'Incorrect';
        }

        feedback.style.display = 'flex';

        // Enable Next/Finish btn
        if (this.currentQuestionIndex === this.quizData.length - 1) {
            this.modal.querySelector('#quiz-finish-btn').disabled = false;
        } else {
            this.modal.querySelector('#quiz-next-btn').disabled = false;
        }
    }

    nextQuestion() {
        this.currentQuestionIndex++;
        this.renderQuestion();
    }

    async showResults() {
        // Save progress to backend
        try {
            await fetch('/api/quiz/save_progress', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    chapter_identifier: this.chapterIdentifier,
                    score: this.score,
                    total: this.quizData.length,
                    details: this.conceptAnalysis
                })
            });
        } catch (e) {
            console.error("Failed to save progress", e);
        }

        const body = this.modal.querySelector('#quiz-body');
        this.modal.querySelector('.quiz-progress-text').textContent = "Résultats";
        this.modal.querySelector('#quiz-progress-fill').style.width = '100%';
        this.modal.querySelector('.quiz-footer').style.display = 'none';

        const percentage = Math.round((this.score / this.quizData.length) * 100);
        let message = '';
        let colorClass = '';

        if (percentage >= 80) {
            message = 'Félicitations ! Vous maîtrisez ce chapitre. 🏆';
            colorClass = 'res-excellent';
        } else if (percentage >= 50) {
            message = 'Bon travail ! Quelques petites révisions et ce sera parfait. 📚';
            colorClass = 'res-good';
        } else {
            message = 'Ne vous découragez pas. Relisez le cours attentivement et réessayez ! 💪';
            colorClass = 'res-needs-work';
        }

        // Generate Analysis HTML
        let analysisHtml = Object.keys(this.conceptAnalysis).map(concept => {
            const stat = this.conceptAnalysis[concept];
            const perc = Math.round((stat.correct / stat.total) * 100);
            return `
                <div class="analysis-row">
                    <div class="analysis-lbl">${concept}</div>
                    <div class="analysis-bar-bg">
                        <div class="analysis-bar-fill" style="width: ${perc}%; background: ${this.getColorForPerc(perc)}"></div>
                    </div>
                    <div class="analysis-val">${stat.correct}/${stat.total}</div>
                </div>
            `;
        }).join('');

        body.innerHTML = `
            <div class="quiz-results-container">
                <div class="quiz-score-circle ${colorClass}">
                    <span class="score-val">${this.score}</span>
                    <span class="score-max">/ ${this.quizData.length}</span>
                </div>
                <h2 class="quiz-res-msg">${message}</h2>
                
                <div class="quiz-analysis-box">
                    <h3>Analyse par concept</h3>
                    ${analysisHtml}
                </div>

                <div class="quiz-res-actions">
                    <button class="quiz-btn outline" onclick="window.quizController.startQuiz('${this.chapterIdentifier}', '${this.chapterTitle}')"><i class="fas fa-redo"></i> Refaire le test</button>
                    <button class="quiz-btn primary" onclick="window.quizController.closeQuiz()"><i class="fas fa-book"></i> Retourner au cours</button>
                </div>
            </div>
        `;
    }

    getColorForPerc(perc) {
        if (perc >= 80) return '#2ea44e';
        if (perc >= 50) return '#d29922';
        return '#f85149';
    }

    closeQuiz() {
        this.modal.classList.remove('active');
        setTimeout(() => this.modal.querySelector('.quiz-footer').style.display = 'flex', 300);
        // Refresh course if needed, or simply return visually
        if (this.course) {
            // Maybe reset scroll or do something
        }
    }

    escapeHtml(text) {
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    formatCodeInQuiz(container) {
        // Quick hack to format backticks as code blocks inside quiz text/choices
        const elements = container.querySelectorAll('.quiz-question-text, .quiz-choice-text, .quiz-feedback-expl');
        elements.forEach(el => {
            let html = el.innerHTML;
            html = html.replace(/`(.*?)`/g, '<code class="quiz-inline-code">$1</code>');
            el.innerHTML = html;
        });
    }
}
