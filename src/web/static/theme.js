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

    // Global Badge Notification Polling
    window.checkNewBadges = async function () {
        // Only run if user is authenticated (checked via endpoint internally or global flag)
        try {
            const res = await fetch('/api/user/progress');
            const data = await res.json();
            if (data.success && data.progress.badges) {
                const unread = data.progress.badges.filter(b => b.earned && !b.seen);
                if (unread.length > 0) {
                    // Check if Swal is available
                    if (typeof Swal !== 'undefined') {
                        for (const badge of unread) {
                            await Swal.fire({
                                title: 'Nouveau Badge Débloqué !',
                                text: `${badge.name}: ${badge.description}`,
                                iconHtml: `<i class="${badge.icon}" style="color: #f1c40f;"></i>`,
                                customClass: { icon: 'no-border' },
                                background: document.body.classList.contains('light-theme') ? '#ffffff' : '#161b22',
                                color: document.body.classList.contains('light-theme') ? '#24292f' : '#c9d1d9',
                                confirmButtonColor: '#4a6ee0',
                                confirmButtonText: 'Génial !'
                            });
                        }
                    } else {
                        console.log("New badges unlocked:", unread.map(b => b.name).join(', '));
                    }

                    // Mark as seen
                    await fetch('/api/user/badges/seen', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ badge_ids: unread.map(b => b.id) })
                    });
                }
            }
        } catch (e) { console.error('Error checking badges', e); }
    }
})();
