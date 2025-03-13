// CodeMirror mode for Tiger language
(function(mod) {
    if (typeof exports == "object" && typeof module == "object") // CommonJS
        mod(require("codemirror"));
    else if (typeof define == "function" && define.amd) // AMD
        define(["codemirror"], mod);
    else // Plain browser env
        mod(CodeMirror);
})(function(CodeMirror) {
    "use strict";

    CodeMirror.defineMode("tiger", function(config) {
        function words(str) {
            var obj = {}, words = str.split(" ");
            for (var i = 0; i < words.length; ++i) obj[words[i]] = true;
            return obj;
        }

        var keywords = words(
            "array break do else end for function if in let nil of then to type var while"
        );

        var atoms = words("nil");

        var isOperatorChar = /[+\-*&%=<>!?|\/]/;

        function tokenBase(stream, state) {
            var ch = stream.next();
            
            if (ch == '"') {
                state.tokenize = tokenString;
                return state.tokenize(stream, state);
            }
            
            if (ch == "/") {
                if (stream.eat("*")) {
                    state.tokenize = tokenComment;
                    return state.tokenize(stream, state);
                }
            }
            
            if (/[\d]/.test(ch)) {
                stream.eatWhile(/[\d]/);
                return "number";
            }
            
            if (/[\w_]/.test(ch)) {
                stream.eatWhile(/[\w\d_]/);
                var word = stream.current();
                if (keywords.hasOwnProperty(word)) return "keyword";
                if (atoms.hasOwnProperty(word)) return "atom";
                return "variable";
            }
            
            if (isOperatorChar.test(ch)) {
                stream.eatWhile(isOperatorChar);
                return "operator";
            }
            
            return null;
        }

        function tokenString(stream, state) {
            var escaped = false, next, end = false;
            while ((next = stream.next()) != null) {
                if (next == '"' && !escaped) {
                    end = true;
                    break;
                }
                escaped = !escaped && next == "\\";
            }
            if (end || !escaped) state.tokenize = tokenBase;
            return "string";
        }

        function tokenComment(stream, state) {
            var maybeEnd = false, ch;
            while (ch = stream.next()) {
                if (ch == "/" && maybeEnd) {
                    state.tokenize = tokenBase;
                    break;
                }
                maybeEnd = (ch == "*");
            }
            return "comment";
        }

        return {
            startState: function() {
                return {
                    tokenize: tokenBase,
                    context: null
                };
            },

            token: function(stream, state) {
                if (stream.eatSpace()) return null;
                return state.tokenize(stream, state);
            }
        };
    });

    CodeMirror.defineMIME("text/x-tiger", "tiger");
}); 