(function () {
  var KEYWORDS = new Set([
    'func', 'var', 'const', 'class_name', 'extends', 'class', 'return',
    'if', 'elif', 'else', 'for', 'while', 'match', 'pass', 'break',
    'continue', 'and', 'or', 'not', 'in', 'is', 'as',
    'signal', 'static', 'enum', 'preload', 'load',
    'await', 'yield', 'super', 'assert', 'breakpoint'
  ]);

  // literal / special-reference values, kept visually distinct from control-flow keywords
  var CONSTANTS = new Set([
    'self', 'true', 'false', 'null', 'PI', 'TAU', 'INF', 'NAN'
  ]);

  // lowercase primitives - PascalCase built-ins/custom classes are caught by the
  // capitalized-word heuristic below instead of needing to be listed here
  var BUILTIN_TYPES = new Set([
    'int', 'float', 'bool', 'void', 'String', 'Array', 'Dictionary',
    'Vector2', 'Vector2i', 'Vector3', 'Vector3i', 'Vector4', 'Color',
    'Node', 'Object', 'Resource', 'Callable', 'Signal',
    'Variant', 'StringName', 'NodePath'
  ]);

  // ordered by priority - first match wins
  var PATTERNS = [
    ['comment',    /#[^\n]*/],
    ['string',     /"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'/],
    ['annotation', /@\w+/],
    ['nodepath',   /\$[A-Za-z_]\w*(?:\/[A-Za-z_]\w*)*|%[A-Za-z_]\w*/],
    ['number',     /\b(?:0x[\da-fA-F]+|0b[01]+|\d[\d_]*(?:\.[\d_]+)?)\b/],
    ['word',       /[a-zA-Z_]\w*/],
    ['other',      /[\s\S]/],
  ];

  function esc(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function tokenize(text) {
    var out = '';
    var i = 0;
    while (i < text.length) {
      var slice = text.slice(i);
      for (var p = 0; p < PATTERNS.length; p++) {
        var type = PATTERNS[p][0];
        var m = slice.match(new RegExp(PATTERNS[p][1].source));
        if (!m || m.index !== 0) continue;

        var tok = m[0];
        if (type === 'word') {
          if (KEYWORDS.has(tok)) {
            out += '<span class="gds-keyword">' + esc(tok) + '</span>';
          } else if (CONSTANTS.has(tok)) {
            out += '<span class="gds-constant">' + esc(tok) + '</span>';
          } else if (BUILTIN_TYPES.has(tok) || /^[A-Z]/.test(tok)) {
            out += '<span class="gds-type">' + esc(tok) + '</span>';
          } else if (/^\s*\(/.test(text.slice(i + tok.length))) {
            out += '<span class="gds-function">' + esc(tok) + '</span>';
          } else if (text[i - 1] === '.') {
            out += '<span class="gds-property">' + esc(tok) + '</span>';
          } else {
            out += esc(tok);
          }
        } else if (type === 'other') {
          out += esc(tok);
        } else {
          out += '<span class="gds-' + type + '">' + esc(tok) + '</span>';
        }
        i += tok.length;
        break;
      }
    }
    return out;
  }

  function highlight() {
    document.querySelectorAll('code.language-gdscript').forEach(function (block) {
      block.innerHTML = tokenize(block.textContent);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', highlight);
  } else {
    highlight();
  }
})();
