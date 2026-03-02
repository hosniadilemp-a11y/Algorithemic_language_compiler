document.addEventListener('DOMContentLoaded', () => {
    // 1. Split Pane Logic
    const vSplitter = document.getElementById('vertical-splitter');
    const problemPane = document.querySelector('.problem-pane');
    const editorPane = document.querySelector('.editor-pane');

    let isVSplitResizing = false;

    if (vSplitter) {
        vSplitter.addEventListener('mousedown', (e) => {
            isVSplitResizing = true;
            vSplitter.classList.add('dragging');
            document.body.style.cursor = 'col-resize';
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isVSplitResizing) return;
            const containerWidth = document.querySelector('.challenge-layout').offsetWidth;
            let newWidth = (e.clientX / containerWidth) * 100;
            // constraints
            if (newWidth < 20) newWidth = 20;
            if (newWidth > 60) newWidth = 60;

            problemPane.style.width = `${newWidth}%`;
            editorPane.style.width = `calc(${100 - newWidth}% - 5px)`;
            if (window.editor) window.editor.refresh();
        });

        document.addEventListener('mouseup', () => {
            if (isVSplitResizing) {
                isVSplitResizing = false;
                vSplitter.classList.remove('dragging');
                document.body.style.cursor = '';
            }
        });
    }

    // Horizontal Split Pane (Editor / Bottom)
    const hSplitter = document.getElementById('horizontal-splitter');
    const editorWrapper = document.querySelector('.editor-wrapper');
    const bottomPane = document.querySelector('.bottom-pane');
    let isHSplitResizing = false;

    if (hSplitter) {
        hSplitter.addEventListener('mousedown', (e) => {
            isHSplitResizing = true;
            hSplitter.classList.add('dragging');
            document.body.style.cursor = 'row-resize';
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isHSplitResizing) return;
            const editorPaneHeight = editorPane.offsetHeight;
            const editorPaneTop = editorPane.getBoundingClientRect().top;

            let newTopHeight = e.clientY - editorPaneTop;
            let percentage = (newTopHeight / editorPaneHeight) * 100;

            // Constraints
            if (percentage < 30) percentage = 30;
            if (percentage > 85) percentage = 85;

            editorWrapper.style.height = `calc(${percentage}% - 5px)`;
            bottomPane.style.height = `${100 - percentage}%`;

            if (window.editor) window.editor.refresh();
        });

        document.addEventListener('mouseup', () => {
            if (isHSplitResizing) {
                isHSplitResizing = false;
                hSplitter.classList.remove('dragging');
                document.body.style.cursor = '';
            }
        });
    }

    // 2. Tabs Logic
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active from all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.style.display = 'none');

            // Add active to clicked
            btn.classList.add('active');
            const target = document.getElementById(btn.getAttribute('data-target'));
            if (target) {
                if (target.id === 'tab-console') {
                    target.style.display = 'flex'; // Flex for split view
                } else {
                    target.style.display = 'block';
                }
            }
        });
    });

    // 3. Load Problem Data
    const problemId = Number(window.CURRENT_PROBLEM_ID);
    const titleEl = document.getElementById('problem-title');
    const topicEl = document.getElementById('problem-topic');
    const diffEl = document.getElementById('problem-difficulty');
    const descEl = document.getElementById('problem-description');
    const testsList = document.getElementById('test-cases-list');
    const testsTab = document.getElementById('tab-tests');
    const prevChallengeBtn = document.getElementById('prev-challenge-btn');
    const nextChallengeBtn = document.getElementById('next-challenge-btn');

    let currentProblem = null;

    function escapeHtml(text) {
        return String(text ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatSingleError(err) {
        if (typeof err === 'string') return err;
        if (err == null) return '';
        if (typeof err === 'object') {
            const line = err.line != null ? `Ligne ${err.line}` : null;
            const col = err.column != null ? `Col ${err.column}` : null;
            const type = err.type ? String(err.type) : null;
            const prefix = [type, line, col].filter(Boolean).join(' | ');
            const message = err.message || err.error || JSON.stringify(err);
            return prefix ? `${prefix}: ${message}` : String(message);
        }
        return String(err);
    }

    function formatErrorDetails(details) {
        if (!details) return [];
        if (Array.isArray(details)) return details.map(formatSingleError).filter(Boolean);
        return [formatSingleError(details)];
    }

    function renderRunError(message, details = []) {
        if (!testsTab) return;
        let box = document.getElementById('run-error-box');
        if (!box) {
            box = document.createElement('div');
            box.id = 'run-error-box';
            box.style.margin = '10px 0';
            box.style.padding = '10px';
            box.style.border = '1px solid #dc3545';
            box.style.borderRadius = '6px';
            box.style.background = 'rgba(220,53,69,0.1)';
            box.style.color = '#ff6b6b';
            box.style.fontFamily = 'monospace';
            box.style.whiteSpace = 'pre-wrap';
            testsTab.insertBefore(box, testsList);
        }
        const detailsHtml = details.length
            ? `<br>${details.map(d => escapeHtml(d)).join('<br>')}`
            : '';
        box.innerHTML = `<strong>Erreur:</strong> ${escapeHtml(message || 'Erreur inconnue')}${detailsHtml}`;
    }

    function clearRunError() {
        const box = document.getElementById('run-error-box');
        if (box) box.remove();
    }

    function setChallengeNavState(btn, targetProblemId) {
        if (!btn) return;
        if (targetProblemId == null) {
            btn.href = '#';
            btn.setAttribute('aria-disabled', 'true');
            return;
        }
        btn.href = `/challenge/${targetProblemId}`;
        btn.setAttribute('aria-disabled', 'false');
    }

    async function setupProblemNavigation() {
        try {
            const res = await fetch('/api/problems');
            const data = await res.json();
            if (!data.success || !Array.isArray(data.problems)) {
                setChallengeNavState(prevChallengeBtn, null);
                setChallengeNavState(nextChallengeBtn, null);
                return;
            }

            const ids = data.problems
                .map(p => Number(p.id))
                .filter(Number.isFinite)
                .sort((a, b) => a - b);

            const idx = ids.indexOf(problemId);
            const prevId = idx > 0 ? ids[idx - 1] : null;
            const nextId = idx >= 0 && idx < ids.length - 1 ? ids[idx + 1] : null;

            setChallengeNavState(prevChallengeBtn, prevId);
            setChallengeNavState(nextChallengeBtn, nextId);
        } catch (e) {
            setChallengeNavState(prevChallengeBtn, null);
            setChallengeNavState(nextChallengeBtn, null);
        }
    }

    async function loadProblem() {
        try {
            const res = await fetch(`/api/problems/${problemId}`);
            const data = await res.json();

            if (data.success) {
                currentProblem = data.problem;
                titleEl.textContent = currentProblem.title;
                topicEl.textContent = currentProblem.topic;
                diffEl.textContent = translateDifficulty(currentProblem.difficulty);
                diffEl.className = `difficulty-badge difficulty-${currentProblem.difficulty}`;

                // Render markdown
                descEl.innerHTML = marked.parse(currentProblem.description);

                // Render public test cases 
                renderTestCases(currentProblem.test_cases);

                // Initialize CodeMirror 
                setTimeout(() => {
                    const codeEditor = document.getElementById('code-editor');
                    if (!window.editor && codeEditor) {
                        window.editor = CodeMirror.fromTextArea(codeEditor, {
                            mode: "algo",
                            theme: document.body.classList.contains('light-theme') ? 'default' : 'dracula',
                            lineNumbers: true,
                            indentUnit: 4,
                            smartIndent: true,
                            styleActiveLine: true,
                            matchBrackets: true,
                            autoCloseBrackets: true,
                            extraKeys: {
                                "Ctrl-Space": "autocomplete"
                            },
                            hintOptions: {
                                hint: (CodeMirror.hint && CodeMirror.hint.algo) || (CodeMirror.helpers && CodeMirror.helpers.hint && CodeMirror.helpers.hint.algo) || CodeMirror.hint.anyword,
                                completeSingle: false,
                                alignWithWord: true,
                                closeOnUnfocus: true
                            }
                        });
                        window.editor.setSize("100%", "100%");

                        // Keep editor theme in sync when user toggles light/dark mode.
                        function applyEditorThemeFromBody() {
                            const isLight = document.body.classList.contains('light-theme');
                            window.editor.setOption('theme', isLight ? 'default' : 'dracula');
                        }
                        applyEditorThemeFromBody();
                        window.addEventListener('themechange', applyEditorThemeFromBody);

                        if (typeof window.initEditorUI === 'function') {
                            window.initEditorUI();
                        }

                        // Auto-trigger autocomplete after typing
                        let typingTimer;
                        window.editor.on("inputRead", function (cm, change) {
                            if (change.text[0].match(/[\w]/)) {
                                clearTimeout(typingTimer);
                                typingTimer = setTimeout(function () {
                                    var cursor = cm.getCursor();
                                    var token = cm.getTokenAt(cursor);
                                    if (token.string.length >= 2) {
                                        const hfn = (CodeMirror.hint && CodeMirror.hint.algo) || (CodeMirror.helpers && CodeMirror.helpers.hint && CodeMirror.helpers.hint.algo);
                                        if (hfn) {
                                            cm.showHint({ hint: hfn });
                                        }
                                    }
                                }, 300);
                            }
                        });

                        // Semicolon auto-insertion logic for Enter
                        window.editor.addKeyMap({
                            "Enter": function (cm) {
                                if (cm.getOption("disableInput")) return CodeMirror.Pass;
                                const cursor = cm.getCursor();
                                const line = cm.getLine(cursor.line);
                                const trimmedLine = line.trim();

                                if (trimmedLine.length > 0 &&
                                    !trimmedLine.startsWith("//") &&
                                    !/[;:\.\,\{\[\(\^]$/.test(trimmedLine) &&
                                    !/^(Algorithme|Var|Const|Debut|Alors|Faire|Sinon|Repeter|Type|Enregistrement|Fin|FinSi|FinPour|FinTantQue)/i.test(trimmedLine) &&
                                    !/\s+(Alors|Faire)$/i.test(trimmedLine)
                                ) {
                                    const lastCharIdx = line.search(/\S\s*$/);
                                    if (cursor.ch > lastCharIdx) {
                                        cm.replaceRange(";", { line: cursor.line, ch: line.length });
                                    }
                                }
                                return CodeMirror.Pass;
                            }
                        });
                    }
                    if (window.editor && !window.editor.getValue().trim()) {
                        window.editor.setValue(currentProblem.template_code);
                    }
                }, 100);

            } else {
                descEl.innerHTML = `<p class="error-msg">Erreur: ${data.error}</p>`;
            }
        } catch (e) {
            descEl.innerHTML = `<p class="error-msg">Erreur de connexion serveur.</p>`;
        }
    }

    function renderTestCases(tests) {
        if (!tests || tests.length === 0) {
            testsList.innerHTML = '<p>Aucun cas de test public disponible.</p>';
            return;
        }

        testsList.innerHTML = tests.map((tc, idx) => `
            <div class="test-case-card">
                <h4>Cas de test #${idx + 1}</h4>
                <strong>Entrée :</strong>
                <div class="io-block">${tc.input || '(Vide)'}</div>
                <strong>Sortie Attendue :</strong>
                <div class="io-block">${tc.expected_output || '(Vide)'}</div>
            </div>
        `).join('');
    }

    function translateDifficulty(diff) {
        switch (diff) {
            case 'Easy': return 'Facile';
            case 'Medium': return 'Moyen';
            case 'Hard': return 'Difficile';
            default: return diff;
        }
    }

    loadProblem();
    setupProblemNavigation();

    // 4. Execution Logic (Run Tests vs Submit vs Stdin)
    const runTestsBtn = document.getElementById('run-tests-btn');
    const submitBtn = document.getElementById('submit-btn');
    const runStdinBtn = document.getElementById('run-stdin-btn');

    async function executeCode(executeAll) {
        if (!window.editor) return;

        const code = window.editor.getValue();

        let originalRunBtnText = '';
        if (executeAll) {
            originalRunBtnText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Soumission...';
            submitBtn.disabled = true;
        } else {
            originalRunBtnText = runTestsBtn.innerHTML;
            runTestsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exécution...';
            runTestsBtn.disabled = true;
            document.querySelector('[data-target="tab-tests"]').click();
        }

        try {
            const res = await fetch('/api/submissions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    problem_id: problemId,
                    code: code,
                    execute_all: executeAll
                })
            });

            const data = await res.json();

            // Attach problem_id for 'réessayer' button
            data.problem_id = problemId;

            if (executeAll) {
                // Save to session cache and redirect
                sessionStorage.setItem('algo_submission_result', JSON.stringify(data));
                window.location.href = '/submission_results';
            } else {
                if (data.success) {
                    clearRunError();
                    renderTestResultsInContext(data);
                } else {
                    renderRunError(data.error || 'Erreur d’exécution', formatErrorDetails(data.details));
                }
            }
        } catch (e) {
            renderRunError('Erreur de connexion', [e.message]);
        } finally {
            if (executeAll) {
                submitBtn.innerHTML = originalRunBtnText;
                submitBtn.disabled = false;
            } else {
                runTestsBtn.innerHTML = originalRunBtnText;
                runTestsBtn.disabled = false;
            }
        }
    }

    function renderTestResultsInContext(data) {
        // Find the test cases UI
        const tcCards = document.querySelectorAll('.test-case-card');

        // Ensure accurate pairing
        data.results.forEach((r, i) => {
            if (i < tcCards.length) {
                const card = tcCards[i];
                // Remove old result if any
                const oldRes = card.querySelector('.tc-quick-result');
                if (oldRes) oldRes.remove();

                const resDiv = document.createElement('div');
                resDiv.className = `tc-quick-result ${r.passed ? 'passed' : 'failed'}`;
                resDiv.style.marginTop = '10px';
                resDiv.style.borderRadius = '4px';
                resDiv.style.overflow = 'hidden';
                resDiv.style.border = r.passed ? '1px solid #28a745' : '1px solid #dc3545';

                const header = document.createElement('div');
                header.style.padding = '8px';
                header.style.cursor = 'pointer';
                header.style.display = 'flex';
                header.style.justifyContent = 'space-between';
                header.style.alignItems = 'center';
                header.style.backgroundColor = r.passed ? 'rgba(40,167,69,0.1)' : 'rgba(220,53,69,0.1)';
                header.style.color = r.passed ? '#28a745' : '#dc3545';
                header.style.fontWeight = 'bold';
                header.innerHTML = `<span>${r.passed ? '<i class="fas fa-check"></i> Réussi' : '<i class="fas fa-times"></i> Échoué'}</span> <i class="fas fa-chevron-down"></i>`;

                const body = document.createElement('div');
                body.style.padding = '8px';
                body.style.display = r.passed ? 'none' : 'block'; // Hide by default if passed, show if failed
                body.style.backgroundColor = 'var(--bg-color, #1e1e1e)';
                body.style.color = 'var(--text-color, #e0e0e0)';
                body.style.fontSize = '0.9em';
                body.style.fontFamily = 'monospace';

                let detailsHtml = '';
                if (r.error && r.error !== 'Execution Failed') {
                    detailsHtml = `<div style="color:#ff6b6b; white-space: pre-wrap;">${escapeHtml(formatSingleError(r.error))}</div>`;
                } else {
                    detailsHtml = `
                        <div style="margin-bottom: 5px; white-space: pre-wrap;"><strong>Entrée :</strong> ${escapeHtml(r.input || '(Vide)')}</div>
                        <div style="margin-bottom: 5px; white-space: pre-wrap;"><strong>Attendu :</strong> ${escapeHtml(r.expected_output || '(Vide)')}</div>
                        <div style="white-space: pre-wrap;"><strong>Votre Sortie :</strong> <span style="color:${r.passed ? '#28a745' : '#ff6b6b'}">${escapeHtml(r.actual_output || '(Rien)')}</span></div>
                    `;
                }
                body.innerHTML = detailsHtml;

                header.onclick = () => {
                    const isHidden = body.style.display === 'none';
                    body.style.display = isHidden ? 'block' : 'none';
                    header.querySelector('i:last-child').className = isHidden ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
                };

                resDiv.appendChild(header);
                resDiv.appendChild(body);
                card.appendChild(resDiv);
            }
        });
    }

    async function executeStdin() {
        if (!window.editor) return;

        // Switch to console tab automatically
        document.querySelector('[data-target="tab-console"]').click();

        const code = window.editor.getValue();
        const customInput = document.getElementById('custom-input').value;
        const consoleLogs = document.getElementById('console-logs');

        consoleLogs.innerHTML = '<span style="color:#888;">Exécution en cours...</span>';

        try {
            const res = await fetch('/api/submissions/custom', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code: code,
                    input: customInput
                })
            });

            const data = await res.json();

            if (data.success && data.results && data.results.length > 0) {
                const r = data.results[0];
                if (r.error && r.error !== 'Execution Failed') {
                    consoleLogs.innerHTML = `<span style="color:#ff6b6b; white-space: pre-wrap;">${escapeHtml(formatSingleError(r.error))}</span>`;
                } else {
                    consoleLogs.innerHTML = `<span style="white-space: pre-wrap;">${escapeHtml(r.actual_output || '(Aucune Sortie)')}</span>`;
                }
            } else {
                const details = formatErrorDetails(data.details);
                consoleLogs.innerHTML = `<span style="color:#ff6b6b; white-space: pre-wrap;">Erreur: ${escapeHtml(data.error || 'Erreur inconnue')}</span>`;
                if (details.length) {
                    consoleLogs.innerHTML += `<br><span style="color:#ff6b6b; white-space: pre-wrap;">${details.map(d => escapeHtml(d)).join('<br>')}</span>`;
                }
            }
        } catch (e) {
            consoleLogs.innerHTML = `<span style="color:#ff6b6b; white-space: pre-wrap;">Erreur de connexion: ${escapeHtml(e.message)}</span>`;
        }
    }

    if (runTestsBtn) runTestsBtn.addEventListener('click', () => executeCode(false));
    if (submitBtn) submitBtn.addEventListener('click', () => executeCode(true));
    if (runStdinBtn) runStdinBtn.addEventListener('click', () => executeStdin());

    // Clear Console
    const clearBtn = document.getElementById('clear-console-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            document.getElementById('console-logs').innerHTML = '';
        });
    }

});
