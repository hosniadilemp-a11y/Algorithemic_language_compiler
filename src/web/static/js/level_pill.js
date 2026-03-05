/**
 * level_pill.js
 * Injects a glowing level badge pill next to the username button in the header.
 * Uses localStorage (5 min cache) to avoid hammering /api/user/progress on every page.
 */
(function () {
    const CACHE_KEY = 'algo_user_level_cache';
    const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

    function injectPill(level) {
        // Find the profile link (the one with fas fa-user-circle)
        const profileLink = document.querySelector('a.auth-btn[href="/progress"]');
        if (!profileLink) return;
        // Avoid double-injection
        if (document.getElementById('header-level-pill')) return;

        // Find the profile link's span where the name is
        const nameSpan = profileLink.querySelector('span');
        if (!nameSpan) return;

        // APPLY THEME COLORS TO THE PROFILE LINK
        profileLink.style.color = level.color;
        profileLink.style.borderColor = level.color;
        // Ensure the span inherits the color so the name is also colored
        nameSpan.style.color = 'inherit';

        const pill = document.createElement('span');
        pill.id = 'header-level-pill';
        pill.textContent = `${level.icon}`;
        pill.style.cssText = `
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 1px 8px;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 700;
            color: inherit; /* inherit from profileLink */
            border: 1px solid currentColor;
            margin-left: 8px;
            background: rgba(0, 0, 0, 0.15);
            cursor: pointer;
            white-space: nowrap;
            vertical-align: middle;
            transition: all 0.2s;
        `;

        // Wrap the name and pill in a flex container if needed, or just append
        profileLink.style.display = 'inline-flex';
        profileLink.style.alignItems = 'center';
        profileLink.appendChild(pill);
    }

    async function loadLevel() {
        // Try cache
        try {
            const cached = localStorage.getItem(CACHE_KEY);
            if (cached) {
                const obj = JSON.parse(cached);
                if (Date.now() - obj.ts < CACHE_TTL) {
                    injectPill(obj.level);
                    return;
                }
            }
        } catch (e) { /* ignore */ }

        // Fetch fresh
        try {
            const res = await fetch('/api/user/progress');
            if (!res.ok) return;
            const data = await res.json();
            if (data.success && data.progress && data.progress.level) {
                const level = data.progress.level;
                localStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), level }));
                injectPill(level);
            }
        } catch (e) { /* silently ignore network errors */ }
    }

    // Only run for authenticated users (check if profile link exists)
    document.addEventListener('DOMContentLoaded', () => {
        const profileLink = document.querySelector('a.auth-btn[href="/progress"]');
        if (profileLink) loadLevel();
    });
})();
