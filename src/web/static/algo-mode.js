// Algo Language Mode for CodeMirror
(function (mod) {
    if (typeof exports == "object" && typeof module == "object") // CommonJS
        mod(require("../../lib/codemirror"));
    else if (typeof define == "function" && define.amd) // AMD
        define(["../../lib/codemirror"], mod);
    else // Plain browser env
        mod(CodeMirror);
})(function (CodeMirror) {
    "use strict";

    CodeMirror.defineMode("algo", function () {
        // Keywords
        var keywords = {
            "algorithme": true, "var": true, "const": true, "debut": true, "fin": true,
            "si": true, "alors": true, "sinon": true, "fsi": true, "finsi": true,
            "pour": true, "finpour": true, "faire": true,
            "tant": true, "tantque": true, "fintantque": true, "que": true,
            "repeter": true, "jusqua": true,
            "ecrire": true, "lire": true, "retourner": true,
            "fonction": true, "procedure": true, "tableau": true,
            "nil": true,          // Null pointer
            "type": true,         // Record type declaration keyword
            "enregistrement": true  // Record body keyword
        };

        // Built-in types (primitives)
        var types = {
            "entier": true, "reel": true, "chaine": true,
            "booleen": true, "caractere": true
        };

        // Built-in functions
        var builtins = {
            "longueur": true, "concat": true,
            "allouer": true, "liberer": true, "taille": true
        };

        // Boolean values
        var atoms = {
            "vrai": true, "faux": true
        };

        // Operators
        var operators = {
            "mod": true, "div": true, "et": true, "ou": true, "non": true
        };

        // Dynamic set of user-defined record type names (collected per-document)
        // This is populated via the global window.algoRecordTypes set by the editor
        function getUserTypes() {
            if (typeof window !== "undefined" && window.algoRecordTypes) {
                return window.algoRecordTypes;
            }
            return {};
        }

        function tokenBase(stream, state) {
            // Handle comments
            if (stream.match(/\/\/.*/)) {
                return "comment";
            }

            // Handle strings
            if (stream.match(/"(?:[^\\]|\\.)*?(?:"|$)/) || stream.match(/'(?:[^\\]|\\.)*?(?:'|$)/)) {
                return "string";
            }

            // Handle numbers
            if (stream.match(/\d+\.?\d*/)) {
                return "number";
            }

            // Handle -> arrow operator (must come before - and >)
            if (stream.match(/->/)) {
                return "operator";
            }

            // Handle operators and assignment
            if (stream.match(/<-|:=|<=|>=|<>|<|>|\+|-|\*|\/|=/)) {
                return "operator";
            }

            // Handle punctuation
            if (stream.match(/[;:,\[\]\(\)\{\}\^\&\.]/)) {
                return "punctuation";
            }

            // Handle words (keywords, types, identifiers) - support hyphens NOT before >
            if (stream.match(/[a-zA-ZÀ-ÿ_][a-zA-ZÀ-ÿ0-9_]*(-(?!>)[a-zA-ZÀ-ÿ0-9_]*)*/)) {
                var word = stream.current().toLowerCase();

                // After 'type' keyword, the next word is a user-defined type name
                if (state.expectTypeName) {
                    state.expectTypeName = false;
                    // Register the user-defined type name for highlighting
                    if (!state.userTypes) state.userTypes = {};
                    state.userTypes[word] = true;
                    return "def";  // highlighted as a definition
                }

                if (word === "type") {
                    state.expectTypeName = true;
                }

                if (keywords.hasOwnProperty(word)) {
                    return "keyword";
                }
                if (types.hasOwnProperty(word)) {
                    return "type";
                }
                if (builtins.hasOwnProperty(word)) {
                    return "builtin";
                }
                if (atoms.hasOwnProperty(word)) {
                    return "atom";
                }
                if (operators.hasOwnProperty(word)) {
                    return "operator";
                }
                // Check user-defined record types (highlighted as 'type')
                if (state.userTypes && state.userTypes[word]) {
                    return "type";
                }
                // Also check global registry if populated
                var ut = getUserTypes();
                if (ut[word]) {
                    return "type";
                }

                return "variable";
            }

            stream.next();
            return null;
        }

        return {
            startState: function () {
                return { expectTypeName: false, userTypes: {} };
            },
            token: function (stream, state) {
                if (stream.eatSpace()) return null;
                return tokenBase(stream, state);
            },
            lineComment: "//"
        };
    });

    CodeMirror.defineMIME("text/x-algo", "algo");
});
