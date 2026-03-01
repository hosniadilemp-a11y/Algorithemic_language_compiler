class QuizController {
    constructor(courseController) {
        this.course = courseController;
        this.quizData = [];
        this.currentQuestionIndex = 0;
        this.score = 0;
        this.conceptAnalysis = {};
        this.userAnswers = [];

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
                    <div class="quiz-progress-text">Test - Question <span id="quiz-current-num">1</span> / <span id="quiz-total-num">20</span></div>
                    <div class="quiz-progress-bar" style="display:none;"><div id="quiz-progress-fill"></div></div>
                    <div id="quiz-bubbles" class="quiz-bubbles"></div>
                    <button class="quiz-close-btn"><i class="fas fa-times"></i></button>
                </div>
                <div id="quiz-body" class="quiz-body">
                    <!-- Dynamic Content -->
                </div>
                <div class="quiz-footer">
                    <button id="quiz-prev-btn" class="quiz-btn secondary" disabled><i class="fas fa-arrow-left"></i> Précédent</button>
                    <button id="quiz-next-btn" class="quiz-btn primary">Question suivante <i class="fas fa-arrow-right"></i></button>
                    <button id="quiz-finish-btn" class="quiz-btn success" style="display: none;">Voir les résultats <i class="fas fa-chart-pie"></i></button>
                </div>
            </div>
        `;
        document.body.appendChild(this.modal);

        this.modal.querySelector('.quiz-close-btn').addEventListener('click', () => this.closeQuiz());
        this.modal.querySelector('#quiz-prev-btn').addEventListener('click', () => this.prevQuestion());
        this.modal.querySelector('#quiz-next-btn').addEventListener('click', () => this.nextQuestion());
        this.modal.querySelector('#quiz-finish-btn').addEventListener('click', () => this.showResults());
    }

    async startQuiz(chapterIdentifier, chapterTitle) {
        this.chapterIdentifier = chapterIdentifier;
        this.chapterTitle = chapterTitle;
        this.currentQuestionIndex = 0;
        this.score = 0;
        this.conceptAnalysis = {};
        this.userAnswers = [];

        const body = this.modal.querySelector('#quiz-body');
        body.innerHTML = `<div class="quiz-loading"><i class="fas fa-circle-notch fa-spin"></i> Chargement du test...</div>`;
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

            this.userAnswers = new Array(this.quizData.length).fill(null);

            this.modal.querySelector('#quiz-total-num').textContent = this.quizData.length;
            this.renderBubbles();
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
        const currentNum = this.modal.querySelector('#quiz-current-num');
        if (currentNum) currentNum.textContent = this.currentQuestionIndex + 1;

        if (progressFill) progressFill.style.width = `${((this.currentQuestionIndex) / this.quizData.length) * 100}%`;

        // Buttons state
        if (nextBtn) {
            nextBtn.style.display = this.currentQuestionIndex === this.quizData.length - 1 ? 'none' : 'inline-block';
            nextBtn.disabled = true;
        }
        if (finishBtn) {
            finishBtn.style.display = this.currentQuestionIndex === this.quizData.length - 1 ? 'inline-block' : 'none';
            finishBtn.disabled = true;
        }

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

        // Update Bubbles visual state to highlight current
        this.updateBubblesUI();

        const choiceBtns = body.querySelectorAll('.quiz-choice');
        const feedback = this.modal.querySelector('#quiz-feedback');

        // Check if already answered
        const previousAnswer = this.userAnswers[this.currentQuestionIndex];

        if (previousAnswer !== null) {
            // Reconstruct the answered state
            choiceBtns.forEach(btn => {
                btn.disabled = true;
                if (btn.dataset.id === String(previousAnswer.id)) {
                    if (previousAnswer.isCorrect) {
                        btn.classList.add('correct');
                        btn.querySelector('.quiz-choice-icon i').className = 'fas fa-check-circle';
                    } else {
                        btn.classList.add('wrong');
                        btn.querySelector('.quiz-choice-icon i').className = 'fas fa-times-circle';
                    }
                }
                // Highlight the correct one if they missed it
                if (!previousAnswer.isCorrect && btn.dataset.correct === 'true') {
                    btn.classList.add('correct-missed');
                    btn.querySelector('.quiz-choice-icon i').className = 'fas fa-check-circle';
                }
            });

            const fTitle = feedback.querySelector('.quiz-feedback-title');
            const fIcon = feedback.querySelector('.quiz-feedback-icon');
            if (previousAnswer.isCorrect) {
                feedback.className = 'quiz-feedback feedback-success';
                fIcon.innerHTML = '<i class="fas fa-check"></i>';
                fTitle.textContent = 'Excellente réponse !';
            } else {
                feedback.className = 'quiz-feedback feedback-error';
                fIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                fTitle.textContent = 'Incorrect';
            }
            feedback.style.display = 'flex';
        } else {
            // Bind Choices if not answered yet
            choiceBtns.forEach(btn => {
                btn.addEventListener('click', (e) => this.handleAnswer(e.currentTarget, choiceBtns, q));
            });
        }

        // Navigation state
        const prevBtn = this.modal.querySelector('#quiz-prev-btn');
        if (prevBtn) prevBtn.disabled = this.currentQuestionIndex === 0;

        if (this.currentQuestionIndex === this.quizData.length - 1) {
            if (nextBtn) nextBtn.style.display = 'none';
            if (finishBtn) finishBtn.style.display = 'inline-block';
            if (finishBtn) finishBtn.disabled = this.userAnswers.includes(null); // Must answer all
        } else {
            if (nextBtn) nextBtn.style.display = 'inline-block';
            if (finishBtn) finishBtn.style.display = 'none';
            if (nextBtn) nextBtn.disabled = false;
        }

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

        // Save the user answer
        this.userAnswers[this.currentQuestionIndex] = {
            id: selectedBtn.dataset.id,
            isCorrect: isCorrect
        };

        this.updateBubblesUI();

        // Enable Next/Finish btn if disabled
        if (this.currentQuestionIndex === this.quizData.length - 1) {
            this.modal.querySelector('#quiz-finish-btn').disabled = this.userAnswers.includes(null);
        }
    }

    renderBubbles() {
        const container = this.modal.querySelector('#quiz-bubbles');
        container.innerHTML = '';
        for (let i = 0; i < this.quizData.length; i++) {
            const bubble = document.createElement('div');
            bubble.className = 'quiz-bubble';
            bubble.dataset.index = i;
            // Let user click bubble to navigate
            bubble.addEventListener('click', () => {
                this.currentQuestionIndex = i;
                this.renderQuestion();
            });
            container.appendChild(bubble);
        }
    }

    updateBubblesUI() {
        const bubbles = this.modal.querySelectorAll('.quiz-bubble');
        bubbles.forEach((bubble, index) => {
            bubble.className = 'quiz-bubble'; // reset
            if (index === this.currentQuestionIndex) {
                bubble.classList.add('current');
            }
            if (this.userAnswers[index] !== null) {
                if (this.userAnswers[index].isCorrect) {
                    bubble.classList.add('correct-answer');
                } else {
                    bubble.classList.add('wrong-answer');
                }
            }
        });
    }

    prevQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.currentQuestionIndex--;
            this.renderQuestion();
        }
    }

    nextQuestion() {
        if (this.currentQuestionIndex < this.quizData.length - 1) {
            this.currentQuestionIndex++;
            this.renderQuestion();
        }
    }

    async showResults() {
        let progressSnapshot = null;
        const passThreshold = 70;
        const percentage = Math.round((this.score / this.quizData.length) * 100);
        const chapterPassed = percentage >= passThreshold;
        let saveSucceeded = false;

        // Save progress to backend
        try {
            const response = await fetch('/api/quiz/save_progress', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    chapter_identifier: this.chapterIdentifier,
                    score: this.score,
                    total: this.quizData.length,
                    details: this.conceptAnalysis
                })
            });

            const data = await response.json();
            if (response.ok && data && data.snapshot) {
                saveSucceeded = true;
                progressSnapshot = data.snapshot;
                this.persistProgressSnapshotCookie(progressSnapshot);
                this.emitProgressUpdate(progressSnapshot);
            }
        } catch (e) {
            console.error("Failed to save progress", e);
        }

        // Always sync snapshot from backend as source of truth.
        const syncedSnapshot = await this.fetchProgressSnapshot();
        if (syncedSnapshot) {
            progressSnapshot = syncedSnapshot;
        }

        // Last resort: optimistic local update so learner sees immediate change.
        if (!progressSnapshot) {
            progressSnapshot = this.buildOptimisticSnapshot(percentage, passThreshold);
            if (progressSnapshot) {
                this.persistProgressSnapshotCookie(progressSnapshot);
                this.emitProgressUpdate(progressSnapshot);
            }
        }

        if (!saveSucceeded && !progressSnapshot) {
            progressSnapshot = await this.fetchProgressSnapshot();
        }

        const body = this.modal.querySelector('#quiz-body');
        const progressText = this.modal.querySelector('.quiz-progress-text');
        if (progressText) progressText.textContent = "Résultats";
        const progressFill = this.modal.querySelector('#quiz-progress-fill');
        if (progressFill) progressFill.style.width = '100%';
        const footer = this.modal.querySelector('.quiz-footer');
        if (footer) footer.style.display = 'none';

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
        const passFeedbackHtml = chapterPassed
            ? `<div class="quiz-analysis-box quiz-analysis-box-progress"><p><strong>Chapitre valide:</strong> ${percentage}% >= ${passThreshold}%.</p></div>`
            : `<div class="quiz-analysis-box quiz-analysis-box-weak"><p><strong>Chapitre non valide:</strong> ${percentage}% &lt; ${passThreshold}%. Refaire le test pour debloquer les +10% et les badges.</p></div>`;
        const weakConceptsHtml = this.buildWeakConceptsHtml(progressSnapshot);
        const progressionFooter = this.buildProgressFooter(progressSnapshot);

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

                ${passFeedbackHtml}
                ${weakConceptsHtml}
                ${progressionFooter}

                <div class="quiz-res-actions">
                    <button class="quiz-btn outline" onclick="window.quizController.startQuiz('${this.chapterIdentifier}', '${this.chapterTitle}')"><i class="fas fa-redo"></i> Refaire le test</button>
                    <button class="quiz-btn primary" onclick="window.quizController.closeQuiz()"><i class="fas fa-book"></i> Retourner au cours</button>
                </div>
            </div>
        `;
    }

    buildOptimisticSnapshot(percentage, passThreshold) {
        const base = this.course && this.course.progress
            ? JSON.parse(JSON.stringify(this.course.progress))
            : null;
        if (!base) return null;

        const chapterId = this.chapterIdentifier;
        if (!chapterId) return null;

        if (!Array.isArray(base.attempted_chapter_ids)) base.attempted_chapter_ids = [];
        if (!Array.isArray(base.completed_chapter_ids)) base.completed_chapter_ids = [];
        if (!base.chapter_progress || typeof base.chapter_progress !== 'object') base.chapter_progress = {};

        if (!base.chapter_progress[chapterId]) {
            base.chapter_progress[chapterId] = {
                attempted: false,
                passed: false,
                best_score: 0,
                best_total: 0,
                best_percent: 0,
                best_attempted_at: null
            };
        }

        const row = base.chapter_progress[chapterId];
        row.attempted = true;
        row.best_score = Math.max(Number(row.best_score) || 0, Number(this.score) || 0);
        row.best_total = Math.max(Number(row.best_total) || 0, Number(this.quizData.length) || 0);
        row.best_percent = Math.max(Number(row.best_percent) || 0, Number(percentage) || 0);
        row.best_attempted_at = new Date().toISOString();

        if (!base.attempted_chapter_ids.includes(chapterId)) {
            base.attempted_chapter_ids.push(chapterId);
        }

        const passed = percentage >= passThreshold;
        if (passed) {
            row.passed = true;
            if (!base.completed_chapter_ids.includes(chapterId)) {
                base.completed_chapter_ids.push(chapterId);
            }
        }

        base.completed_count = base.completed_chapter_ids.length;
        base.overall_percent = Math.min(base.completed_count * 10, 100);
        base.pass_threshold = passThreshold;

        if (Array.isArray(base.badges)) {
            base.badges = base.badges.map((badge) => {
                if (!badge || !badge.id) return badge;
                const unlocked =
                    badge.id === 'first_chapter' ? base.completed_count >= 1 :
                    badge.id === 'three_chapters' ? base.completed_count >= 3 :
                    badge.id === 'five_chapters' ? base.completed_count >= 5 :
                    badge.id === 'ten_chapters' ? base.completed_count >= 10 :
                    badge.id === 'streak_3_days' ? (Number(base.streak_days) || 0) >= 3 :
                    Boolean(badge.unlocked);
                return { ...badge, unlocked };
            });
        }

        return base;
    }

    async fetchProgressSnapshot() {
        try {
            const response = await fetch('/api/quiz/progress');
            if (!response.ok) return null;
            const data = await response.json();
            if (!data || !data.snapshot) return null;
            this.persistProgressSnapshotCookie(data.snapshot);
            this.emitProgressUpdate(data.snapshot);
            return data.snapshot;
        } catch (error) {
            console.error('Failed to refresh progress snapshot', error);
            return null;
        }
    }

    buildWeakConceptsHtml(snapshot) {
        if (!snapshot || !Array.isArray(snapshot.weak_concepts) || snapshot.weak_concepts.length === 0) {
            return '';
        }

        const rows = snapshot.weak_concepts.map((item) => `
            <div class="analysis-row">
                <div class="analysis-lbl">${this.escapeHtml(item.concept || 'Concept')}</div>
                <div class="analysis-bar-bg">
                    <div class="analysis-bar-fill" style="width: ${Math.max(0, Math.min(100, Number(item.accuracy) || 0))}%; background: #f85149"></div>
                </div>
                <div class="analysis-val">${Math.max(0, Math.min(100, Number(item.accuracy) || 0))}%</div>
            </div>
            <p class="quiz-weak-tip">${this.escapeHtml(item.suggestion || '')}</p>
        `).join('');

        return `
            <div class="quiz-analysis-box quiz-analysis-box-weak">
                <h3>Priorites de revision</h3>
                ${rows}
            </div>
        `;
    }

    buildProgressFooter(snapshot) {
        if (!snapshot) return '';

        const completed = Number(snapshot.completed_count) || 0;
        const total = Number(snapshot.core_chapters_total) || 10;
        const overall = Number(snapshot.overall_percent) || 0;
        const streak = Number(snapshot.streak_days) || 0;
        const recommendation = snapshot.recommendation || '';

        return `
            <div class="quiz-analysis-box quiz-analysis-box-progress">
                <h3>Progression globale</h3>
                <p>Avancement: <strong>${overall}%</strong> (${completed}/${total} chapitres valides) | Serie: <strong>${streak} jour(s)</strong></p>
                <p>${this.escapeHtml(recommendation)}</p>
            </div>
        `;
    }

    emitProgressUpdate(snapshot) {
        window.dispatchEvent(new CustomEvent('quiz:progress-updated', {
            detail: { snapshot }
        }));
    }

    persistProgressSnapshotCookie(snapshot) {
        try {
            const compact = {
                overall_percent: Number(snapshot.overall_percent) || 0,
                completed_count: Number(snapshot.completed_count) || 0,
                core_chapters_total: Number(snapshot.core_chapters_total) || 10,
                completed_chapter_ids: Array.isArray(snapshot.completed_chapter_ids) ? snapshot.completed_chapter_ids : [],
                attempted_chapter_ids: Array.isArray(snapshot.attempted_chapter_ids) ? snapshot.attempted_chapter_ids : [],
                streak_days: Number(snapshot.streak_days) || 0,
                badges: Array.isArray(snapshot.badges)
                    ? snapshot.badges.filter((b) => b && b.unlocked).map((b) => b.id)
                    : [],
                weak_concepts: Array.isArray(snapshot.weak_concepts)
                    ? snapshot.weak_concepts.map((item) => ({
                        concept: item.concept,
                        accuracy: Number(item.accuracy) || 0
                    }))
                    : [],
                recommendation: snapshot.recommendation || '',
                last_updated: snapshot.last_updated || null
            };
            const encoded = encodeURIComponent(JSON.stringify(compact));
            document.cookie = `algo_progress_snapshot=${encoded}; max-age=31536000; path=/; SameSite=Lax`;
        } catch (error) {
            console.warn('Unable to persist progress snapshot cookie', error);
        }
    }

    getColorForPerc(perc) {
        if (perc >= 80) return '#2ea44e';
        if (perc >= 50) return '#d29922';
        return '#f85149';
    }

    closeQuiz() {
        this.modal.classList.remove('active');
        setTimeout(() => this.modal.querySelector('.quiz-footer').style.display = 'flex', 300);
        // Keep right progress panel in sync after closing modal.
        if (this.course && typeof this.course.refreshProgressFromApi === 'function') {
            this.course.refreshProgressFromApi();
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
