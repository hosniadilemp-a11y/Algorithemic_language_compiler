document.addEventListener('DOMContentLoaded', () => {
    const runBtn = document.getElementById('run-btn');
    const downloadBtn = document.getElementById('download-btn');
    const clearConsoleBtn = document.getElementById('clear-console-btn');
    const filenameInput = document.getElementById('filename-input');
    const codeEditorElement = document.getElementById('code-editor');
    const consoleLogs = document.getElementById('console-logs');
    const consoleInputContainer = document.getElementById('console-input-container');
    const consoleInput = document.getElementById('console-input');

    // Examples Sidebar Elements
    const openExamplesBtn = document.getElementById('open-examples-btn');
    const closeExamplesBtn = document.getElementById('close-examples-btn');
    const examplesSidebar = document.getElementById('examples-sidebar');
    const examplesOverlay = document.getElementById('examples-overlay');
    const examplesContent = document.getElementById('examples-content');

    const variablesBody = document.querySelector('#variables-table tbody');
    const statusBadge = document.getElementById('status-badge');
    const fileStateBadge = document.getElementById('file-state');

    let eventSource = null;
    let editor = null;

    // Initialize CodeMirror with sophisticated IDE features
    if (codeEditorElement) {
        window.editor = CodeMirror.fromTextArea(codeEditorElement, {
            mode: "algo", // Use custom mode from algo-mode.js
            theme: "dracula",
            lineNumbers: true,
            lineWrapping: false,
            indentUnit: 4,
            smartIndent: true,
            tabSize: 4,
            indentWithTabs: false,

            // Bracket and tag matching
            matchBrackets: true,
            autoCloseBrackets: true,

            // Active line highlighting
            styleActiveLine: true,
            // Code folding with custom Algo fold helper
            foldGutter: true,
            gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],

            // Scrollbar
            scrollbarStyle: "simple",

            // Selection
            showCursorWhenSelecting: true,

            // Keyboard shortcuts and commands
            extraKeys: {
                "Ctrl-Space": "autocomplete",        // Autocomplete
                "Ctrl-/": "toggleComment",           // Toggle comment
                "Ctrl-F": "find",                    // Find
                "Ctrl-H": "replace",                 // Replace
                "Ctrl-G": "jumpToLine",              // Go to line
                "Alt-G": "jumpToLine",               // Alternative go to line
                "Ctrl-Z": "undo",                    // Undo
                "Ctrl-Y": "redo",                    // Redo
                "Ctrl-Shift-Z": "redo",              // Alternative redo
                "Ctrl-S": function (cm) {             // Save file
                    saveFile();
                    return false; // Prevent browser save dialog
                },
                "Ctrl-N": function (cm) {             // New file
                    newFile();
                    return false;
                },
                "Ctrl-O": function (cm) {             // Open file
                    document.getElementById('file-input').click();
                    return false;
                },
                "Ctrl-D": function (cm) {             // Select next occurrence
                    var sel = cm.getSelection();
                    if (sel) {
                        var cursor = cm.getCursor();
                        var searchCursor = cm.getSearchCursor(sel, cursor);
                        if (searchCursor.findNext()) {
                            cm.addSelection(searchCursor.from(), searchCursor.to());
                        }
                    }
                },
                "Ctrl-Shift-D": function (cm) {       // Duplicate line
                    var cursor = cm.getCursor();
                    var line = cm.getLine(cursor.line);
                    cm.replaceRange('\n' + line, { line: cursor.line, ch: line.length });
                },
                "Alt-Up": function (cm) {             // Move line up
                    var cursor = cm.getCursor();
                    if (cursor.line > 0) {
                        var line = cm.getLine(cursor.line);
                        cm.replaceRange("", { line: cursor.line, ch: 0 }, { line: cursor.line + 1, ch: 0 });
                        cm.replaceRange(line + "\n", { line: cursor.line - 1, ch: 0 });
                        cm.setCursor({ line: cursor.line - 1, ch: cursor.ch });
                    }
                },
                "Alt-Down": function (cm) {           // Move line down
                    var cursor = cm.getCursor();
                    if (cursor.line < cm.lineCount() - 1) {
                        var line = cm.getLine(cursor.line);
                        cm.replaceRange("", { line: cursor.line, ch: 0 }, { line: cursor.line + 1, ch: 0 });
                        cm.replaceRange(line + "\n", { line: cursor.line + 1, ch: 0 });
                        cm.setCursor({ line: cursor.line + 1, ch: cursor.ch });
                    }
                },
                "Ctrl-Shift-F": function (cm) {       // Format code
                    formatAlgoCode(cm);
                },
                "Shift-Ctrl-F": function (cm) {       // Format code
                    formatAlgoCode(cm);
                },
                "Alt-Shift-F": function (cm) {        // VS Code style
                    formatAlgoCode(cm);
                },
                "Tab": function (cm) {
                    // Smart tab: indent or insert spaces
                    if (cm.somethingSelected()) {
                        cm.indentSelection("add");
                    } else {
                        cm.replaceSelection("    ");
                    }
                },
                "Shift-Tab": function (cm) {          // Unindent
                    cm.indentSelection("subtract");
                },
                "F11": function (cm) {                // Fullscreen
                    cm.setOption("fullScreen", !cm.getOption("fullScreen"));
                },
                "Enter": function (cm) {
                    if (cm.getOption("disableInput")) return CodeMirror.Pass;
                    const cursor = cm.getCursor();
                    const line = cm.getLine(cursor.line);
                    const trimmedLine = line.trim();

                    // Auto-semicolon logic:
                    // If line is not empty, not a comment, doesn't end in punctuation that doesn't need a semicolon,
                    // and doesn't end in keywords that start/end blocks.
                    if (trimmedLine.length > 0 &&
                        !trimmedLine.startsWith("//") &&
                        !/[;:\.\,\{\[\(\^]$/.test(trimmedLine) &&
                        !/^(Algorithme|Var|Const|Debut|Alors|Faire|Sinon|Repeter|Type|Enregistrement|Fin|FinSi|FinPour|FinTantQue)/i.test(trimmedLine) &&
                        !/\s+(Alors|Faire)$/i.test(trimmedLine)
                    ) {
                        // Insert semicolon at the end of the line if the cursor is at or after the last non-space character
                        const lastCharIdx = line.search(/\S\s*$/);
                        if (cursor.ch > lastCharIdx) {
                            cm.replaceRange(";", { line: cursor.line, ch: line.length });
                        }
                    }
                    return CodeMirror.Pass;
                }
            },

            // Enable undo/redo history
            undoDepth: 200,
            historyEventDelay: 1000,

            // Autocomplete options
            hintOptions: {
                hint: (CodeMirror.helpers.hint && CodeMirror.helpers.hint.algo) || CodeMirror.hint.anyword,
                completeSingle: false,
                alignWithWord: true,
                closeOnUnfocus: true
            }
        });

        editor.setSize("100%", null); // Let flex handle height

        // If code was requested from the standalone course page, inject it on load.
        try {
            const pendingCourseCode = localStorage.getItem('algocompiler.pendingCourseCode');
            if (pendingCourseCode) {
                editor.setValue(pendingCourseCode);
                localStorage.removeItem('algocompiler.pendingCourseCode');
            }
        } catch (error) {
            console.warn("Unable to read pending course code from storage:", error);
        }

        // Auto-trigger autocomplete after typing
        let typingTimer;
        editor.on("inputRead", function (cm, change) {
            if (change.text[0].match(/[\w]/)) {
                clearTimeout(typingTimer);
                typingTimer = setTimeout(function () {
                    // Only show if user has typed at least 2 characters
                    var cursor = cm.getCursor();
                    var token = cm.getTokenAt(cursor);
                    if (token.string.length >= 2) {
                        cm.showHint({ hint: CodeMirror.helpers.hint.algo });
                    }
                }, 300); // 300ms delay
            }
        });

        // Fullscreen mode handler
        editor.on("optionChange", function (cm, option) {
            if (option === "fullScreen") {
                var wrap = cm.getWrapperElement();
                if (cm.getOption("fullScreen")) {
                    wrap.style.position = "fixed";
                    wrap.style.top = "0";
                    wrap.style.left = "0";
                    wrap.style.right = "0";
                    wrap.style.bottom = "0";
                    wrap.style.zIndex = "9999";
                } else {
                    wrap.style.position = "";
                    wrap.style.top = "";
                    wrap.style.left = "";
                    wrap.style.right = "";
                    wrap.style.bottom = "";
                    wrap.style.zIndex = "";
                }
            }
        });
    }

    // Code formatting function for Algo - Refined for structural alignment
    function formatAlgoCode(cm) {
        var code = cm.getValue();
        var lines = code.split('\n');
        var formatted = [];
        var indentLevel = 0;
        var indentStr = '    '; // 4 spaces

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();

            // Decrease indent BEFORE the line for block-closing or section-switching keywords
            // These keywords should shift back out to the same level as their header
            if (/^(Fin|Sinon|Jusqua|Debut|Var|Const|Type)/i.test(line)) {
                indentLevel = Math.max(0, indentLevel - 1);
            }

            // Add formatted line
            if (line) {
                formatted.push(indentStr.repeat(indentLevel) + line);
            } else {
                formatted.push('');
            }

            // Increase indent AFTER the line for block-opening keywords
            // Note: Algorithme, Fonction, Procedure themselves don't increase indent
            // because the next line is usually Var/Debut which will handle its own indent.
            if (/^(Var|Const|Debut|Si|Sinon|Pour\s|Tant\s*Que\s|Repeter|Type|Enregistrement)/i.test(line) ||
                /\s+(Alors|Faire|Enregistrement)$/i.test(line)) {
                indentLevel++;
            }
        }

        cm.setValue(formatted.join('\n'));
    }

    // ═══════════════════════════════════════════════════════════
    // STATUS BAR — live cursor position, char count, line count
    // ═══════════════════════════════════════════════════════════
    const statusCursor = document.getElementById('status-cursor');
    const statusChars = document.getElementById('status-chars');
    const statusLines = document.getElementById('status-lines');
    const statusFontSize = document.getElementById('status-fontsize');

    function updateStatusBar() {
        if (!editor) return;
        const cursor = editor.getCursor();
        const line = cursor.line + 1;
        const col = cursor.ch + 1;
        const text = editor.getValue();
        const charCount = text.length;
        const lineCount = editor.lineCount();

        if (statusCursor) statusCursor.innerHTML = `<i class="fas fa-map-pin"></i> Ln ${line}, Col ${col}`;
        if (statusChars) statusChars.innerHTML = `<i class="fas fa-font"></i> ${charCount.toLocaleString()} car.`;
        if (statusLines) statusLines.innerHTML = `<i class="fas fa-list-ol"></i> ${lineCount} lignes`;
    }

    if (editor) {
        editor.on('cursorActivity', updateStatusBar);
        editor.on('change', updateStatusBar);
        updateStatusBar(); // initial
    }

    // ═══════════════════════════════════════════════════════════
    // FONT SIZE ZOOM — buttons + Ctrl+= / Ctrl+-
    // ═══════════════════════════════════════════════════════════
    let currentFontSize = 14;
    const MIN_FONT = 10;
    const MAX_FONT = 24;
    const DEFAULT_FONT = 14;

    function applyFontSize(size) {
        currentFontSize = Math.min(MAX_FONT, Math.max(MIN_FONT, size));
        if (editor) {
            editor.getWrapperElement().style.fontSize = currentFontSize + 'px';
            editor.refresh();
        }
        if (statusFontSize) statusFontSize.textContent = currentFontSize + 'px';
    }

    const fontIncBtn = document.getElementById('font-increase-btn');
    const fontDecBtn = document.getElementById('font-decrease-btn');
    const fontResetBtn = document.getElementById('font-reset-btn');

    if (fontIncBtn) fontIncBtn.addEventListener('click', () => applyFontSize(currentFontSize + 1));
    if (fontDecBtn) fontDecBtn.addEventListener('click', () => applyFontSize(currentFontSize - 1));
    if (fontResetBtn) fontResetBtn.addEventListener('click', () => applyFontSize(DEFAULT_FONT));

    // Ctrl+= to increase, Ctrl+- to decrease
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && (e.key === '=' || e.key === '+')) {
            e.preventDefault();
            applyFontSize(currentFontSize + 1);
        }
        if (e.ctrlKey && e.key === '-') {
            e.preventDefault();
            applyFontSize(currentFontSize - 1);
        }
        if (e.ctrlKey && e.key === '0') {
            e.preventDefault();
            applyFontSize(DEFAULT_FONT);
        }
        // F5 to run
        if (e.key === 'F5') {
            e.preventDefault();
            runBtn && runBtn.click();
        }
    });

    // ═══════════════════════════════════════════════════════════
    // WORD WRAP TOGGLE
    // ═══════════════════════════════════════════════════════════
    let wordWrapEnabled = false;
    const wordWrapBtn = document.getElementById('wordwrap-btn');

    function toggleWordWrap() {
        wordWrapEnabled = !wordWrapEnabled;
        if (editor) editor.setOption('lineWrapping', wordWrapEnabled);
        if (wordWrapBtn) wordWrapBtn.classList.toggle('active', wordWrapEnabled);
    }

    if (wordWrapBtn) wordWrapBtn.addEventListener('click', toggleWordWrap);

    // ═══════════════════════════════════════════════════════════
    // FULLSCREEN BUTTON (in pane header)
    // ═══════════════════════════════════════════════════════════
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    if (fullscreenBtn && editor) {
        fullscreenBtn.addEventListener('click', () => {
            const isFS = editor.getOption('fullScreen');
            editor.setOption('fullScreen', !isFS);
            fullscreenBtn.title = isFS ? 'Plein Écran (F11)' : 'Quitter le plein écran (F11)';
            fullscreenBtn.innerHTML = isFS
                ? '<i class="fas fa-expand"></i>'
                : '<i class="fas fa-compress"></i>';
        });
        // Also update button icon when F11 is used
        editor.on('optionChange', (cm, opt) => {
            if (opt === 'fullScreen' && fullscreenBtn) {
                const isFS = cm.getOption('fullScreen');
                fullscreenBtn.innerHTML = isFS
                    ? '<i class="fas fa-compress"></i>'
                    : '<i class="fas fa-expand"></i>';
            }
        });
    }

    // ═══════════════════════════════════════════════════════════
    // KEYBOARD SHORTCUTS MODAL
    // ═══════════════════════════════════════════════════════════
    const shortcutsBtn = document.getElementById('shortcuts-btn');
    const shortcutsModal = document.getElementById('shortcuts-modal');
    const shortcutsOverlay = document.getElementById('shortcuts-overlay');
    const closeShortcutsBtn = document.getElementById('close-shortcuts-btn');

    function openShortcutsModal() {
        shortcutsModal.style.display = 'block';
        shortcutsOverlay.style.display = 'block';
    }

    function closeShortcutsModal() {
        shortcutsModal.style.display = 'none';
        shortcutsOverlay.style.display = 'none';
    }

    if (shortcutsBtn) shortcutsBtn.addEventListener('click', openShortcutsModal);
    if (closeShortcutsBtn) closeShortcutsBtn.addEventListener('click', closeShortcutsModal);
    if (shortcutsOverlay) shortcutsOverlay.addEventListener('click', closeShortcutsModal);
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && shortcutsModal && shortcutsModal.style.display !== 'none') {
            closeShortcutsModal();
        }
    });

    // ═══════════════════════════════════════════════════════════
    // RESIZABLE PANE SPLITTER
    // ═══════════════════════════════════════════════════════════
    const splitter = document.getElementById('pane-splitter');
    const editorPane = document.querySelector('.editor-pane');
    const outputPane = document.querySelector('.output-pane');
    const editorLayout = document.querySelector('.editor-layout');

    if (splitter && editorPane && outputPane) {
        let isResizing = false;
        let startX = 0;
        let startEditorWidth = 0;

        splitter.addEventListener('mousedown', (e) => {
            isResizing = true;
            startX = e.clientX;
            startEditorWidth = editorPane.getBoundingClientRect().width;
            splitter.classList.add('dragging');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            const layoutWidth = editorLayout.getBoundingClientRect().width;
            const delta = e.clientX - startX;
            let newEditorWidth = startEditorWidth + delta;
            // Enforce min/max: each pane must be at least 250px
            newEditorWidth = Math.max(250, Math.min(layoutWidth - 255, newEditorWidth));
            const newOutputWidth = layoutWidth - newEditorWidth - 5; // 5 = splitter width
            editorPane.style.flex = 'none';
            editorPane.style.width = newEditorWidth + 'px';
            outputPane.style.flex = 'none';
            outputPane.style.width = newOutputWidth + 'px';
            if (editor) editor.refresh();
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                splitter.classList.remove('dragging');
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
    }

    // File management variables
    let currentFileName = "programme.algo";
    let isModified = false;
    let fileHandle = null; // Store the file handle for File System Access API


    // Track modifications
    if (editor) {
        editor.on("change", function () {
            isModified = true;
            updateTitle();
        });
    }

    // Update window title and UI with file name and modified status
    function updateTitle() {
        const modifiedMark = isModified ? " *" : "";
        document.title = `${currentFileName}${modifiedMark} - AlgoCompiler`;

        if (filenameInput && filenameInput.value !== currentFileName) {
            filenameInput.value = currentFileName;
        }

        if (fileStateBadge) {
            if (isModified) {
                fileStateBadge.style.display = 'inline-block';
                fileStateBadge.style.backgroundColor = '#d29922'; // Yellow/Orange
                fileStateBadge.textContent = "Non enregistré";
            } else {
                fileStateBadge.style.display = 'none';
            }
        }
    }

    // Handle filename input changes
    if (filenameInput) {
        filenameInput.addEventListener('change', (e) => {
            let newName = e.target.value.trim();
            if (!newName.endsWith('.algo')) {
                newName += '.algo';
            }
            currentFileName = newName;
            fileHandle = null; // Clear handle on manual rename
            updateTitle();
        });
    }

    // Clear Console
    if (clearConsoleBtn) {
        clearConsoleBtn.addEventListener('click', () => {
            consoleLogs.innerHTML = '';
            updateVariables({});
        });
    }

    // New file
    async function newFile() {
        if (isModified) {
            if (!confirm("Vous avez des modifications non sauvegardées. Continuer?")) {
                return;
            }
        }

        if (editor) {
            editor.setValue(`Algorithme NouveauProgramme;
Var
    // Déclarez vos variables ici
Debut
    // Écrivez votre code ici
    Ecrire("Bonjour!");
Fin.`);
        }

        currentFileName = "programme.algo";
        isModified = false;
        fileHandle = null; // Reset handle
        updateTitle();
        statusBadge.textContent = "Nouveau";
        statusBadge.style.backgroundColor = "#28a745";
    }

    // Open File
    async function openFile() {
        if (isModified) {
            if (!confirm("Vous avez des modifications non sauvegardées. Continuer?")) {
                return;
            }
        }

        // Try File System Access API
        if ('showOpenFilePicker' in window) {
            try {
                const [handle] = await window.showOpenFilePicker({
                    types: [{
                        description: 'Fichiers Algo',
                        accept: { 'text/plain': ['.algo', '.txt'] }
                    }],
                    multiple: false
                });

                const file = await handle.getFile();
                const content = await file.text();

                if (editor) {
                    editor.setValue(content);
                } else {
                    codeEditorElement.value = content;
                }

                fileHandle = handle;
                currentFileName = file.name;
                isModified = false;
                updateTitle();
                statusBadge.textContent = "Chargé";
                statusBadge.style.backgroundColor = "#28a745";

            } catch (err) {
                // User cancelled or error
                if (err.name !== 'AbortError') {
                    console.error('Error opening file:', err);
                }
            }
        } else {
            // Fallback to input element
            document.getElementById('file-input').click();
        }
    }

    // Save file
    async function saveFile() {
        const code = editor ? editor.getValue() : codeEditorElement.value;

        if (fileHandle) {
            // Write to existing handle
            try {
                const writable = await fileHandle.createWritable();
                await writable.write(code);
                await writable.close();

                isModified = false;
                updateTitle();
                statusBadge.textContent = "Sauvegardé";
                statusBadge.style.backgroundColor = "#28a745";
                setTimeout(() => {
                    statusBadge.textContent = "Prêt";
                    statusBadge.style.backgroundColor = "#28a745";
                }, 2000);
            } catch (err) {
                console.error('Error saving file:', err);
                alert("Erreur lors de la sauvegarde: " + err.message);
            }
        } else {
            // No handle, use Save As
            await saveFileAs();
        }
    }

    // Save File As
    async function saveFileAs() {
        const code = editor ? editor.getValue() : codeEditorElement.value;

        if ('showSaveFilePicker' in window) {
            try {
                // Ensure filename has .algo extension
                let suggestedName = currentFileName;
                if (!suggestedName.endsWith('.algo')) {
                    suggestedName += '.algo';
                }

                const handle = await window.showSaveFilePicker({
                    suggestedName: suggestedName,
                    types: [{
                        description: 'Fichiers Algo',
                        accept: { 'application/octet-stream': ['.algo'] }
                    }],
                });

                const writable = await handle.createWritable();
                await writable.write(code);
                await writable.close();

                fileHandle = handle;
                currentFileName = handle.name;
                isModified = false;
                updateTitle();

                statusBadge.textContent = "Sauvegardé";
                statusBadge.style.backgroundColor = "#28a745";
                setTimeout(() => {
                    statusBadge.textContent = "Prêt";
                    statusBadge.style.backgroundColor = "#28a745";
                }, 2000);

            } catch (err) {
                if (err.name !== 'AbortError') {
                    console.error('Error saving file as:', err);
                }
            }
        } else {
            // Fallback download
            const blob = new Blob([code], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = currentFileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            isModified = false;
            updateTitle();
            statusBadge.textContent = "Sauvegardé";
            statusBadge.style.backgroundColor = "#28a745";
            setTimeout(() => {
                statusBadge.textContent = "Prêt";
                statusBadge.style.backgroundColor = "#28a745";
            }, 2000);
        }
    }

    // Load file (Fallback for input element)
    function loadFile(file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            const content = e.target.result;
            if (editor) {
                editor.setValue(content);
            } else {
                codeEditorElement.value = content;
            }
            currentFileName = file.name;
            isModified = false;
            fileHandle = null; // No handle from input element
            updateTitle();
            statusBadge.textContent = "Chargé";
            statusBadge.style.backgroundColor = "#28a745";
        };
        reader.readAsText(file);
    }

    // Editor Toolbar Buttons
    const undoBtn = document.getElementById('undo-btn');
    const redoBtn = document.getElementById('redo-btn');
    const commentBtn = document.getElementById('comment-btn');
    const searchBtn = document.getElementById('search-btn');
    const replaceBtn = document.getElementById('replace-btn');
    const formatBtn = document.getElementById('format-btn');

    if (undoBtn && editor) {
        undoBtn.addEventListener('click', () => {
            editor.undo();
        });
    }

    if (redoBtn && editor) {
        redoBtn.addEventListener('click', () => {
            editor.redo();
        });
    }

    if (commentBtn && editor) {
        commentBtn.addEventListener('click', () => {
            const selection = editor.getSelection();
            if (selection) {
                // Toggle comment on selection
                editor.toggleComment();
            } else {
                // Comment current line
                const cursor = editor.getCursor();
                editor.toggleComment();
            }
        });
    }

    if (searchBtn && editor) {
        searchBtn.addEventListener('click', () => {
            editor.execCommand('find');
        });
    }

    if (replaceBtn && editor) {
        replaceBtn.addEventListener('click', () => {
            editor.execCommand('replace');
        });
    }

    if (formatBtn && editor) {
        formatBtn.addEventListener('click', () => {
            formatCode();
        });
    }

    // Event listeners for file management buttons
    const newBtn = document.getElementById('new-btn');
    const openBtn = document.getElementById('open-btn');
    const saveBtn = document.getElementById('save-btn');
    const fileInput = document.getElementById('file-input');

    if (newBtn) {
        newBtn.addEventListener('click', newFile);
    }

    if (openBtn) {
        openBtn.addEventListener('click', openFile);
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', saveFile);
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                loadFile(file);
            }
            // Reset input so same file can be loaded again
            e.target.value = '';
        });
    }

    // Prevent accidental page close with unsaved changes
    window.addEventListener('beforeunload', (e) => {
        if (isModified) {
            e.preventDefault();
            e.returnValue = '';
            return '';
        }
    });

    // Initialize title
    updateTitle();

    // Sidebar Toggle Logic
    function openSidebar() {
        examplesSidebar.classList.add('open');
        examplesOverlay.classList.add('show');
    }

    function closeSidebar() {
        examplesSidebar.classList.remove('open');
        examplesOverlay.classList.remove('show');
    }

    if (openExamplesBtn) openExamplesBtn.addEventListener('click', openSidebar);
    if (closeExamplesBtn) closeExamplesBtn.addEventListener('click', closeSidebar);
    if (examplesOverlay) examplesOverlay.addEventListener('click', closeSidebar);


    // Load Examples into Sidebar
    async function loadExamples() {
        try {
            console.log("Fetching examples...");
            const response = await fetch('/examples');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            console.log("Examples loaded:", data);

            // Clear loading placeholder
            examplesContent.innerHTML = '';

            // Define category order
            const order = ["Basics", "Arrays", "Strings", "Pointers", "Dynamic Allocation", "Functions"];

            // Map categories to icons and localized names
            const categoryMeta = {
                "Basics": { icon: "fas fa-leaf", label: "Les Bases" },
                "Arrays": { icon: "fas fa-table", label: "Tableaux" },
                "Strings": { icon: "fas fa-language", label: "Chaînes de Caractères" },
                "Pointers": { icon: "fas fa-bullseye", label: "Pointeurs" },
                "Dynamic Allocation": { icon: "fas fa-link", label: "Allocation Dynamique" },
                "Functions": { icon: "fas fa-cogs", label: "Fonctions & Procédures" }
            };

            // Process predefined tracked categories
            order.forEach(category => {
                if (data[category] && data[category].length > 0) {
                    addCategory(category, data[category]);
                }
            });

            // Process arbitrary other categories
            Object.keys(data).forEach(category => {
                if (!order.includes(category) && data[category].length > 0) {
                    addCategory(category, data[category]);
                }
            });

            function addCategory(rawName, files) {
                const categoryDiv = document.createElement('div');
                categoryDiv.className = 'example-category';

                const title = document.createElement('div');
                title.className = 'example-category-title';

                if (categoryMeta[rawName]) {
                    title.innerHTML = `<i class="${categoryMeta[rawName].icon}"></i> ${categoryMeta[rawName].label}`;
                } else {
                    title.innerHTML = `<i class="fas fa-folder"></i> ${rawName}`;
                }

                categoryDiv.appendChild(title);

                files.forEach(file => {
                    const btn = document.createElement('button');
                    btn.className = 'example-btn';

                    // Track path in dataset
                    btn.dataset.path = file.path;

                    // Style tutorials specifically
                    if (file.name.startsWith('00_Tutoriel')) {
                        btn.classList.add('tutorial');
                        btn.innerHTML = `<i class="fas fa-graduation-cap"></i> ${file.name.replace('00_Tutoriel_', '').replace('.algo', '').replace(/_/g, ' ')}`;
                    } else {
                        btn.innerHTML = `<i class="fas fa-file-code"></i> ${file.name}`;
                    }

                    // Attach click handler cleanly
                    btn.addEventListener('click', () => loadExampleFile(file.path));

                    categoryDiv.appendChild(btn);
                });

                examplesContent.appendChild(categoryDiv);
            }
        } catch (e) {
            console.error("Failed to load examples", e);
            examplesContent.innerHTML = `<div class="text-danger p-3"><i class="fas fa-exclamation-triangle"></i> Erreur lors du chargement des exemples.</div>`;
            statusBadge.textContent = "Err Exemples";
            statusBadge.style.backgroundColor = "#da3633";
        }
    }
    loadExamples();

    // Fetch and load a specific example file
    async function loadExampleFile(filename) {
        if (!filename) return;

        if (isModified) {
            if (!confirm("Vous avez des modifications non sauvegardées. Écraser votre travail avec cet exemple ?")) {
                return;
            }
        }

        try {
            console.log(`Loading example: ${filename}`);
            const response = await fetch(`/example/${filename}`);
            if (response.ok) {
                const data = await response.json();
                if (editor) {
                    editor.setValue(data.code);
                } else {
                    codeEditorElement.value = data.code;
                }

                // Treat as new file visually
                currentFileName = filename.split('/').pop();
                fileHandle = null;
                isModified = false;
                updateTitle();
                statusBadge.textContent = "Exemple chargé";
                statusBadge.style.backgroundColor = "#28a745";

                // Close the sidebar immediately on selection for better UX
                closeSidebar();
            } else {
                console.error("Failed to fetch example content");
            }
        } catch (e) {
            console.error("Failed to load example content", e);
        }
    }

    // Toggle Python Code Visibility - Functionality Removed


    // Update Variable Table
    function updateVariables(vars) {
        const variablesBody = document.getElementById('variables-body');
        const variablesTable = variablesBody.closest('table');
        const thead = variablesTable.querySelector('thead tr');

        // Ensure Type and Size headers exist
        const requiredHeaders = ['Nom', 'Valeur', 'Adresse', 'Type', 'Taille'];
        if (thead.children.length < requiredHeaders.length) {
            thead.innerHTML = ''; // Rebuild headers
            requiredHeaders.forEach(text => {
                const th = document.createElement('th');
                th.textContent = text;
                thead.appendChild(th);
            });
        }

        variablesBody.innerHTML = '';
        if (!vars || Object.keys(vars).length === 0) {
            variablesBody.innerHTML = '<tr><td colspan="4" class="placeholder-text">Aucune donnée</td></tr>';
            return;
        }

        for (const [keyName, info] of Object.entries(vars)) {
            const row = document.createElement('tr');

            const nameCell = document.createElement('td');
            nameCell.textContent = (info && info.name) ? info.name : keyName;

            const valueCell = document.createElement('td');
            valueCell.className = 'font-mono';

            const addrCell = document.createElement('td');
            addrCell.className = 'font-mono text-gray-500 text-xs';

            const typeCell = document.createElement('td');
            typeCell.className = 'text-xs text-gray-500';

            const sizeCell = document.createElement('td');
            sizeCell.className = 'text-xs text-gray-500 font-mono';

            // Handle different info structures
            if (typeof info === 'object' && info !== null) {
                // Formatting based on type
                if (info.type === 'POINTEUR' || info.type === 'Pointeur') {
                    if (info.target_address && info.target_address !== 'ERROR') {
                        valueCell.textContent = `${info.value} → ${info.target_address}`;
                    } else {
                        valueCell.textContent = info.value;
                    }
                } else {
                    valueCell.textContent = info.value;
                }
                addrCell.textContent = info.address || '-';
                typeCell.textContent = info.type || 'Inconnu';
                sizeCell.textContent = info.size !== undefined ? info.size : '-';
            } else {
                // Legacy simple format
                valueCell.textContent = String(info);
                addrCell.textContent = '-';
                typeCell.textContent = 'Inconnu';
                sizeCell.textContent = '-';
            }

            row.appendChild(nameCell);
            row.appendChild(valueCell);
            row.appendChild(addrCell);
            row.appendChild(typeCell);
            row.appendChild(sizeCell);
            variablesBody.appendChild(row);
        }
    }

    // Execution Logic
    function startLogic(btn) {
        // Get code from CodeMirror if active
        const code = editor ? editor.getValue() : codeEditorElement.value;

        if (btn.innerText.includes('Arrêter')) {
            stopExecution();
            return;
        }

        // UI Reset
        btn.innerHTML = '<i class="fas fa-stop"></i> Arrêter';
        consoleLogs.innerHTML = '';
        updateVariables({});
        statusBadge.textContent = "Exécution...";
        statusBadge.style.backgroundColor = "#d29922";
        consoleInputContainer.style.display = 'none';

        if (eventSource) eventSource.close();

        // Get Input File Content if any
        const inputFileContent = window.inputFileContent || "";

        runExecution(code, inputFileContent);
    }

    async function runExecution(code, inputFileContent) {
        try {
            console.log("Starting execution...");
            const response = await fetch('/start_execution', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code, inputFileContent: inputFileContent })
            });
            const data = await response.json();

            if (!data.success) {
                // Check if we have detailed errors
                if (data.details && Array.isArray(data.details)) {
                    appendToConsole("ÉCHEC DE LA COMPILATION:\n", 'error');
                    data.details.forEach(err => {
                        const loc = `Ligne ${err.line}, Colonne ${err.column}`;
                        const span = document.createElement('span');
                        span.style.color = '#da3633';
                        if (err.error_code) {
                            span.innerHTML = `<a href="/doc/errors#${err.error_code}" target="_blank" style="color: #ffb86c; font-weight: bold; text-decoration: underline;">[${err.error_code}]</a> [${err.type}] ${loc}: ${err.message}\n`;
                        } else {
                            span.textContent = `[${err.type}] ${loc}: ${err.message}\n`;
                        }
                        document.getElementById('console-logs').appendChild(span);
                    });
                } else {
                    appendToConsole(data.error, 'error');
                }
                finishExecution();
                return;
            }

            console.log("Connecting to stream...");
            eventSource = new EventSource('/stream');

            eventSource.onmessage = (e) => {
                const msg = JSON.parse(e.data);
                // console.log("Stream msg:", msg); // Verbose logging

                if (msg.type === 'stdout') {
                    appendToConsole(msg.data);
                } else if (msg.type === 'trace') {
                    if (msg.data.variables) updateVariables(msg.data.variables);
                } else if (msg.type === 'input_request') {
                    console.log("Input request received from server");
                    showInputPrompt();
                } else if (msg.type === 'error') {
                    appendToConsole('\n' + msg.data, 'error');
                } else if (msg.type === 'finished') {
                    statusBadge.textContent = "Terminé";
                    statusBadge.style.backgroundColor = "#238636";
                    eventSource.close();
                    finishExecution();
                } else if (msg.type === 'stopped') {
                    statusBadge.textContent = "Arrêté";
                    statusBadge.style.backgroundColor = "#cf222e";
                    appendToConsole('\n' + (msg.data || "Arrêt"), 'error');
                    eventSource.close();
                    finishExecution(true);
                }
            };

            eventSource.onerror = (e) => {
                console.error("Stream error", e);
                // Don't finish immediately, maybe just connection hiccup?
                // But for SSE usually it means end.
                if (eventSource.readyState === EventSource.CLOSED) {
                    finishExecution();
                }
            };

        } catch (error) {
            console.error("Execution error", error);
            appendToConsole(`Erreur système: ${error.message}`, 'error');
            finishExecution();
        }
    }

    async function stopExecution() {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }

        statusBadge.textContent = "Arrêt en cours...";
        statusBadge.style.backgroundColor = "#cf222e";

        try {
            await fetch('/stop_execution', { method: 'POST' });
        } catch (e) {
            console.error("Failed to stop execution on server", e);
        }

        finishExecution(true); // true = stopped manually
    }

    function finishExecution(stopped = false) {
        const btn = document.getElementById('run-btn');
        btn.innerHTML = '<i class="fas fa-play"></i> Exécuter';

        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
        consoleInputContainer.style.display = 'none';

        if (stopped) {
            statusBadge.textContent = "Arrêté";
            statusBadge.style.backgroundColor = "#cf222e";
            appendToConsole("\n[Exécution interrompue par l'utilisateur]", 'error');
        } else {
            // If not manually stopped, it's finished successfully (or error handled elsewhere)
            // But if we are here via finishExecution() called generally, we might want to keep the "Terminé" or "Erreur" state set by the stream.
            // Only reset to "Prêt" if we want to auto-reset. 
            // Let's keep the last state for clarity.
            if (statusBadge.textContent === "Exécution...") {
                statusBadge.textContent = "Terminé";
                statusBadge.style.backgroundColor = "#238636";
            }
        }
    }

    function showInputPrompt() {
        console.log("Showing input prompt (forced)");

        let container = consoleInputContainer;
        if (!container) {
            console.warn("consoleInputContainer lost, re-querying");
            container = document.getElementById('console-input-container');
        }

        if (!container) {
            console.error("consoleInputContainer NOT FOUND in DOM");
            return;
        }

        // Force header update to indicate waiting
        statusBadge.textContent = "Attente saisie...";
        statusBadge.style.backgroundColor = "#1f6feb";

        // Use direct style property
        container.style.display = 'flex';
        // Also try legacy
        container.setAttribute('style', 'display: flex !important; background-color: #0d1117;');

        if (consoleInput) {
            consoleInput.value = '';
            consoleInput.focus();
        }

        // Scroll to bottom
        const logsElement = document.getElementById('console-logs');
        if (logsElement) logsElement.scrollTop = logsElement.scrollHeight;
        consoleInput.value = '';
        consoleInput.focus();
        statusBadge.textContent = "Attente saisie...";
        statusBadge.style.backgroundColor = "#1f6feb";

        // Scroll to bottom of logs
        const logs = document.getElementById('console-logs');
        if (logs) logs.scrollTop = logs.scrollHeight;
    }

    // Console Helper
    function appendToConsole(text, type = 'normal') {
        const span = document.createElement('span');
        span.textContent = text;
        if (type === 'error') span.style.color = '#da3633';
        if (type === 'input') span.style.color = '#238636';
        consoleLogs.appendChild(span);
        // Auto scroll
        consoleLogs.scrollTop = consoleLogs.scrollHeight;
        document.getElementById('execution-output').scrollTop = document.getElementById('execution-output').scrollHeight;
    }

    if (consoleInput) {
        consoleInput.addEventListener('keydown', async (e) => {
            if (e.key === 'Enter') {
                e.preventDefault(); // Prevent default submission
                const text = consoleInput.value;
                appendToConsole(text + '\n', 'input');
                consoleInputContainer.style.display = 'none';
                statusBadge.textContent = "Exécution...";
                statusBadge.style.backgroundColor = "#d29922";

                console.log("Sending input to server:", text);

                try {
                    const response = await fetch('/send_input', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ input: text })
                    });
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    console.log("Input sent successfully");
                } catch (err) {
                    console.error("Failed to send input", err);
                    appendToConsole(`Erreur envoi: ${err.message}\n`, 'error');
                }
            }
        });
    }

    // Initial Setup
    if (runBtn) {
        runBtn.addEventListener('click', () => startLogic(runBtn));
    }

    // Input File Handling
    const inputFileBtn = document.getElementById('input-file-btn');
    const inputFileSelect = document.getElementById('input-file-select');
    const inputFileStatus = document.getElementById('input-file-status');
    window.inputFileContent = "";

    if (inputFileBtn) {
        inputFileBtn.addEventListener('click', () => {
            inputFileSelect.click();
        });
    }

    if (inputFileSelect) {
        inputFileSelect.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    window.inputFileContent = e.target.result;
                    inputFileStatus.style.display = 'inline';
                    inputFileStatus.textContent = file.name;
                    inputFileStatus.title = "Fichier d'entrée chargé pour la prochaine exécution";
                };
                reader.readAsText(file);
            }
        });
    }

});
