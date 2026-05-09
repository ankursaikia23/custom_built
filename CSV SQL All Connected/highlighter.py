import re
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

class SQLHighlighter(QSyntaxHighlighter):
    def __init__(self, document, app):
        super().__init__(document)
        self.app = app
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#808080"))
        self.keyword_format.setFontWeight(QFont.Weight.Bold)
        self.pattern = re.compile(r"(?!x)x")
        self._last_keywords = []
        self.update_pattern()

    def update_pattern(self):
        try:
            keywords = self.app.get_keywords()
            keywords = [
                k.upper()
                for k in keywords
                if isinstance(k, str) and k.strip()
            ]
            keywords = sorted(set(keywords), key=len, reverse=True)
            if keywords == self._last_keywords:
                return
            self._last_keywords = keywords
            if not keywords:
                self.pattern = re.compile(r"(?!x)x")
                return
            pattern = r"\b(" + "|".join(map(re.escape, keywords)) + r")\b"
            self.pattern = re.compile(pattern)
        except Exception:
            self.pattern = re.compile(r"(?!x)x")

    def highlightBlock(self, text):
        if not self.pattern:
            return
        try:
            for match in self.pattern.finditer(text):
                self.setFormat(
                    match.start(),
                    match.end() - match.start(),
                    self.keyword_format
                )
        except Exception:
            pass