class CourseController {
    constructor() {
        this.courseData = null;
        this.currentChapterIndex = 0;
        this.contentVersion = '27';
        this.coreChapterIds = [
            'intro',
            'tableaux',
            'chaines',
            'allocation',
            'actions',
            'enregistrements',
            'fichiers',
            'listes_chainees',
            'piles',
            'files'
        ];
        this.progress = this.defaultProgressState();
        this.isStandalonePage = !!document.getElementById('course-outline');

        this.sidebar = document.getElementById('course-outline');
        this.contentArea = document.getElementById('course-content');
        this.prevBtn = document.getElementById('course-prev-btn');
        this.nextBtn = document.getElementById('course-next-btn');
        this.paginationLabel = document.getElementById('course-pagination');

        this.progressDock = document.getElementById('course-progress-dock');
        this.progressGauge = document.getElementById('course-progress-gauge');
        this.progressPercent = document.getElementById('course-progress-percent');
        this.progressCompleted = document.getElementById('course-progress-completed');
        this.progressStreak = document.getElementById('course-progress-streak');
        this.progressBadges = document.getElementById('course-progress-badges');
        this.progressWeak = document.getElementById('course-progress-weak');
        this.progressRecommendation = document.getElementById('course-progress-reco');

        if (typeof QuizController !== 'undefined') {
            this.quiz = new QuizController(this);
            window.quizController = this.quiz;
        }

        this.init();
    }

    defaultProgressState() {
        return {
            core_chapters_total: this.coreChapterIds.length,
            pass_threshold: 70,
            overall_percent: 0,
            completed_count: 0,
            completed_chapter_ids: [],
            attempted_chapter_ids: [],
            chapter_progress: this.coreChapterIds.reduce((acc, chapterId) => {
                acc[chapterId] = {
                    attempted: false,
                    passed: false,
                    best_score: 0,
                    best_total: 0,
                    best_percent: 0,
                    best_attempted_at: null
                };
                return acc;
            }, {}),
            streak_days: 0,
            badges: this.getBadgeCatalog().map((badge) => ({ ...badge, unlocked: false })),
            weak_concepts: [],
            recommendation: ''
        };
    }

    getBadgeCatalog() {
        return [
            { id: 'first_chapter', label: 'Premier Pas', description: 'Valider 1 chapitre.', icon: 'fas fa-seedling' },
            { id: 'three_chapters', label: 'Trio Solide', description: 'Valider 3 chapitres.', icon: 'fas fa-medal' },
            { id: 'five_chapters', label: 'Mi-Parcours', description: 'Valider 5 chapitres.', icon: 'fas fa-star' },
            { id: 'ten_chapters', label: 'Maitre Algo', description: 'Valider 10 chapitres.', icon: 'fas fa-crown' },
            { id: 'streak_3_days', label: 'Serie 3 Jours', description: 'Reussir sur 3 jours consecutifs.', icon: 'fas fa-bolt' }
        ];
    }

    async init() {
        try {
            const response = await fetch(`/static/algo-course.json?v=${this.contentVersion}`);
            this.courseData = await response.json();
            this.loadState();

            if (this.currentChapterIndex < 0) this.currentChapterIndex = 0;
            if (this.courseData?.chapters?.length) {
                this.currentChapterIndex = Math.min(this.currentChapterIndex, this.courseData.chapters.length - 1);
            }

            this.hydrateProgressFromCookie();
            await this.renderOutline();
            this.bindEvents();
            this.updateProgressUI();
            this.refreshProgressFromApi();

            if (this.isStandalonePage) {
                this.renderCurrentChapter();
            }
        } catch (error) {
            console.error('Failed to initialize course controller:', error);
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

        window.addEventListener('quiz:progress-updated', (event) => {
            const snapshot = event?.detail?.snapshot;
            if (!snapshot) return;
            this.applyProgressSnapshot(snapshot, { persistCookie: true });
        });
    }

    readCookie(name) {
        const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const match = document.cookie.match(new RegExp(`(?:^|; )${escaped}=([^;]*)`));
        return match ? decodeURIComponent(match[1]) : null;
    }

    writeProgressSnapshotCookie(snapshot) {
        try {
            const compact = {
                overall_percent: Number(snapshot.overall_percent) || 0,
                completed_count: Number(snapshot.completed_count) || 0,
                core_chapters_total: Number(snapshot.core_chapters_total) || this.coreChapterIds.length,
                completed_chapter_ids: Array.isArray(snapshot.completed_chapter_ids) ? snapshot.completed_chapter_ids : [],
                attempted_chapter_ids: Array.isArray(snapshot.attempted_chapter_ids) ? snapshot.attempted_chapter_ids : [],
                streak_days: Number(snapshot.streak_days) || 0,
                badges: Array.isArray(snapshot.badges)
                    ? snapshot.badges.filter((badge) => badge?.unlocked).map((badge) => badge.id)
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

            const payload = encodeURIComponent(JSON.stringify(compact));
            document.cookie = `algo_progress_snapshot=${payload}; max-age=31536000; path=/; SameSite=Lax`;
        } catch (error) {
            console.warn('Unable to write progress cookie', error);
        }
    }

    hydrateProgressFromCookie() {
        const raw = this.readCookie('algo_progress_snapshot');
        if (!raw) return;

        try {
            const parsed = JSON.parse(raw);
            this.applyProgressSnapshot(parsed, { persistCookie: false });
        } catch (error) {
            console.warn('Invalid progress snapshot cookie', error);
        }
    }

    async refreshProgressFromApi() {
        try {
            const response = await fetch('/api/quiz/progress');
            if (!response.ok) return;
            const data = await response.json();
            const snapshot = data?.snapshot || null;
            if (!snapshot) return;
            this.applyProgressSnapshot(snapshot, { persistCookie: true });
        } catch (error) {
            console.warn('Unable to fetch server progress snapshot', error);
        }
    }

    normalizeBadges(rawBadges) {
        const catalog = this.getBadgeCatalog();
        const byId = new Map();

        if (Array.isArray(rawBadges)) {
            rawBadges.forEach((entry) => {
                if (typeof entry === 'string') {
                    byId.set(entry, { id: entry, unlocked: true });
                    return;
                }
                if (entry && entry.id) {
                    byId.set(entry.id, entry);
                }
            });
        }

        return catalog.map((badge) => {
            const fromPayload = byId.get(badge.id);
            return {
                id: badge.id,
                label: fromPayload?.label || badge.label,
                description: fromPayload?.description || badge.description,
                icon: fromPayload?.icon || badge.icon,
                unlocked: fromPayload ? Boolean(fromPayload.unlocked) : false
            };
        });
    }

    normalizeProgressSnapshot(snapshot) {
        const normalized = this.defaultProgressState();
        if (!snapshot || typeof snapshot !== 'object') {
            return normalized;
        }

        const completedIds = Array.isArray(snapshot.completed_chapter_ids)
            ? snapshot.completed_chapter_ids.filter((id) => this.coreChapterIds.includes(id))
            : [];
        const attemptedIds = Array.isArray(snapshot.attempted_chapter_ids)
            ? snapshot.attempted_chapter_ids.filter((id) => this.coreChapterIds.includes(id))
            : [];

        const chapterProgress = {};
        this.coreChapterIds.forEach((chapterId) => {
            const source = snapshot.chapter_progress?.[chapterId] || {};
            chapterProgress[chapterId] = {
                attempted: Boolean(source.attempted || attemptedIds.includes(chapterId)),
                passed: Boolean(source.passed || completedIds.includes(chapterId)),
                best_score: Number(source.best_score) || 0,
                best_total: Number(source.best_total) || 0,
                best_percent: Number(source.best_percent) || 0,
                best_attempted_at: source.best_attempted_at || null
            };
        });

        const computedCompleted = this.coreChapterIds.filter((chapterId) => chapterProgress[chapterId].passed);
        const computedAttempted = this.coreChapterIds.filter((chapterId) => chapterProgress[chapterId].attempted);

        normalized.core_chapters_total = Number(snapshot.core_chapters_total) || this.coreChapterIds.length;
        normalized.pass_threshold = Number(snapshot.pass_threshold) || 70;
        normalized.completed_chapter_ids = computedCompleted;
        normalized.attempted_chapter_ids = computedAttempted;
        normalized.completed_count = Number(snapshot.completed_count) || computedCompleted.length;
        normalized.overall_percent = Number(snapshot.overall_percent);
        if (!Number.isFinite(normalized.overall_percent)) {
            normalized.overall_percent = Math.min(normalized.completed_count * 10, 100);
        }
        normalized.overall_percent = Math.max(0, Math.min(100, Math.round(normalized.overall_percent)));
        normalized.chapter_progress = chapterProgress;
        normalized.streak_days = Math.max(0, Number(snapshot.streak_days) || 0);
        normalized.badges = this.normalizeBadges(snapshot.badges);
        normalized.weak_concepts = Array.isArray(snapshot.weak_concepts)
            ? snapshot.weak_concepts.map((item) => ({
                concept: String(item?.concept || '').trim(),
                accuracy: Math.max(0, Math.min(100, Number(item?.accuracy) || 0)),
                suggestion: item?.suggestion || ''
            })).filter((item) => item.concept)
            : [];
        normalized.recommendation = snapshot.recommendation || '';

        return normalized;
    }

    applyProgressSnapshot(snapshot, options = {}) {
        const { persistCookie = false } = options;
        this.progress = this.normalizeProgressSnapshot(snapshot);
        if (persistCookie) {
            this.writeProgressSnapshotCookie(this.progress);
        }
        this.updateOutlineProgressState();
        this.updateProgressUI();
    }

    updateOutlineProgressState() {
        if (!this.sidebar) return;

        this.sidebar.querySelectorAll('.outline-item').forEach((item) => {
            const chapterId = item.dataset.chapterId;
            const isCompleted = this.progress.completed_chapter_ids.includes(chapterId);
            const isAttempted = this.progress.attempted_chapter_ids.includes(chapterId);
            const statusIcon = item.querySelector('.outline-status-icon');

            item.classList.toggle('completed', isCompleted);
            item.classList.toggle('attempted', !isCompleted && isAttempted);

            if (statusIcon) {
                if (isCompleted) {
                    statusIcon.className = 'outline-status-icon fas fa-check-circle';
                } else if (isAttempted) {
                    statusIcon.className = 'outline-status-icon fas fa-dot-circle';
                } else {
                    statusIcon.className = 'outline-status-icon far fa-circle';
                }
            }
        });
    }

    updateProgressUI() {
        if (!this.progressDock) return;

        const overall = Number(this.progress.overall_percent) || 0;
        const completedCount = Number(this.progress.completed_count) || 0;
        const total = Number(this.progress.core_chapters_total) || this.coreChapterIds.length;
        const streak = Number(this.progress.streak_days) || 0;

        if (this.progressGauge) {
            this.progressGauge.style.setProperty('--progress-value', `${Math.max(0, Math.min(100, overall))}%`);
        }
        if (this.progressPercent) this.progressPercent.textContent = `${overall}%`;
        if (this.progressCompleted) this.progressCompleted.textContent = `${completedCount} / ${total} chapitres valides`;
        if (this.progressStreak) this.progressStreak.textContent = `${streak} jour(s) de serie`;
        if (this.progressRecommendation) {
            this.progressRecommendation.textContent = this.progress.recommendation || 'Passe un quiz pour lancer le suivi pedagogique.';
        }

        if (this.progressBadges) {
            this.progressBadges.innerHTML = '';
            this.progress.badges.forEach((badge) => {
                const badgeEl = document.createElement('div');
                badgeEl.className = `course-progress-badge ${badge.unlocked ? 'is-unlocked' : ''}`;
                badgeEl.title = badge.description;
                const iconEl = document.createElement('i');
                iconEl.className = badge.icon || 'fas fa-award';
                const labelEl = document.createElement('span');
                labelEl.textContent = badge.label;
                badgeEl.appendChild(iconEl);
                badgeEl.appendChild(labelEl);
                this.progressBadges.appendChild(badgeEl);
            });
        }

        if (this.progressWeak) {
            if (!this.progress.weak_concepts.length) {
                this.progressWeak.innerHTML = '<span class="course-progress-empty">Aucun concept faible detecte pour le moment.</span>';
                return;
            }

            this.progressWeak.innerHTML = '';
            this.progress.weak_concepts.forEach((item) => {
                const chip = document.createElement('div');
                chip.className = 'course-progress-weak-item';
                chip.textContent = `${item.concept} (${item.accuracy}%)`;
                chip.title = item.suggestion || '';
                this.progressWeak.appendChild(chip);
            });
        }
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
            item.innerHTML = `
                <i class="${chapter.icon || 'fas fa-book'}"></i>
                <span class="outline-title">${chapter.title}</span>
                <span class="outline-status-icon far fa-circle"></span>
            `;
            item.dataset.index = index;
            item.dataset.chapterId = chapter.id || '';
            item.onclick = () => {
                this.currentChapterIndex = index;
                this.saveState();
                this.renderCurrentChapter();
                this.updateOutlineActiveState();
            };
            this.sidebar.appendChild(item);
        });

        this.updateOutlineProgressState();
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
            chapter.sections.forEach((section) => {
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
                    <p style="color: var(--course-muted);">Mettez vos connaissances a l'epreuve avec notre test interactif.</p>
                </div>
                <button class="course-quiz-btn" onclick="window.quizController.startQuiz('${chapterInfo.id}', '${safeTitle}')" style="font-size: 1.1rem; padding: 12px 30px;">
                    <i class="fas fa-tasks"></i> Demarrer le Quiz
                </button>
            `;
            this.contentArea.appendChild(quizDiv);
        }

        this.bindSectionEvents();
        await this.validateRunnableSnippets();

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
        this.contentArea.querySelectorAll('.course-exec-btn').forEach((btn) => {
            btn.onclick = (e) => {
                const codeBlock = e.currentTarget.closest('.course-code-block').querySelector('.course-code-body');
                const code = codeBlock.dataset.rawCode || codeBlock.innerText;
                this.executeCode(code);
            };
        });

        this.contentArea.querySelectorAll('.course-try-btn, .course-solution-run').forEach((btn) => {
            btn.onclick = (e) => {
                const rawCode = e.currentTarget.getAttribute('data-code') || '';
                const code = this.normalizeCodeForDisplay(this.decodeCourseCode(rawCode));
                this.executeCode(code, true);
            };
        });

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

        if (!normalized.includes('\n') && normalized.includes('\\n')) {
            normalized = normalized.replace(/\\n/g, '\n').replace(/\\t/g, '\t');
        }

        normalized = normalized.replace(/;\s*(?=\S)/g, ';\n');

        normalized = normalized.replace(
            /;\s*(?=(Algorithme|Type|Var|Const|Debut|Procedure|Fonction|Tantque|Pour|Si|Sinon|Fin\s*Si|FinSi|Fin\s*Pour|FinPour|Fin\s*Tantque|Fin\s*TantQue|FinTantque|FinTantQue|Jusqua|Fin\.|[A-Za-z_][A-Za-z0-9_]*\s*:=))/gi,
            ';\n'
        );

        normalized = normalized
            .replace(/\b(Alors)(?!\s*\n)\s+/gi, '$1\n    ')
            .replace(/\b(Faire)(?!\s*\n)\s+/gi, '$1\n    ');

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
            .replace(/\[\[DEF\]\]\s*(.*?)(\n|$)/g, '<div class="course-callout course-callout-def"><div class="course-callout-title">Definition</div><p>$1</p></div>')
            .replace(/\[\[ALERT\]\]\s*(.*?)(\n|$)/g, '<div class="course-callout course-callout-alert"><div class="course-callout-title">Alerte</div><p>$1</p></div>')
            .replace(/\[\[NOTE\]\]\s*(.*?)(\n|$)/g, '<div class="course-callout course-callout-note"><div class="course-callout-title">Note</div><p>$1</p></div>')
            .replace(/\[\[STYLISH_EX\]\]/g, '<div class="stylish-lesson-intro"><i class="fas fa-star"></i> Objectifs pedagogiques</div>')
            .replace(/### (.*?)\n/g, '<h4 class="course-h4">$1</h4>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code class="course-inline-code">$1</code>')
            .replace(/^- (.*?)(\n|$)/gm, '<li>$1</li>');

        if (html.includes('<li>')) {
            html = html.replace(/(<li>.*?<\/li>)+/gs, '<ul>$&</ul>');
        }

        html = html.replace(/data-code="([^"]*)"/g, (_match, p1) => {
            return 'data-code="' + p1.replace(/\n/g, '&#10;').replace(/\\n/g, '&#10;') + '"';
        });

        return html.split(/\n\n+/).map((block) => {
            const normalized = block.trim();
            if (!normalized) return '';
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
        if (!/^\s*Algorithme\b/i.test(code)) {
            code = 'Algorithme ExerciceAuto;\n' + code;
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
            this.saveState();
            window.location.href = '/';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.courseController = new CourseController();
});
