// Custom Code Folding for Algo Language
(function (mod) {
    if (typeof exports == "object" && typeof module == "object") // CommonJS
        mod(require("../../lib/codemirror"));
    else if (typeof define == "function" && define.amd) // AMD
        define(["../../lib/codemirror"], mod);
    else // Plain browser env
        mod(CodeMirror);
})(function (CodeMirror) {
    "use strict";

    CodeMirror.registerHelper("fold", "algo", function (cm, start) {
        var line = cm.getLine(start.line);
        var lineText = line.trim();

        // Only fold on specific keyword lines, not variable declarations
        var foldablePatterns = [
            // Var block - only on the "Var" keyword line
            {
                start: /^Var\s*$/i,
                end: /^(Debut|Const|Algorithme)/i,
                skipEmpty: true
            },

            // Const block - only on the "Const" keyword line
            {
                start: /^Const\s*$/i,
                end: /^(Debut|Var|Algorithme)/i,
                skipEmpty: true
            },

            // Debut block (main program body)
            {
                start: /^Debut\s*$/i,
                end: /^Fin\s*\.?\s*$/i,
                skipEmpty: false
            },

            // Si (if) blocks - single line with Alors
            {
                start: /^Si\s+.+\s+Alors\s*$/i,
                end: /^Fin\s+Si/i,
                skipEmpty: false
            },

            // Sinon (else) blocks
            {
                start: /^Sinon\s*$/i,
                end: /^Fin\s+Si/i,
                skipEmpty: false
            },

            // Pour (for) loops - single line with Faire
            {
                start: /^Pour\s+.+\s+Faire\s*$/i,
                end: /^Fin\s+Pour/i,
                skipEmpty: false
            },

            // Tant Que (while) loops - single line with Faire
            {
                start: /^Tant\s+Que\s+.+\s+Faire\s*$/i,
                end: /^Fin\s+Tant\s+Que/i,
                skipEmpty: false
            },

            // Repeter (repeat) loops
            {
                start: /^Repeter\s*$/i,
                end: /^Jusqua/i,
                skipEmpty: false
            },

            // Fonction (function) blocks
            {
                start: /^Fonction\s+/i,
                end: /^Fin\s+Fonction/i,
                skipEmpty: false
            },

            // Procedure blocks
            {
                start: /^Procedure\s+/i,
                end: /^Fin\s+Procedure/i,
                skipEmpty: false
            }
        ];

        // Check if current line starts a foldable block
        var matchedPattern = null;
        for (var i = 0; i < foldablePatterns.length; i++) {
            if (foldablePatterns[i].start.test(lineText)) {
                matchedPattern = foldablePatterns[i];
                break;
            }
        }

        if (!matchedPattern) {
            return null; // Not a foldable line
        }

        // Find the end of the block
        var lastLine = cm.lastLine();
        var endLine = null;
        var depth = 0;

        for (var lineNo = start.line + 1; lineNo <= lastLine; lineNo++) {
            var currentLine = cm.getLine(lineNo);
            var currentTrimmed = currentLine.trim();

            // Skip empty lines if configured
            if (matchedPattern.skipEmpty && !currentTrimmed) {
                continue;
            }

            // Check if this line starts a nested block of the same type
            if (matchedPattern.start.test(currentTrimmed)) {
                depth++;
            }

            // Check for end pattern
            if (matchedPattern.end.test(currentTrimmed)) {
                if (depth === 0) {
                    endLine = lineNo;
                    break;
                } else {
                    depth--;
                }
            }
        }

        if (endLine === null || endLine <= start.line + 1) {
            return null; // No valid fold range
        }

        // Return the fold range
        // Fold from end of start line to beginning of end line
        return {
            from: CodeMirror.Pos(start.line, line.length),
            to: CodeMirror.Pos(endLine, 0)
        };
    });

    // Also register as the default fold helper for algo mode
    CodeMirror.registerGlobalHelper("fold", "algo-fold", function (mode) {
        return mode.name === "algo";
    }, function (cm, start) {
        return cm.getHelper(start, "fold")(cm, start);
    });
});
