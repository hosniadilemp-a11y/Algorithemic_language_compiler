class CourseController {
    constructor() {
        this.courseData = null;
        this.currentChapterIndex = 0;
        this.contentVersion = '26';
        this.isStandalonePage = !!document.getElementById('course-outline');

        this.sidebar = document.getElementById('course-outline');
        this.contentArea = document.getElementById('course-content');
        this.prevBtn = document.getElementById('course-prev-btn');
        this.nextBtn = document.getElementById('course-next-btn');
        this.paginationLabel = document.getElementById('course-pagination');

        // Initialize Quiz System
        if (typeof QuizController !== 'undefined') {
            this.quiz = new QuizController(this);
            window.quizController = this.quiz; // Export globally for HTML inline onclick
        }

        this.init();
    }

    async init() {
        try {
            const response = await fetch(`/static/algo-course.json?v=${this.contentVersion}`);
            this.courseData = await response.json();
            this.loadState();
            await this.renderOutline();
            this.bindEvents();
            if (this.isStandalonePage) {
                this.renderCurrentChapter();
            }
        } catch (error) {
            console.error("Failed to initialize course controller:", error);
        }
    }

    bindEvents() {
        if (this.prevBtn) this.prevBtn.onclick = () => this.navigate(-1);
        if (this.nextBtn) this.nextBtn.onclick = () => this.navigate(1);

        window.onpopstate = (e) => {
            if (e.state && e.state.chapterIndex !== undefined) {
                this.currentChapterIndex = e.state.chapterIndex;
                this.renderCurrentChapter();
                this.updateOutlineActiveState();
            }
        };
    }

    navigate(direction) {
        const nextIndex = this.currentChapterIndex + direction;
        if (nextIndex >= 0 && nextIndex < this.courseData.chapters.length) {
            this.currentChapterIndex = nextIndex;
            this.saveState();
            this.renderCurrentChapter();
            this.updateOutlineActiveState();
        }
    }

    async renderOutline() {
        if (!this.sidebar) return;
        this.sidebar.innerHTML = '';

        this.courseData.chapters.forEach((chapter, index) => {
            const item = document.createElement('div');
            item.className = 'outline-item' + (index === this.currentChapterIndex ? ' active' : '');
            item.innerHTML = `<i class="${chapter.icon || 'fas fa-book'}"></i> <span>${chapter.title}</span>`;
            item.dataset.index = index;
            item.onclick = () => {
                this.currentChapterIndex = index;
                this.saveState();
                this.renderCurrentChapter();
                this.updateOutlineActiveState();
            };
            this.sidebar.appendChild(item);
        });
    }

    updateOutlineActiveState() {
        if (!this.sidebar) return;
        this.sidebar.querySelectorAll('.outline-item').forEach((item, index) => {
            item.classList.toggle('active', index === this.currentChapterIndex);
        });
    }

    async renderCurrentChapter() {
        if (!this.contentArea || !this.courseData) return;

        const chapterInfo = this.courseData.chapters[this.currentChapterIndex];
        const sep = chapterInfo.file.includes('?') ? '&' : '?';
        const response = await fetch(`${chapterInfo.file}${sep}v=${this.contentVersion}`);
        const chapter = await response.json();

        this.contentArea.innerHTML = `
            <h1 class="course-h1">${chapter.title}</h1>
        `;

        if (chapter.sections) {
            chapter.sections.forEach(section => {
                const sectionEl = document.createElement('section');
                sectionEl.className = 'course-section';

                if (section.title) {
                    const h3 = document.createElement('h3');
                    h3.className = 'course-h3';
                    h3.textContent = section.title;
                    sectionEl.appendChild(h3);
                }

                if (section.content) {
                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'course-text';
                    contentDiv.innerHTML = this.formatContent(section.content);
                    sectionEl.appendChild(contentDiv);
                }

                if (section.code) {
                    const codeBlock = this.createCodeBlock(section.code);
                    sectionEl.appendChild(codeBlock);
                }

                this.contentArea.appendChild(sectionEl);
            });
        }

        // --- Add Quiz Button if applicable ---
        if (this.quiz && chapterInfo.id && chapterInfo.id !== 'tutorial') {
            const quizDiv = document.createElement('div');
            quizDiv.className = 'course-section';
            quizDiv.style.textAlign = 'center';
            quizDiv.style.marginTop = '40px';
            quizDiv.style.paddingTop = '20px';
            quizDiv.style.borderTop = '1px solid var(--course-line)';

            const safeTitle = chapterInfo.title.replace(/'/g, "\\'");
            quizDiv.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <h3 style="font-size: 1.5rem; margin-bottom: 10px;">Avez-vous tout compris ?</h3>
                    <p style="color: var(--course-muted);">Mettez vos connaissances à l'épreuve avec notre test interactif généré aléatoirement.</p>
                </div>
                <button class="course-quiz-btn" onclick="window.quizController.startQuiz('${chapterInfo.id}', '${safeTitle}')" style="font-size: 1.1rem; padding: 12px 30px;">
                    <i class="fas fa-tasks"></i> Démarrer le Quiz
                </button>
            `;
            this.contentArea.appendChild(quizDiv);
        }

        this.bindSectionEvents();
        await this.validateRunnableSnippets();

        // Restore scroll position
        const savedScroll = localStorage.getItem('algocompiler.scrollTop');
        if (savedScroll !== null) {
            this.contentArea.scrollTop = parseInt(savedScroll, 10);
            localStorage.removeItem('algocompiler.scrollTop');
        } else {
            this.contentArea.scrollTop = 0;
        }

        this.updateNavButtons();
    }

    updateNavButtons() {
        if (this.prevBtn) this.prevBtn.disabled = this.currentChapterIndex === 0;
        if (this.nextBtn) this.nextBtn.disabled = this.currentChapterIndex === this.courseData.chapters.length - 1;

        if (this.paginationLabel && this.courseData) {
            this.paginationLabel.textContent = `${this.currentChapterIndex + 1} / ${this.courseData.chapters.length}`;
        }
    }

    bindSectionEvents() {
        // Add listeners to "Executer" buttons
        this.contentArea.querySelectorAll('.course-exec-btn').forEach(btn => {
            btn.onclick = (e) => {
                const codeBlock = e.currentTarget.closest('.course-code-block').querySelector('.course-code-body');
                const code = codeBlock.dataset.rawCode || codeBlock.innerText;
                this.executeCode(code);
            };
        });

        // Add listeners to "Try in Editor" buttons (Exercises)
        this.contentArea.querySelectorAll('.course-try-btn, .course-solution-run').forEach(btn => {
            btn.onclick = (e) => {
                const rawCode = e.currentTarget.getAttribute('data-code') || '';
                const code = this.normalizeCodeForDisplay(this.decodeCourseCode(rawCode));
                this.executeCode(code, true);
            };
        });

        // Always keep exercise solution buttons actionable and clearly labeled.
        this.contentArea.querySelectorAll('.course-solution-run').forEach((btn) => {
            btn.disabled = false;
            btn.classList.remove('course-solution-run-disabled');
            btn.removeAttribute('title');
            btn.innerHTML = 'Executer code';
        });

        this.contentArea.querySelectorAll('.course-solution-code').forEach((pre) => {
            const normalized = this.normalizeCodeForDisplay(pre.textContent || '');
            pre.innerHTML = this.highlightAlgoCode(normalized);
        });
    }

    async validateRunnableSnippets() {
        const checks = [];

        this.contentArea.querySelectorAll('.course-exec-btn').forEach((btn) => {
            const codeBlock = btn.closest('.course-code-block')?.querySelector('.course-code-body');
            const code = (codeBlock?.dataset?.rawCode || codeBlock?.innerText || '').trim();

            if (!this.isCompleteCourseCode(code)) {
                btn.remove();
                return;
            }

            checks.push(this.validateSnippet(btn, code, false));
        });

        // Do not disable exercise solution buttons.
        // User should always be able to send solution code to the editor.

        if (checks.length > 0) {
            await Promise.all(checks);
        }
    }

    async validateSnippet(button, code, isSolutionButton) {
        try {
            const response = await fetch('/api/validate_algo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code })
            });

            if (!response.ok) {
                if (isSolutionButton) return;
                button.remove();
                return;
            }

            const data = await response.json();
            if (!data.ok) {
                if (isSolutionButton) return;
                button.remove();
            }
        } catch (error) {
            if (isSolutionButton) return;
            button.remove();
        }
    }

    normalizeCodeForDisplay(code) {
        let normalized = String(code || '').replace(/\r\n?/g, '\n');
        normalized = normalized
            .replace(/&#10;|&#x0A;|&#xA;/gi, '\n')
            .replace(/&#13;|&#x0D;|&#xD;/gi, '\n');

        // Some stored blocks may contain literal \n; convert for proper multi-line display.
        if (!normalized.includes('\n') && normalized.includes('\\n')) {
            normalized = normalized.replace(/\\n/g, '\n').replace(/\\t/g, '\t');
        }

        // Split merged statements such as ";Tantque", ";Cour->x :=", ";Fin.".
        normalized = normalized.replace(/;\s*(?=\S)/g, ';\n');

        // Secondary split pass for common pseudo-code tokens.
        normalized = normalized.replace(
            /;\s*(?=(Algorithme|Type|Var|Const|Debut|Procedure|Fonction|Tantque|Pour|Si|Sinon|Fin\s*Si|FinSi|Fin\s*Pour|FinPour|Fin\s*Tantque|Fin\s*TantQue|FinTantque|FinTantQue|Jusqua|Fin\.|[A-Za-z_][A-Za-z0-9_]*\s*:=))/gi,
            ';\n'
        );

        // Ensure block starters are on their own line when flattened after conditions.
        normalized = normalized
            .replace(/\b(Alors)(?!\s*\n)\s+/gi, '$1\n    ')
            .replace(/\b(Faire)(?!\s*\n)\s+/gi, '$1\n    ');

        // If still one line, perform stronger splitting.
        if (!normalized.includes('\n')) {
            normalized = normalized
                .replace(/;\s*/g, ';\n')
                .replace(/\s+(Algorithme|Type|Var|Const|Debut|Procedure|Fonction|Tantque|Pour|Si|Sinon|Fin|Jusqua)\b/g, '\n$1')
                .trim();
        }

        return normalized;
    }

    saveState() {
        localStorage.setItem('algocompiler.currentChapter', this.currentChapterIndex);
        localStorage.setItem('algocompiler.scrollTop', this.contentArea.scrollTop);
    }

    loadState() {
        const saved = localStorage.getItem('algocompiler.currentChapter');
        if (saved !== null) {
            this.currentChapterIndex = parseInt(saved, 10);
        }
    }

    formatContent(text) {
        if (!text) return '';
        let html = text
            .replace(/\[\[DEF\]\]\s*(.*?)(\n|$)/g, '<div class="course-callout course-callout-def"><div class="course-callout-title">Définition</div><p>$1</p></div>')
            .replace(/\[\[ALERT\]\]\s*(.*?)(\n|$)/g, '<div class="course-callout course-callout-alert"><div class="course-callout-title">Alerte</div><p>$1</p></div>')
            .replace(/\[\[NOTE\]\]\s*(.*?)(\n|$)/g, '<div class="course-callout course-callout-note"><div class="course-callout-title">Note</div><p>$1</p></div>')
            .replace(/\[\[STYLISH_EX\]\]/g, '<div class="stylish-lesson-intro"><i class="fas fa-star"></i> Objectifs pédagogiques</div>')
            .replace(/### (.*?)\n/g, '<h4 class="course-h4">$1</h4>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code class="course-inline-code">$1</code>')
            .replace(/^- (.*?)(\n|$)/gm, '<li>$1</li>');

        if (html.includes('<li>')) {
            html = html.replace(/(<li>.*?<\/li>)+/gs, '<ul>$&</ul>');
        }

        // Protect data-code attribute newlines from being flattened to spaces by the browser DOM
        html = html.replace(/data-code="([^"]*)"/g, (match, p1) => {
            return 'data-code="' + p1.replace(/\n/g, '&#10;').replace(/\\n/g, '&#10;') + '"';
        });

        return html.split(/\n\n+/).map(block => {
            const normalized = block.trim();
            if (!normalized) return '';
            // Keep any HTML fragment intact (not only a small whitelist),
            // otherwise SVG blocks get split and wrapped in <p>, which breaks figures.
            if (normalized.startsWith('<')) {
                return normalized;
            }
            return `<p>${normalized.replace(/\n/g, '<br>')}</p>`;
        }).join('');
    }

    createCodeBlock(code) {
        const div = document.createElement('div');
        div.className = 'course-code-block';

        const header = document.createElement('div');
        header.className = 'course-code-header';
        const canLoad = this.isCompleteCourseCode(code);
        header.innerHTML = `<span><i class="fas fa-terminal"></i> Exemple d'algorithme</span>` +
            (canLoad ? `<button class="course-exec-btn"><i class="fas fa-play"></i> Charger & Formater</button>` : '');

        const body = document.createElement('div');
        body.className = 'course-code-body';
        const normalizedCode = this.normalizeCodeForDisplay(code);
        body.dataset.rawCode = normalizedCode;
        body.innerHTML = this.highlightAlgoCode(normalizedCode);

        div.appendChild(header);
        div.appendChild(body);
        return div;
    }

    escapeHtml(text) {
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    highlightAlgoCode(code) {
        const escaped = this.escapeHtml(code);
        return escaped
            .replace(/(\/\/.*)$/gm, '<span class="algo-cmt">$1</span>')
            .replace(/(\"(?:[^\"\\\\]|\\\\.)*\")/g, '<span class="algo-str">$1</span>')
            .replace(/('(?:[^'\\\\]|\\\\.)*')/g, '<span class="algo-str">$1</span>')
            .replace(/\b(\d+(?:\.\d+)?)\b/g, '<span class="algo-num">$1</span>')
            .replace(/\b(Algorithme|Const|Var|Type|Enregistrement|Debut|Fin|Fonction|Procedure|Retourner|Si|Sinon|Alors|Fin Si|Pour|Fin Pour|Tantque|Fin Tantque|Repeter|Jusqua|Lire|Ecrire|Vrai|Faux|NIL|allouer|liberer|taille|Entier|Reel|Chaine|Caractere|Booleen|Tableau|De|Et|Ou|Non)\b/g, '<span class="algo-kw">$1</span>');
    }

    decodeCourseCode(rawCode) {
        return String(rawCode)
            .replace(/&#10;|&#x0A;|&#xA;/gi, '\n')
            .replace(/\\n/g, '\n')
            .replace(/\\t/g, '\t')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&')
            .replace(/&#39;/g, "'")
            .replace(/&quot;/g, '"');
    }

    isCompleteCourseCode(code) {
        const normalized = String(code || '').trim();
        if (!normalized) return false;
        if (!/\bDebut\b/i.test(normalized)) return false;
        if (!/\bFin\.\s*$/i.test(normalized)) return false;
        return true;
    }

    executeCode(code, fromExercise = false) {
        // Auto-wrap bare blocks with 'Algorithme' to ensure valid compilation in the IDE
        if (!/^\s*Algorithme\b/i.test(code)) {
            code = "Algorithme ExerciceAuto;\n" + code;
        }

        if (window.editor) {
            window.editor.setValue(code);
            if (typeof formatAlgoCode === 'function') {
                formatAlgoCode(window.editor);
            }
        } else {
            localStorage.setItem('algocompiler.pendingCourseCode', code);
            if (fromExercise) {
                localStorage.setItem('algocompiler.fromExercise', 'true');
            }
            // Save scroll position before leaving
            this.saveState();
            window.location.href = '/';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.courseController = new CourseController();
});
