// Algo Language Autocomplete/IntelliSense
(function (mod) {
    if (typeof exports == "object" && typeof module == "object") // CommonJS
        mod(require("../../lib/codemirror"));
    else if (typeof define == "function" && define.amd) // AMD
        define(["../../lib/codemirror"], mod);
    else // Plain browser env
        mod(CodeMirror);
})(function (CodeMirror) {
    "use strict";

    // Algo keywords and constructs
    var algoKeywords = [
        "Algorithme", "Var", "Const", "Debut", "Fin",
        "Si", "Alors", "Sinon", "FinSi", "Fin Si",
        "Pour", "Faire", "FinPour", "Fin Pour",
        "TantQue", "Tant Que", "FinTantQue", "Fin Tant Que",
        "Repeter", "Jusqua",
        "Ecrire", "Lire",
        "Retourner", "Fonction", "Procedure",
        "Tableau", "NIL",
        "Type", "Enregistrement"  // Record support
    ];

    var algoTypes = [
        "Entier", "Reel", "Chaine", "Booleen", "Caractere"
    ];

    var algoBuiltins = [
        "Longueur", "Concat",
        "Allouer", "Liberer", "Taille"  // Dynamic allocation
    ];

    var algoAtoms = [
        "Vrai", "Faux"
    ];

    var algoOperators = [
        "Mod", "Div", "Et", "Ou", "Non"
    ];

    // Snippet templates with visual indicators
    var snippets = {
        "algorithme": {
            text: "Algorithme NomAlgorithme;\nVar\n    i, j : Entier;\nDebut\n    Ecrire(\"Debut de l'algorithme\");\n    \nFin.",
            displayText: "Algorithme (full structure)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-icon hint-snippet-icon">⚡</span> ' + data.displayText;
            }
        },
        "pour": {
            text: "Pour i := 0 a 10 Faire\n    // Code ici\nFinPour;",
            displayText: "Pour ... Faire (loop)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-icon hint-snippet-icon">⚡</span> ' + data.displayText;
            }
        },
        "si": {
            text: "Si condition Alors\n    // Code ici\nFin Si;",
            displayText: "Si ... Alors (if)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-icon hint-snippet-icon">⚡</span> ' + data.displayText;
            }
        },
        "tantque": {
            text: "TantQue condition Faire\n    // Code ici\nFinTantQue;",
            displayText: "TantQue ... Faire (while)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-icon hint-snippet-icon">⚡</span> ' + data.displayText;
            }
        },
        "tanque": {
            text: "TantQue condition Faire\n    // Code ici\nFinTantQue;",
            displayText: "Tanque (alias for TantQue)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-icon hint-snippet-icon">⚡</span> ' + data.displayText;
            }
        },
        "repeter": {
            text: "Repeter\n    // Code ici\nJusqua condition;",
            displayText: "Repeter ... Jusqua (loop)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-icon hint-snippet-icon">⚡</span> ' + data.displayText;
            }
        },
        "repre": {
            text: "Repeter\n    // Code ici\nJusqua condition;",
            displayText: "Repre (alias for Repeter)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-icon hint-snippet-icon">⚡</span> ' + data.displayText;
            }
        },
        "ecrire": {
            text: "Ecrire(\"\");",
            displayText: "Ecrire(\"\") (print)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-icon hint-snippet-icon">⚡</span> ' + data.displayText;
            }
        },
        "lire": {
            text: "Lire(\"\");",
            displayText: "Lire(\"\") (read)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-icon hint-snippet-icon">⚡</span> ' + data.displayText;
            }
        },
        "type": {
            text: "Type NomType = Enregistrement\nDebut\n    champ : Entier;\nFin;",
            displayText: "Type ... = Enregistrement (record)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-icon hint-snippet-icon">⚡</span> ' + data.displayText;
            }
        },
        "enregistrement": {
            text: "Enregistrement\nDebut\n    champ : Entier;\nFin;",
            displayText: "Enregistrement (record body)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-icon hint-snippet-icon">⚡</span> ' + data.displayText;
            }
        },
        "fonction": {
            text: "Fonction NomFonction(param : Entier) : Entier\nVar\n    res : Entier;\nDebut\n    // Code ici\n    Retourner res;\nFin;",
            displayText: "Fonction ... (function)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-icon hint-snippet-icon">⚡</span> ' + data.displayText;
            }
        },
        "procedure": {
            text: "Procedure NomProcedure(param : Entier)\nVar\n    \nDebut\n    // Code ici\nFin;",
            displayText: "Procedure ... (procedure)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-icon hint-snippet-icon">⚡</span> ' + data.displayText;
            }
        }
    };

    // Extract user-defined record type names for dynamic autocompletion
    function extractRecordTypes(code) {
        var types = [];
        var seen = {};
        var typeMatches = code.matchAll(/^\s*Type\s+([a-zA-Z_][a-zA-Z0-9_-]*)\s*=/gim);
        for (let match of typeMatches) {
            var name = match[1];
            if (!seen[name]) {
                seen[name] = true;
                types.push({
                    text: name,
                    displayText: name + " (Enregistrement)",
                    type: "type",
                    render: function (element, self, data) {
                        element.innerHTML = '<span class="hint-icon hint-type-icon">📋</span> ' + data.displayText;
                    }
                });
            }
        }
        return types;
    }

    // Helper function to create render function for different types
    function createRenderFunction(icon, className) {
        return function (element, self, data) {
            var displayText = data.displayText || data.text;
            element.innerHTML = '<span class="hint-icon ' + className + '">' + icon + '</span> ' + displayText;
        };
    }

    // Extract declared variables from code
    function extractVariables(code) {
        var variables = [];
        var varBlockMatch = code.match(/Var\s+([\s\S]*?)(?=Debut|Const|$)/i);

        if (varBlockMatch) {
            var varBlock = varBlockMatch[1];
            // Match variable declarations: name : Type or name[size] : Type (support hyphens)
            var varMatches = varBlock.matchAll(/([a-zA-Z_][a-zA-Z0-9_-]*)\s*(?:\[\d+\])?\s*:\s*([a-zA-Z]+)/gi);

            for (let match of varMatches) {
                variables.push({
                    text: match[1],
                    displayText: match[1] + " : " + match[2],
                    type: "variable",
                    varType: match[2]
                });
            }
        }

        return variables;
    }

    // Get context-aware suggestions
    function getContextSuggestions(cm, cursor) {
        var line = cm.getLine(cursor.line);
        var lineUpToCursor = line.slice(0, cursor.ch);
        var suggestions = [];

        // After "Var" keyword
        if (/Var\s*$/i.test(lineUpToCursor)) {
            return algoTypes.map(function (t) {
                return { text: ": " + t + ";", displayText: ": " + t, type: "type" };
            });
        }

        // After ":" in variable declaration
        if (/:\s*$/i.test(lineUpToCursor) && /Var/i.test(cm.getValue())) {
            return algoTypes.map(function (t) {
                return { text: t + ";", displayText: t, type: "type" };
            });
        }

        // After "Pour" - suggest := or <-
        if (/Pour\s+[a-zA-Z_][a-zA-Z0-9_-]*\s*$/i.test(lineUpToCursor)) {
            return [
                { text: ":= ", displayText: ":=", type: "operator" },
                { text: "<- ", displayText: "<-", type: "operator" }
            ];
        }

        // After ":=" or "<-" in Pour loop, suggest number then 'a'
        if (/Pour\s+[a-zA-Z_][a-zA-Z0-9_-]*\s+(:=|<-)\s+\d+\s*$/i.test(lineUpToCursor)) {
            return [{ text: "a ", displayText: "a (to)", type: "keyword" }];
        }

        // After "a" in Pour loop
        if (/Pour\s+[a-zA-Z_][a-zA-Z0-9_-]*\s+(:=|<-)\s+\d+\s+a\s+\d+\s*$/i.test(lineUpToCursor)) {
            return [{ text: "Faire", displayText: "Faire", type: "keyword" }];
        }

        return null;
    }

    // Main hint function
    CodeMirror.registerHelper("hint", "algo", function (cm, options) {
        var cursor = cm.getCursor();
        var line = cm.getLine(cursor.line);
        var start = cursor.ch;
        var end = cursor.ch;

        // Find word boundaries (support hyphens)
        while (start && /[\w-]/.test(line.charAt(start - 1))) --start;
        while (end < line.length && /[\w]/.test(line.charAt(end))) ++end;

        var word = line.slice(start, end).toLowerCase();
        var curWord = line.slice(start, cursor.ch);

        // Check for context-specific suggestions first
        var contextSuggestions = getContextSuggestions(cm, cursor);
        if (contextSuggestions && contextSuggestions.length > 0) {
            return {
                list: contextSuggestions,
                from: CodeMirror.Pos(cursor.line, cursor.ch),
                to: CodeMirror.Pos(cursor.line, cursor.ch)
            };
        }

        var suggestions = [];

        // Add snippets
        for (var key in snippets) {
            if (key.indexOf(word) === 0) {
                suggestions.push(snippets[key]);
            }
        }

        // Add keywords
        algoKeywords.forEach(function (kw) {
            if (kw.toLowerCase().indexOf(word) === 0) {
                suggestions.push({
                    text: kw,
                    displayText: kw,
                    type: "keyword",
                    render: createRenderFunction("🔑", "hint-keyword-icon")
                });
            }
        });

        // Add types
        algoTypes.forEach(function (type) {
            if (type.toLowerCase().indexOf(word) === 0) {
                suggestions.push({
                    text: type,
                    displayText: type,
                    type: "type",
                    render: createRenderFunction("📐", "hint-type-icon")
                });
            }
        });

        // Add built-in functions
        algoBuiltins.forEach(function (fn) {
            if (fn.toLowerCase().indexOf(word) === 0) {
                suggestions.push({
                    text: fn + "()",
                    displayText: fn + "()",
                    type: "builtin",
                    render: createRenderFunction("⚙️", "hint-builtin-icon")
                });
            }
        });

        // Add boolean atoms
        algoAtoms.forEach(function (atom) {
            if (atom.toLowerCase().indexOf(word) === 0) {
                suggestions.push({
                    text: atom,
                    displayText: atom,
                    type: "atom",
                    render: createRenderFunction("💡", "hint-atom-icon")
                });
            }
        });

        // Add operators
        algoOperators.forEach(function (op) {
            if (op.toLowerCase().indexOf(word) === 0) {
                suggestions.push({
                    text: op,
                    displayText: op,
                    type: "operator",
                    render: createRenderFunction("➕", "hint-operator-icon")
                });
            }
        });

        // Add variables from code
        var variables = extractVariables(cm.getValue());
        variables.forEach(function (v) {
            if (v.text.toLowerCase().indexOf(word) === 0) {
                v.render = createRenderFunction("📦", "hint-variable-icon");
                suggestions.push(v);
            }
        });

        // Add user-defined record type names
        var recordTypes = extractRecordTypes(cm.getValue());
        recordTypes.forEach(function (rt) {
            if (rt.text.toLowerCase().indexOf(word) === 0) {
                suggestions.push(rt);
            }
        });

        // Remove duplications where a keyword has a matching snippet
        var snippetKeys = Object.keys(snippets);
        suggestions = suggestions.filter(function (item) {
            if (item.type === "keyword") {
                var kw = item.text.toLowerCase();
                // If there's a snippet for this keyword, remove the plain keyword suggestion
                if (snippetKeys.indexOf(kw) !== -1) return false;
            }
            return true;
        });

        // Remove duplicates and sort
        var seen = {};
        suggestions = suggestions.filter(function (item) {
            var key = item.text + item.type;
            if (seen[key]) return false;
            seen[key] = true;
            return true;
        });

        // Sort by relevance
        suggestions.sort(function (a, b) {
            // Prioritize exact matches
            var aExact = a.text.toLowerCase() === word;
            var bExact = b.text.toLowerCase() === word;
            if (aExact && !bExact) return -1;
            if (!aExact && bExact) return 1;

            // Then by type priority
            var typePriority = { "variable": 0, "snippet": 1, "keyword": 2, "type": 3, "builtin": 4, "atom": 5, "operator": 6 };
            var aPriority = typePriority[a.type] || 99;
            var bPriority = typePriority[b.type] || 99;
            if (aPriority !== bPriority) return aPriority - bPriority;

            // Then alphabetically
            return a.text.localeCompare(b.text);
        });

        return {
            list: suggestions,
            from: CodeMirror.Pos(cursor.line, start),
            to: CodeMirror.Pos(cursor.line, end)
        };
    });
});
