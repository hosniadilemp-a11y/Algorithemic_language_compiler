/**
 * Algo Course Controller
 * Handles navigation, rendering, and interactivity for the course section.
 */

class CourseController {
    constructor() {
        this.courseData = null;
        this.currentChapterIndex = 0;
        this.chapterCache = new Map();
        this.renderRequestId = 0;

        // DOM Elements
        this.overlay = document.getElementById('course-overlay');
        this.outline = document.getElementById('course-outline');
        this.contentArea = document.getElementById('course-content');
        this.pagination = document.getElementById('course-pagination');

        this.prevBtn = document.getElementById('course-prev-btn');
        this.nextBtn = document.getElementById('course-next-btn');
        this.closeBtn = document.getElementById('close-course-btn');
        this.openBtn = document.getElementById('open-course-btn');
        this.isStandalonePage = !this.overlay;

        this.init();
    }

    async init() {
        try {
            const response = await fetch('/static/algo-course.json');
            this.courseData = await response.json();
            this.renderOutline();
            this.bindEvents();
            if (this.isStandalonePage) {
                this.renderCurrentChapter();
            }
        } catch (error) {
            console.error("Error loading course data:", error);
        }
    }

    bindEvents() {
        if (this.openBtn) {
            this.openBtn.addEventListener('click', () => this.show());
        }
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.hide());
        }

        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => this.navigate(-1));
        }
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => this.navigate(1));
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            const isCourseVisible = this.isStandalonePage || (this.overlay && this.overlay.style.display === 'flex');
            if (isCourseVisible) {
                if (e.key === 'ArrowLeft') this.navigate(-1);
                if (e.key === 'ArrowRight') this.navigate(1);
                if (e.key === 'Escape') this.hide();
            }
        });
    }

    show() {
        if (!this.overlay) {
            return;
        }
        this.overlay.style.display = 'flex';
        this.overlay.classList.add('fade-in');
        this.renderCurrentChapter();
    }

    hide() {
        if (!this.overlay) {
            return;
        }
        this.overlay.style.display = 'none';
    }

    navigate(direction) {
        const nextIndex = this.currentChapterIndex + direction;
        if (nextIndex >= 0 && nextIndex < this.courseData.chapters.length) {
            this.currentChapterIndex = nextIndex;
            this.renderCurrentChapter();
            this.updateOutlineActiveState();
        }
    }

    renderOutline() {
        if (!this.outline) return;
        this.outline.innerHTML = '';
        this.courseData.chapters.forEach((chapter, index) => {
            const item = document.createElement('div');
            item.className = 'course-chapter-item';
            const iconClass = chapter.icon || 'fas fa-book-open';
            item.innerHTML = `<i class="${iconClass}"></i> ${chapter.title}`;
            item.dataset.index = index;
            item.onclick = () => {
                this.currentChapterIndex = index;
                this.renderCurrentChapter();
                this.updateOutlineActiveState();
            };
            this.outline.appendChild(item);
        });
        this.updateOutlineActiveState();
    }

    updateOutlineActiveState() {
        if (!this.outline) return;
        const items = this.outline.querySelectorAll('.course-chapter-item');
        items.forEach((item, index) => {
            if (index === this.currentChapterIndex) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    async loadChapter(chapter) {
        if (!chapter || !chapter.file) return chapter;

        if (this.chapterCache.has(chapter.file)) {
            return this.chapterCache.get(chapter.file);
        }

        try {
            const response = await fetch(chapter.file);
            if (!response.ok) {
                throw new Error(`Failed to fetch ${chapter.file}: ${response.status}`);
            }
            const loadedChapter = await response.json();
            const mergedChapter = {
                ...chapter,
                ...loadedChapter,
                sections: Array.isArray(loadedChapter.sections)
                    ? loadedChapter.sections
                    : (chapter.sections || [])
            };
            this.chapterCache.set(chapter.file, mergedChapter);
            return mergedChapter;
        } catch (error) {
            console.error("Error loading chapter file:", chapter.file, error);
            return chapter;
        }
    }

    async renderCurrentChapter() {
        const requestId = ++this.renderRequestId;
        const baseChapter = this.courseData.chapters[this.currentChapterIndex];
        const chapter = await this.loadChapter(baseChapter);
        if (requestId !== this.renderRequestId) return;
        if (!this.contentArea) return;

        this.contentArea.innerHTML = `
            <div class="fade-in">
                <div class="course-header-meta">${chapter.id.toUpperCase()}</div>
                <h1><i class="${chapter.icon || 'fas fa-book-open'}"></i> ${chapter.title}</h1>
                ${chapter.sections.map(section => `
                    <section class="course-section">
                        <h3><i class="${section.icon || 'fas fa-angle-right'}"></i> ${section.title}</h3>
                        <div class="course-text">${this.formatContent(section.content)}</div>
                        ${section.code ? this.renderCodeBlock(section.code) : ''}
                    </section>
                `).join('')}
                <div class="course-footer-spacer"></div>
            </div>
        `;

        this.contentArea.scrollTop = 0;
        if (this.pagination) {
            this.pagination.innerText = `${this.currentChapterIndex + 1} / ${this.courseData.chapters.length}`;
        }

        if (this.prevBtn) {
            this.prevBtn.disabled = this.currentChapterIndex === 0;
        }
        if (this.nextBtn) {
            this.nextBtn.disabled = this.currentChapterIndex === this.courseData.chapters.length - 1;
        }

        // Add listeners to "Executer" buttons
        this.contentArea.querySelectorAll('.course-exec-btn').forEach(btn => {
            btn.onclick = (e) => {
                const codeBlock = e.target.closest('.course-code-block').querySelector('.course-code-body');
                const code = codeBlock.innerText;
                this.executeCode(code);
            };
        });

        this.contentArea.querySelectorAll('.course-solution-code').forEach((pre) => {
            pre.innerHTML = this.highlightAlgoCode(pre.textContent || '');
        });
    }

    formatContent(text) {
        if (!text) return '';
        const html = text
            .replace(/\[\[DEF\]\]\s*(.*?)(\n|$)/g, '<div class="course-callout course-callout-def"><div class="course-callout-title">Définition</div><p>$1</p></div>')
            .replace(/\[\[ALERT\]\]\s*(.*?)(\n|$)/g, '<div class="course-callout course-callout-alert"><div class="course-callout-title">Alerte</div><p>$1</p></div>')
            .replace(/\[\[NOTE\]\]\s*(.*?)(\n|$)/g, '<div class="course-callout course-callout-note"><div class="course-callout-title">Note</div><p>$1</p></div>')
            .replace(/### (.*?)\n/g, '<h4 class="course-h4">$1</h4>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code class="course-inline-code">$1</code>');

        return html
            .split(/\n\n+/)
            .map((block) => {
                const normalized = block.trim();
                if (!normalized) return '';
                if (
                    normalized.startsWith('<div class="course-callout') ||
                    normalized.startsWith('<div class="course-exercise') ||
                    normalized.startsWith('<details') ||
                    normalized.startsWith('<h4 ')
                ) {
                    return normalized;
                }
                return `<p>${normalized.replace(/\n/g, '<br>')}</p>`;
            })
            .join('');
    }

    renderCodeBlock(code) {
        const highlightedCode = this.highlightAlgoCode(code);
        return `
            <div class="course-code-block">
                <div class="course-code-header">
                    <span><i class="fas fa-terminal"></i> Exemple d'algorithme</span>
                    <button class="course-exec-btn"><i class="fas fa-play"></i> Charger & Formater</button>
                </div>
                <div class="course-code-body">${highlightedCode}</div>
            </div>
        `;
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

    executeCode(code) {
        if (window.editor) {
            window.editor.setValue(code);
            this.hide();

            // Auto-format after loading
            if (typeof formatAlgoCode === 'function') {
                formatAlgoCode(window.editor);
            }
        } else {
            try {
                localStorage.setItem('algocompiler.pendingCourseCode', code);
            } catch (error) {
                console.warn("Unable to cache code for compiler redirect:", error);
            }
            window.location.href = '/';
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.courseController = new CourseController();
});
