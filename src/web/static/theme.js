(function () {
    const STORAGE_KEY = 'algocompiler.theme';

    function currentTheme() {
        try {
            return localStorage.getItem(STORAGE_KEY) || 'dark';
        } catch (error) {
            return 'dark';
        }
    }

    function applyTheme(theme) {
        const isLight = theme === 'light';
        document.body.classList.toggle('light-theme', isLight);
        const toggles = document.querySelectorAll('[data-theme-toggle]');
        toggles.forEach((btn) => {
            const icon = btn.querySelector('i');
            if (icon) {
                icon.className = isLight ? 'fas fa-moon' : 'fas fa-sun';
            }
            const label = btn.querySelector('.theme-label');
            if (label) {
                label.textContent = isLight ? 'Mode Sombre' : 'Mode Clair';
            }
            btn.title = isLight ? 'Passer en mode sombre' : 'Passer en mode clair';
        });

        try {
            if (typeof CustomEvent === 'function') {
                window.dispatchEvent(new CustomEvent('themechange', {
                    detail: { theme }
                }));
            } else {
                window.dispatchEvent(new Event('themechange'));
            }
        } catch (error) {
            // Theme change notification is optional.
        }
    }

    function toggleTheme() {
        const next = currentTheme() === 'dark' ? 'light' : 'dark';
        try {
            localStorage.setItem(STORAGE_KEY, next);
        } catch (error) {
            // Ignore storage failures (private mode/restrictions).
        }
        applyTheme(next);
    }

    document.addEventListener('DOMContentLoaded', () => {
        try {
            applyTheme(currentTheme());
            document.querySelectorAll('[data-theme-toggle]').forEach((btn) => {
                btn.addEventListener('click', toggleTheme);
            });
        } catch (error) {
            // Never block app initialization if theme setup fails.
            console.warn('Theme initialization skipped:', error);
        }
    });
})();
