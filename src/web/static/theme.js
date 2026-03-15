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

    function ensureConfettiCanvas() {
        let canvas = document.getElementById('global-confetti-canvas');
        if (canvas) return canvas;
        canvas = document.createElement('canvas');
        canvas.id = 'global-confetti-canvas';
        canvas.style.position = 'fixed';
        canvas.style.inset = '0';
        canvas.style.pointerEvents = 'none';
        canvas.style.zIndex = '9999';
        document.body.appendChild(canvas);
        return canvas;
    }

    function launchConfetti(durationMs = 2500) {
        const canvas = ensureConfettiCanvas();
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        let w = canvas.width = window.innerWidth;
        let h = canvas.height = window.innerHeight;
        const colors = ['#f94144', '#f3722c', '#f9c74f', '#90be6d', '#43aa8b', '#577590'];
        const pieces = Array.from({ length: 140 }).map(() => ({
            x: Math.random() * w,
            y: Math.random() * h - h,
            vx: (Math.random() - 0.5) * 2,
            vy: 2 + Math.random() * 3,
            size: 6 + Math.random() * 6,
            rot: Math.random() * Math.PI,
            vr: (Math.random() - 0.5) * 0.2,
            color: colors[Math.floor(Math.random() * colors.length)]
        }));
        const resize = () => {
            w = canvas.width = window.innerWidth;
            h = canvas.height = window.innerHeight;
        };
        window.addEventListener('resize', resize);
        const start = performance.now();
        const frame = (t) => {
            ctx.clearRect(0, 0, w, h);
            pieces.forEach(p => {
                p.x += p.vx;
                p.y += p.vy;
                p.rot += p.vr;
                if (p.y > h) {
                    p.y = -10;
                    p.x = Math.random() * w;
                }
                ctx.save();
                ctx.translate(p.x, p.y);
                ctx.rotate(p.rot);
                ctx.fillStyle = p.color;
                ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
                ctx.restore();
            });
            if (t - start < durationMs) {
                requestAnimationFrame(frame);
            } else {
                ctx.clearRect(0, 0, w, h);
                window.removeEventListener('resize', resize);
            }
        };
        requestAnimationFrame(frame);
    }
    window.launchConfetti = launchConfetti;

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
                            launchConfetti();
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
