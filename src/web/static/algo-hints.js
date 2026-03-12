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
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        },
        "pour": {
            text: "Pour i := 0 a 10 Faire\n    // Code ici\nFin Pour;",
            displayText: "Pour ... Faire (loop)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        },
        "pout": {
            text: "Pour i := 0 a 10 Faire\n    // Code ici\nFin Pour;",
            displayText: "Pout (alias for Pour)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        },
        "si": {
            text: "Si condition Alors\n    // Code ici\nFin Si;",
            displayText: "Si ... Alors (if)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        },
        "si_sinon": {
            text: "Si condition Alors\n    // Code ici\nSinon\n    // Code ici\nFin Si;",
            displayText: "Si ... Alors ... Sinon (if/else)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        },
        "tantque": {
            text: "TantQue condition Faire\n    // Code ici\nFin TantQue;",
            displayText: "TantQue ... Faire (while)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        },
        "tanque": {
            text: "TantQue condition Faire\n    // Code ici\nFin TantQue;",
            displayText: "Tanque (alias for TantQue)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        },
        "repeter": {
            text: "Repeter\n    // Code ici\nJusqua condition;",
            displayText: "Repeter ... Jusqua (loop)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        },
        "repre": {
            text: "Repeter\n    // Code ici\nJusqua condition;",
            displayText: "Repre (alias for Repeter)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        },
        "ecrire": {
            text: "Ecrire(\"\");",
            displayText: "Ecrire(\"\") (print)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        },
        "lire": {
            text: "Lire(\"\");",
            displayText: "Lire(\"\") (read)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        },
        "type": {
            text: "Type NomType = Enregistrement\nDebut\n    champ : Entier;\nFin;",
            displayText: "Type ... = Enregistrement (record)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        },
        "enregistrement": {
            text: "Enregistrement\nDebut\n    champ : Entier;\nFin;",
            displayText: "Enregistrement (record body)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        },
        "fonction": {
            text: "Fonction NomFonction(param : Entier) : Entier\nVar\n    res : Entier;\nDebut\n    // Code ici\n    Retourner res;\nFin;",
            displayText: "Fonction ... (function)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        },
        "procedure": {
            text: "Procedure NomProcedure(param : Entier)\nVar\n    \nDebut\n    // Code ici\nFin;",
            displayText: "Procedure ... (procedure)",
            className: "hint-snippet",
            render: function (element, self, data) {
                element.innerHTML = '<span class="hint-badge hint-badge-snippet">SNIP</span> ' + data.displayText;
            }
        }
    };

    function hashCode(str) {
        var hash = 0;
        for (var i = 0; i < str.length; i++) {
            hash = ((hash << 5) - hash) + str.charCodeAt(i);
            hash |= 0;
        }
        return hash;
    }

    var parseCache = { hash: null, recordTypes: {}, recordTypesLower: {}, recordTypeList: [], variables: [], varMap: {}, fields: [] };

    function parseRecordTypes(code) {
        var types = {};
        var typesLower = {};
        var list = [];
        var seen = {};
        var typeBlocks = code.matchAll(/^\s*Type\s+([a-zA-Z_][a-zA-Z0-9_-]*)\s*=\s*Enregistrement([\s\S]*?)(?:^\s*Fin\s*;)/gim);
        for (let match of typeBlocks) {
            var typeName = match[1];
            var body = match[2] || "";
            var fields = [];
            var fieldMatches = body.matchAll(/([a-zA-Z_][a-zA-Z0-9_-]*)\s*(\[\s*\d+\s*\])?\s*:\s*([a-zA-Z_][a-zA-Z0-9_-]*)/g);
            for (let fm of fieldMatches) {
                var fname = fm[1];
                var sizeToken = fm[2];
                var ftype = fm[3];
                var size = null;
                if (sizeToken) {
                    var n = sizeToken.replace(/[\[\]\s]/g, '');
                    size = n || null;
                }
                var typeStr = size ? ("TABLEAU_" + ftype + "_" + size) : ftype;
                fields.push({
                    name: fname,
                    nameDisplay: size ? (fname + "[" + size + "]") : fname,
                    type: typeStr,
                    baseType: ftype,
                    arraySize: size
                });
            }
            types[typeName] = fields;
            typesLower[typeName.toLowerCase()] = fields;
            if (!seen[typeName]) {
                seen[typeName] = true;
                list.push({
                    text: typeName,
                    displayText: typeName + " (Enregistrement)",
                    type: "type",
                    render: createRenderFunction("TYPE", "hint-badge-type")
                });
            }
        }
        return { types: types, typesLower: typesLower, list: list };
    }

    function parseVarDecls(block, outVars) {
        var decls = block.split(';');
        decls.forEach(function (decl) {
            var parts = decl.split(':');
            if (parts.length < 2) return;
            var namesPart = parts[0].trim();
            var typePart = parts.slice(1).join(':').trim();
            if (!namesPart || !typePart) return;
            var tableauMatch = typePart.match(/^Tableau\s+de\s+([a-zA-Z_][a-zA-Z0-9_-]*)/i);
            var rawType = tableauMatch ? ("TABLEAU_" + tableauMatch[1]) : (typePart.match(/^([^\s]+)/) || [])[1];
            if (!rawType) return;

            namesPart.split(',').forEach(function (nameRaw) {
                var nm = nameRaw.trim();
                if (!nm) return;
                var nmMatch = nm.match(/^([a-zA-Z_][a-zA-Z0-9_-]*)(\[\s*\d+\s*\])?$/);
                if (!nmMatch) return;
                var name = nmMatch[1];
                var sizeToken = nmMatch[2];
                var size = null;
                if (sizeToken) size = sizeToken.replace(/[\[\]\s]/g, '');
                var typeStr = rawType;
                if (size && /chaine/i.test(rawType)) {
                    typeStr = "TABLEAU_Chaine_" + size;
                } else if (size) {
                    typeStr = "TABLEAU_" + rawType + "_" + size;
                }
                outVars.push({
                    text: name,
                    displayText: name + " : " + rawType,
                    type: "variable",
                    varType: typeStr,
                    rawType: rawType
                });
            });
        });
    }

    function extractVariablesAndParams(code) {
        var variables = [];
        var varBlocks = code.matchAll(/^\s*Var\s+([\s\S]*?)(?=^\s*(Debut|Const|Type|Fonction|Procedure|Algorithme)\b|$)/gim);
        for (let match of varBlocks) {
            parseVarDecls(match[1] || "", variables);
        }

        var paramBlocks = code.matchAll(/^\s*(Fonction|Procedure)\s+[a-zA-Z_][a-zA-Z0-9_-]*\s*\(([^)]*)\)/gim);
        for (let match of paramBlocks) {
            parseVarDecls(match[2] || "", variables);
        }

        return variables;
    }

    function buildFieldList(recordTypes) {
        var fields = [];
        Object.keys(recordTypes).forEach(function (typeName) {
            recordTypes[typeName].forEach(function (f) {
                fields.push({
                    text: f.nameDisplay,
                    displayText: f.nameDisplay + " : " + f.baseType + " (" + typeName + ")",
                    type: "field",
                    render: createRenderFunction("FIELD", "hint-badge-field")
                });
            });
        });
        return fields;
    }

    function getParsed(code) {
        var h = hashCode(code);
        if (parseCache.hash === h) return parseCache;
        var rec = parseRecordTypes(code);
        var vars = extractVariablesAndParams(code);
        var varMap = {};
        vars.forEach(function (v) { varMap[v.text] = v; });
        parseCache = {
            hash: h,
            recordTypes: rec.types,
            recordTypesLower: rec.typesLower,
            recordTypeList: rec.list,
            variables: vars,
            varMap: varMap,
            fields: buildFieldList(rec.types)
        };
        return parseCache;
    }

    // Helper function to create render function for different types
    function createRenderFunction(label, className) {
        return function (element, self, data) {
            var displayText = data.displayText || data.text;
            element.innerHTML = '<span class="hint-badge ' + className + '">' + label + '</span> ' + displayText;
        };
    }

    function resolveTypeFromExpr(expr, parsed) {
        var tokens = [];
        var parts = expr.split(/(\.|->)/).filter(Boolean);
        for (var i = 0; i < parts.length; i++) {
            var p = parts[i].trim();
            if (!p) continue;
            if (p === "." || p === "->") {
                tokens.push(p);
            } else {
                tokens.push(p);
            }
        }
        if (!tokens.length) return null;

        function getBaseName(token) {
            var m = token.match(/^([a-zA-Z_][a-zA-Z0-9_-]*)(\s*\[[^\]]+\])?$/);
            if (!m) return { name: token, hasIndex: false };
            return { name: m[1], hasIndex: !!m[2] };
        }

        var first = getBaseName(tokens[0]);
        var v = parsed.varMap[first.name];
        if (!v) return null;
        var currentType = v.varType || v.rawType || v.displayText;

        function stripPointer(t) {
            if (!t) return t;
            if (t.startsWith('^')) return t.slice(1);
            if (t.startsWith('POINTEUR_')) return t.slice('POINTEUR_'.length);
            return t;
        }

        function arrayElemType(t) {
            if (!t) return t;
            if (t.startsWith('TABLEAU_')) {
                var parts = t.split('_');
                if (parts.length >= 3) return parts.slice(1, parts.length - 1).join('_');
            }
            return t;
        }

        if (first.hasIndex) currentType = arrayElemType(currentType);

        for (var i = 1; i < tokens.length; i += 2) {
            var op = tokens[i];
            var next = tokens[i + 1];
            if (!next) break;
            var field = getBaseName(next);
            var recType = currentType;
            if (op === "->") {
                recType = stripPointer(currentType);
            }
            var keyLower = (recType || "").toLowerCase();
            var fields = parsed.recordTypes[recType] || parsed.recordTypesLower[keyLower];
            if (!fields) return null;
            var found = null;
            for (var j = 0; j < fields.length; j++) {
                if (fields[j].name === field.name) { found = fields[j]; break; }
            }
            if (!found) return null;
            currentType = found.type;
            if (field.hasIndex) currentType = arrayElemType(currentType);
        }
        return currentType;
    }

    function getFieldSuggestions(cm, cursor, parsed) {
        var line = cm.getLine(cursor.line);
        var upto = line.slice(0, cursor.ch);
        var m = upto.match(/([a-zA-Z_][a-zA-Z0-9_-]*(?:\s*\[[^\]]*\])?(?:\s*(?:->|\.)\s*[a-zA-Z_][a-zA-Z0-9_-]*(?:\s*\[[^\]]*\])?)*)\s*(->|\.)\s*([a-zA-Z_][a-zA-Z0-9_-]*)?$/);
        if (!m) return null;
        var expr = m[1];
        var partial = m[3] || "";
        var t = resolveTypeFromExpr(expr, parsed);
        if (!t) return null;
        var recType = t.startsWith('^') ? t.slice(1) : t;
        if (recType.startsWith('POINTEUR_')) recType = recType.slice('POINTEUR_'.length);
        var fields = parsed.recordTypes[recType] || parsed.recordTypesLower[(recType || "").toLowerCase()];
        if (!fields) return null;
        var list = fields.filter(function (f) {
            return f.name.toLowerCase().indexOf(partial.toLowerCase()) === 0;
        }).map(function (f) {
            return {
                text: f.nameDisplay,
                displayText: f.nameDisplay + " : " + f.baseType,
                type: "field",
                render: createRenderFunction("FIELD", "hint-badge-field")
            };
        });
        return {
            list: list,
            from: CodeMirror.Pos(cursor.line, cursor.ch - partial.length),
            to: CodeMirror.Pos(cursor.line, cursor.ch)
        };
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

        var parsed = getParsed(cm.getValue());

        var fieldContext = getFieldSuggestions(cm, cursor, parsed);
        if (fieldContext && fieldContext.list.length > 0) {
            return fieldContext;
        }

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
                    render: createRenderFunction("KW", "hint-badge-keyword")
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
                    render: createRenderFunction("TYPE", "hint-badge-type")
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
                    render: createRenderFunction("FN", "hint-badge-builtin")
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
                    render: createRenderFunction("LIT", "hint-badge-atom")
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
                    render: createRenderFunction("OP", "hint-badge-operator")
                });
            }
        });

        // Add variables from code
        parsed.variables.forEach(function (v) {
            if (v.text.toLowerCase().indexOf(word) === 0) {
                v.render = createRenderFunction("VAR", "hint-badge-variable");
                suggestions.push(v);
            }
        });

        // Add user-defined record type names
        parsed.recordTypeList.forEach(function (rt) {
            if (rt.text.toLowerCase().indexOf(word) === 0) {
                suggestions.push(rt);
            }
        });

        // Add record fields (lower priority)
        parsed.fields.forEach(function (f) {
            if (f.text.toLowerCase().indexOf(word) === 0) {
                suggestions.push(f);
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
            var typePriority = { "variable": 0, "snippet": 1, "keyword": 2, "type": 3, "builtin": 4, "atom": 5, "operator": 6, "field": 7 };
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
