document.addEventListener('DOMContentLoaded', () => {
    const problemsList = document.getElementById('problems-list');
    const topicFilters = document.querySelectorAll('#topic-filters input[type="checkbox"]');
    const difficultyFilters = document.querySelectorAll('#difficulty-filters input[type="checkbox"]');
    const resetBtn = document.getElementById('reset-filters');
    const FILTER_KEY = 'algo_problem_filters';

    function getCookie(name) {
        const raw = document.cookie
            .split('; ')
            .find(row => row.startsWith(name + '='));
        return raw ? decodeURIComponent(raw.split('=')[1]) : '';
    }

    function getSolvedProblems() {
        const cookie = getCookie('algo_solved_problems');
        if (!cookie) return new Set();
        return new Set(
            cookie
                .split(',')
                .map(v => Number(v.trim()))
                .filter(Number.isFinite)
        );
    }

    async function fetchProblems() {
        const topics = Array.from(topicFilters).filter(i => i.checked).map(i => i.value);
        const difficulties = Array.from(difficultyFilters).filter(i => i.checked).map(i => i.value);

        let url = '/api/problems?';
        topics.forEach(t => url += `topic=${encodeURIComponent(t)}&`);
        difficulties.forEach(d => url += `difficulty=${encodeURIComponent(d)}&`);

        try {
            problemsList.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Chargement des défis...</div>';

            const response = await fetch(url);
            const data = await response.json();

            if (data.success) {
                renderProblems(data.problems);
            } else {
                problemsList.innerHTML = `<div class="error-msg">Erreur: ${data.error}</div>`;
            }
        } catch (error) {
            problemsList.innerHTML = `<div class="error-msg">Erreur de connexion serveur: ${error.message}</div>`;
        }
    }

    function saveFilters() {
        const topics = Array.from(topicFilters).filter(i => i.checked).map(i => i.value);
        const difficulties = Array.from(difficultyFilters).filter(i => i.checked).map(i => i.value);
        try {
            localStorage.setItem(FILTER_KEY, JSON.stringify({ topics, difficulties }));
        } catch (e) {
            // ignore storage errors
        }
    }

    function restoreFilters() {
        try {
            const raw = localStorage.getItem(FILTER_KEY);
            if (!raw) return;
            const data = JSON.parse(raw);
            const topics = new Set(data.topics || []);
            const diffs = new Set(data.difficulties || []);
            topicFilters.forEach(cb => { cb.checked = topics.has(cb.value); });
            difficultyFilters.forEach(cb => { cb.checked = diffs.has(cb.value); });
        } catch (e) {
            // ignore parse errors
        }
    }

    function renderProblems(problems) {
        if (!problems || problems.length === 0) {
            problemsList.innerHTML = '<div class="no-results" style="text-align:center; padding: 40px; color: #888;">' +
                '<i class="fas fa-search" style="font-size: 3rem; margin-bottom: 20px; display: block; opacity: 0.5;"></i>' +
                'Aucun défi trouvé pour ces critères.</div>';
            return;
        }

        const solved = getSolvedProblems();

        problemsList.innerHTML = problems.map(p => {
            const isSolved = (p.solved !== null && p.solved !== undefined) ? p.solved : solved.has(p.id);

            return `
            <div class="problem-card ${isSolved ? 'solved' : ''}">
                <div class="problem-info">
                    <h3>${p.title}</h3>
                    <p class="problem-snippet">${p.description ? p.description.replace(/<[^>]*>?/gm, '').replace(/[#*`]/g, '').trim().substring(0, 150) + '...' : ''}</p>
                    <div class="problem-meta">
                        <span class="topic-tag"><i class="fas fa-tag"></i> ${p.topic}</span>
                        <span class="difficulty-badge difficulty-${p.difficulty}">${translateDifficulty(p.difficulty)}</span>
                        <span class="solver-count" title="Utilisateurs ayant tenté"><i class="fas fa-user-clock"></i> ${p.attempted_users || 0}</span>
                        <span class="solver-count" title="Taux de réussite"><i class="fas fa-percentage"></i> ${(p.success_rate ?? 0)}%</span>
                        ${isSolved ? '<span class="done-badge"><i class="fas fa-check-circle"></i> Terminé</span>' : ''}
                    </div>
                </div>
                <div class="problem-actions">
                    <a href="/challenge/${p.id}" class="btn-solve ${isSolved ? 'done' : ''}">${isSolved ? 'Revoir' : 'Résoudre'} <i class="fas fa-arrow-right"></i></a>
                </div>
            </div>
        `;
        }).join('');
    }

    function translateDifficulty(diff) {
        switch (diff) {
            case 'Easy': return 'Facile';
            case 'Medium': return 'Moyen';
            case 'Hard': return 'Difficile';
            default: return diff;
        }
    }

    // Add listeners to all checkboxes
    [...topicFilters, ...difficultyFilters].forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            saveFilters();
            fetchProblems();
        });
    });

    // Reset logic
    resetBtn.addEventListener('click', () => {
        [...topicFilters, ...difficultyFilters].forEach(checkbox => {
            checkbox.checked = false;
        });
        try { localStorage.removeItem(FILTER_KEY); } catch (e) {}
        fetchProblems();
    });

    // Initial load
    restoreFilters();
    fetchProblems();
});
