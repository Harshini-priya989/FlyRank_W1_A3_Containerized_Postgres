from __future__ import annotations

from pathlib import Path
from textwrap import wrap

import fitz


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "prompt-iteration-log.md"
OUT = ROOT / "docs" / "prompt-iteration-log.pdf"


class Pdf:
    def __init__(self) -> None:
        self.doc = fitz.open()
        self.page = None
        self.margin = 54.0
        self.y = 54.0

    def new_page(self) -> None:
        self.page = self.doc.new_page(width=595, height=842)
        self.y = self.margin

    def ensure(self, needed: float) -> None:
        if self.page is None or self.y + needed > 790:
            self.new_page()

    def text(self, value: str, size: int = 10, font: str = "helv", chars: int = 88) -> None:
        for line in wrap(value, width=chars, replace_whitespace=False) or [""]:
            self.ensure(size * 1.5)
            self.page.insert_text((self.margin, self.y), line, fontsize=size, fontname=font, color=(0.10, 0.12, 0.16))
            self.y += size * 1.35
        self.y += 5

    def heading(self, value: str, level: int) -> None:
        if level == 1:
            self.text(value, size=22, chars=50)
        elif level == 2:
            self.y += 6
            self.text(value, size=16, chars=65)
        else:
            self.text(value, size=12, chars=75)

    def code(self, value: str) -> None:
        for line in value.splitlines():
            for part in wrap(line, width=92, replace_whitespace=False) or [""]:
                self.ensure(14)
                self.page.insert_text((self.margin, self.y), part, fontsize=8.3, fontname="cour")
                self.y += 11.5
        self.y += 7


def main() -> None:
    pdf = Pdf()
    in_code = False
    code_lines: list[str] = []

    for raw in SOURCE.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                pdf.code("\n".join(code_lines))
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line:
            pdf.y += 5
            continue
        if line.startswith("### "):
            pdf.heading(line[4:], 3)
        elif line.startswith("## "):
            pdf.heading(line[3:], 2)
        elif line.startswith("# "):
            pdf.heading(line[2:], 1)
        elif line.startswith("- "):
            pdf.text("- " + line[2:], size=10, chars=84)
        else:
            pdf.text(line)

    pdf.doc.save(OUT)
    pdf.doc.close()
    print(OUT)


if __name__ == "__main__":
    main()
