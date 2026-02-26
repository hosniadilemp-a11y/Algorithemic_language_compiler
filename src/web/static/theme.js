(function () {
    const STORAGE_KEY = 'algocompiler.theme';

    function currentTheme() {
        return localStorage.getItem(STORAGE_KEY) || 'dark';
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

        window.dispatchEvent(new CustomEvent('themechange', {
            detail: { theme }
        }));
    }

    function toggleTheme() {
        const next = currentTheme() === 'dark' ? 'light' : 'dark';
        localStorage.setItem(STORAGE_KEY, next);
        applyTheme(next);
    }

    document.addEventListener('DOMContentLoaded', () => {
        applyTheme(currentTheme());
        document.querySelectorAll('[data-theme-toggle]').forEach((btn) => {
            btn.addEventListener('click', toggleTheme);
        });
    });
})();
