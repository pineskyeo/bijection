"""BSPEC measurement definition file (.bspec) lexer.

Format:
    QKDLDJTM_START / QKDLDJTM_END [!]  — section markers
    !                                    — standalone comment line
    @Name[.Variant] = { Model TypeFlag [/ params]
    B SignalName DBName [= params...]
    M VarName (~)OutputName [formula with ~refs]
    A VarName=Method,Output[,Key=val...]
    ! inline comment
    }

Identifiers: section markers, block names/variants, model names, type flags,
    B signal/DB names, M var/output names, ~refs in formulas,
    A var/method/output names, key names in A key=value pairs.
Not transformed: numeric literals, $param refs, quoted formula strings, comments.
"""
import re
from typing import List

from bijection.core.token import Token, TokenKind
from bijection.lexers.base import BaseLexer

_IDENT_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
_WS_RE = re.compile(r'[ \t]+')
_MARKERS = {'QKDLDJTM_START', 'QKDLDJTM_END'}


class BSpecLexer(BaseLexer):

    def tokenize(self, source: str) -> List[Token]:
        tokens: List[Token] = []
        pos = 0
        n = len(source)

        while pos < n:
            eol = source.find('\n', pos)
            line_end = eol if eol != -1 else n
            line = source[pos:line_end]
            nl = '\n' if eol != -1 else ''
            stripped = line.strip()

            if not stripped:
                tokens.append(Token(TokenKind.WHITESPACE, line + nl))
            elif stripped == '!':
                tokens.append(Token(TokenKind.COMMENT, line + nl))
            elif stripped == '}':
                tokens.append(Token(TokenKind.SYNTAX, line + nl))
            elif stripped.startswith('@'):
                self._tok_block_header(line, tokens)
                if nl:
                    tokens.append(Token(TokenKind.SYNTAX, nl))
            else:
                m = _IDENT_RE.match(stripped)
                if m and m.group() in _MARKERS:
                    self._tok_marker_line(line, nl, m.group(), tokens)
                else:
                    self._tok_body(line, tokens)
                    if nl:
                        tokens.append(Token(TokenKind.SYNTAX, nl))

            pos = line_end + (1 if eol != -1 else 0)

        return tokens

    # ------------------------------------------------------------------
    # Line-level parsers
    # ------------------------------------------------------------------

    def _tok_marker_line(self, line: str, nl: str, marker: str,
                         tokens: List[Token]) -> None:
        """QKDLDJTM_START or QKDLDJTM_END [! comment]"""
        idx = line.index(marker)
        if idx:
            tokens.append(Token(TokenKind.WHITESPACE, line[:idx]))
        tokens.append(Token(TokenKind.IDENTIFIER, marker))
        rest = line[idx + len(marker):]
        if rest:
            m = _WS_RE.match(rest)
            if m:
                tokens.append(Token(TokenKind.WHITESPACE, m.group()))
                rest = rest[m.end():]
            if rest:
                tokens.append(Token(TokenKind.COMMENT, rest))
        if nl:
            tokens.append(Token(TokenKind.SYNTAX, nl))

    def _tok_block_header(self, line: str, tokens: List[Token]) -> None:
        """@Name[.Variant] = { ModelName TypeFlag [/ rest]"""
        i = 0
        n = len(line)

        tokens.append(Token(TokenKind.SYNTAX, '@'))
        i = 1

        m = _IDENT_RE.match(line, i)
        if m:
            tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
            i = m.end()

        if i < n and line[i] == '.':
            tokens.append(Token(TokenKind.SYNTAX, '.'))
            i += 1
            m = _IDENT_RE.match(line, i)
            if m:
                tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
                i = m.end()

        m = re.match(r'[ \t]*=[ \t]*\{[ \t]*', line[i:])
        if m:
            tokens.append(Token(TokenKind.SYNTAX, m.group()))
            i += m.end()

        m = _IDENT_RE.match(line, i)
        if m:
            tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
            i = m.end()

        m = _WS_RE.match(line, i)
        if m:
            tokens.append(Token(TokenKind.WHITESPACE, m.group()))
            i = m.end()

        m = _IDENT_RE.match(line, i)
        if m:
            tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
            i = m.end()

        if i < n:
            tokens.append(Token(TokenKind.OTHER, line[i:]))

    def _tok_body(self, line: str, tokens: List[Token]) -> None:
        """Sequence of B/M/A statements and inline ! comments."""
        i = 0
        n = len(line)

        while i < n:
            m = _WS_RE.match(line[i:])
            if m:
                tokens.append(Token(TokenKind.WHITESPACE, m.group()))
                i += m.end()
                continue

            if i >= n:
                break

            c = line[i]

            if c == '!':
                end = self._stmt_end(line, i + 1)
                tokens.append(Token(TokenKind.COMMENT, line[i:end]))
                i = end
                continue

            if c in 'BMA' and i + 1 < n and line[i + 1] == ' ':
                tokens.append(Token(TokenKind.SYNTAX, c))
                i += 1
                end = self._stmt_end(line, i)
                content = line[i:end]
                if c == 'B':
                    self._tok_b(content, tokens)
                elif c == 'M':
                    self._tok_m(content, tokens)
                elif c == 'A':
                    self._tok_a(content, tokens)
                i = end
                continue

            tokens.append(Token(TokenKind.OTHER, c))
            i += 1

    def _stmt_end(self, line: str, start: int) -> int:
        """Position where the current segment ends (before next stmt or '!')."""
        n = len(line)
        i = start
        while i < n:
            if line[i] == '!':
                return i
            if (line[i] == ' '
                    and i + 1 < n and line[i + 1] in 'BMA'
                    and i + 2 < n and line[i + 2] == ' '):
                return i
            i += 1
        return n

    # ------------------------------------------------------------------
    # Statement parsers
    # ------------------------------------------------------------------

    def _tok_b(self, content: str, tokens: List[Token]) -> None:
        """' SignalName DBName [= params...]'"""
        i = 0
        n = len(content)

        m = _WS_RE.match(content, i)
        if m and m.start() == i:
            tokens.append(Token(TokenKind.WHITESPACE, m.group()))
            i = m.end()

        m = _IDENT_RE.match(content, i)
        if m and m.start() == i:
            tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
            i = m.end()

        m = _WS_RE.match(content, i)
        if m and m.start() == i:
            tokens.append(Token(TokenKind.WHITESPACE, m.group()))
            i = m.end()

        m = _IDENT_RE.match(content, i)
        if m and m.start() == i:
            tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
            i = m.end()

        if i < n:
            tokens.append(Token(TokenKind.OTHER, content[i:]))

    def _tok_m(self, content: str, tokens: List[Token]) -> None:
        """' VarName (~)OutputName [formula]'"""
        i = 0
        n = len(content)

        m = _WS_RE.match(content, i)
        if m and m.start() == i:
            tokens.append(Token(TokenKind.WHITESPACE, m.group()))
            i = m.end()

        m = _IDENT_RE.match(content, i)
        if m and m.start() == i:
            tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
            i = m.end()

        m = _WS_RE.match(content, i)
        if m and m.start() == i:
            tokens.append(Token(TokenKind.WHITESPACE, m.group()))
            i = m.end()

        if i >= n:
            return

        if content[i] == '~':
            tokens.append(Token(TokenKind.SYNTAX, '~'))
            i += 1

        m = _IDENT_RE.match(content, i)
        if m and m.start() == i:
            tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
            i = m.end()

        if i < n:
            self._tok_formula(content[i:], tokens)

    def _tok_a(self, content: str, tokens: List[Token]) -> None:
        """' VarName[sp]=Method,Output[,Key=val...]'"""
        i = 0
        n = len(content)

        m = _WS_RE.match(content, i)
        if m and m.start() == i:
            tokens.append(Token(TokenKind.WHITESPACE, m.group()))
            i = m.end()

        m = _IDENT_RE.match(content, i)
        if m and m.start() == i:
            tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
            i = m.end()

        # Optional whitespace before '=' (e.g. 'GG =PPP...')
        m = _WS_RE.match(content, i)
        sp = m.group() if (m and m.start() == i) else ''
        j = i + len(sp)
        if j < n and content[j] == '=':
            if sp:
                tokens.append(Token(TokenKind.WHITESPACE, sp))
                i = j
            tokens.append(Token(TokenKind.SYNTAX, '='))
            i = j + 1

        m = _IDENT_RE.match(content, i)
        if m and m.start() == i:
            tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
            i = m.end()

        while i < n:
            if content[i] == ',':
                tokens.append(Token(TokenKind.SYNTAX, ','))
                i += 1
                m = _IDENT_RE.match(content, i)
                if m and m.start() == i:
                    tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
                    i = m.end()
                    ws_m = _WS_RE.match(content, i)
                    sp2 = ws_m.group() if (ws_m and ws_m.start() == i) else ''
                    j2 = i + len(sp2)
                    if j2 < n and content[j2] == '=':
                        if sp2:
                            tokens.append(Token(TokenKind.WHITESPACE, sp2))
                            i = j2
                        tokens.append(Token(TokenKind.SYNTAX, '='))
                        i = j2 + 1
                        i = self._tok_a_value(content, i, tokens)
            elif content[i] in ' \t':
                m = _WS_RE.match(content, i)
                tokens.append(Token(TokenKind.WHITESPACE, m.group()))
                i = m.end()
            else:
                tokens.append(Token(TokenKind.OTHER, content[i]))
                i += 1

    def _tok_a_value(self, content: str, i: int,
                     tokens: List[Token]) -> int:
        n = len(content)
        if i >= n:
            return i
        if content[i] == '"':
            tokens.append(Token(TokenKind.SYNTAX, '"'))
            i += 1
            close = content.find('"', i)
            if close == -1:
                close = n
            if close > i:
                tokens.append(Token(TokenKind.OTHER, content[i:close]))
            i = close
            if i < n and content[i] == '"':
                tokens.append(Token(TokenKind.SYNTAX, '"'))
                i += 1
        elif content[i] == '$':
            j = i
            while j < n and content[j] not in (',', ' ', '\t'):
                j += 1
            tokens.append(Token(TokenKind.OTHER, content[i:j]))
            i = j
        else:
            m = _IDENT_RE.match(content, i)
            if m and m.start() == i:
                tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
                i = m.end()
        return i

    def _tok_formula(self, content: str, tokens: List[Token]) -> None:
        """Scan formula text, transforming ~identifier references only."""
        i = 0
        n = len(content)
        other_start = 0

        while i < n:
            if content[i] == '~':
                if i > other_start:
                    tokens.append(Token(TokenKind.OTHER, content[other_start:i]))
                tokens.append(Token(TokenKind.SYNTAX, '~'))
                i += 1
                m = _IDENT_RE.match(content, i)
                if m and m.start() == i:
                    tokens.append(Token(TokenKind.IDENTIFIER, m.group()))
                    i = m.end()
                other_start = i
            else:
                i += 1

        if other_start < n:
            tokens.append(Token(TokenKind.OTHER, content[other_start:]))
