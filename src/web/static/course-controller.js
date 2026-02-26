/**
 * Algo Course Controller
 * Handles navigation, rendering, and interactivity for the course section.
 */

class CourseController {
    constructor() {
        this.courseData = null;
        this.currentChapterIndex = 0;

        // DOM Elements
        this.overlay = document.getElementById('course-overlay');
        this.outline = document.getElementById('course-outline');
        this.contentArea = document.getElementById('course-content');
        this.pagination = document.getElementById('course-pagination');

        this.prevBtn = document.getElementById('course-prev-btn');
        this.nextBtn = document.getElementById('course-next-btn');
        this.closeBtn = document.getElementById('close-course-btn');
        this.openBtn = document.getElementById('open-course-btn');

        this.init();
    }

    async init() {
        try {
            const response = await fetch('/static/algo-course.json');
            this.courseData = await response.json();
            this.renderOutline();
            this.bindEvents();
        } catch (error) {
            console.error("Error loading course data:", error);
        }
    }

    bindEvents() {
        this.openBtn.addEventListener('click', () => this.show());
        this.closeBtn.addEventListener('click', () => this.hide());

        this.prevBtn.addEventListener('click', () => this.navigate(-1));
        this.nextBtn.addEventListener('click', () => this.navigate(1));

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (this.overlay.style.display === 'flex') {
                if (e.key === 'ArrowLeft') this.navigate(-1);
                if (e.key === 'ArrowRight') this.navigate(1);
                if (e.key === 'Escape') this.hide();
            }
        });
    }

    show() {
        this.overlay.style.display = 'flex';
        this.overlay.classList.add('fade-in');
        this.renderCurrentChapter();
    }

    hide() {
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
        this.outline.innerHTML = '';
        this.courseData.chapters.forEach((chapter, index) => {
            const item = document.createElement('div');
            item.className = 'course-chapter-item';
            item.innerHTML = `<i class="fas fa-book-open"></i> ${chapter.title}`;
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
        const items = this.outline.querySelectorAll('.course-chapter-item');
        items.forEach((item, index) => {
            if (index === this.currentChapterIndex) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    renderCurrentChapter() {
        const chapter = this.courseData.chapters[this.currentChapterIndex];
        this.contentArea.innerHTML = `
            <div class="fade-in">
                <h1>${chapter.title}</h1>
                ${chapter.sections.map(section => `
                    <section>
                        <h3>${section.title}</h3>
                        <p>${this.formatContent(section.content)}</p>
                        ${section.code ? this.renderCodeBlock(section.code) : ''}
                    </section>
                `).join('')}
            </div>
        `;

        this.pagination.innerText = `${this.currentChapterIndex + 1} / ${this.courseData.chapters.length}`;

        this.prevBtn.disabled = this.currentChapterIndex === 0;
        this.nextBtn.disabled = this.currentChapterIndex === this.courseData.chapters.length - 1;

        // Add listeners to "Executer" buttons
        this.contentArea.querySelectorAll('.course-exec-btn').forEach(btn => {
            btn.onclick = (e) => {
                const code = e.target.closest('.course-code-block').querySelector('.course-code-body').innerText;
                this.executeCode(code);
            };
        });
    }

    formatContent(text) {
        // Simple markdown-to-html conversion for basic needs
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    renderCodeBlock(code) {
        return `
            <div class="course-code-block">
                <div class="course-code-header">
                    <span>Exemple d'algorithme</span>
                    <button class="course-exec-btn"><i class="fas fa-play"></i> Charger dans l'éditeur</button>
                </div>
                <div class="course-code-body">${code}</div>
            </div>
        `;
    }

    executeCode(code) {
        if (window.editor) {
            window.editor.setValue(code);
            this.hide();
            // Optional: Trigger formatting or execution automatically
            // formatAlgoCode(window.editor);
            // document.getElementById('run-btn').click();
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.courseController = new CourseController();
});
