document.addEventListener('DOMContentLoaded', () => {
    const problemsList = document.getElementById('problems-list');
    const topicFilter = document.getElementById('topic-filter');
    const difficultyFilter = document.getElementById('difficulty-filter');

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
        const topic = topicFilter.value;
        const difficulty = difficultyFilter.value;

        let url = '/api/problems?';
        if (topic) url += `topic=${topic}&`;
        if (difficulty) url += `difficulty=${difficulty}`;

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

    function renderProblems(problems) {
        if (!problems || problems.length === 0) {
            problemsList.innerHTML = '<div class="no-results">Aucun défi trouvé pour ces critères.</div>';
            return;
        }

        const solved = getSolvedProblems();

        problemsList.innerHTML = problems.map(p => {
            // Use API 'solved' status if provided, otherwise fallback to cookie
            const isSolved = (p.solved !== null && p.solved !== undefined) ? p.solved : solved.has(p.id);

            return `
            <div class="problem-card ${isSolved ? 'solved' : ''}">
                <div class="problem-info">
                    <h3>${p.title}</h3>
                    <p class="problem-snippet">${p.description ? p.description.replace(/<[^>]*>?/gm, '').replace(/[#*`]/g, '').trim().substring(0, 100) + '...' : ''}</p>
                    <div class="problem-meta">
                        <span class="topic-tag"><i class="fas fa-tag"></i> ${p.topic}</span>
                        <span class="difficulty-badge difficulty-${p.difficulty}">${translateDifficulty(p.difficulty)}</span>
                        <span class="solver-count"><i class="fas fa-user-clock"></i> Pris: ${p.attempted_users || 0}</span>
                        <span class="solver-count"><i class="fas fa-percentage"></i> Réussite: ${(p.success_rate ?? 0)}%</span>
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

    topicFilter.addEventListener('change', fetchProblems);
    difficultyFilter.addEventListener('change', fetchProblems);

    // Initial load
    fetchProblems();
});
