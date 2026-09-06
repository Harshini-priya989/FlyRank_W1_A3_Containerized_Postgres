from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path
from textwrap import wrap

import fitz


ROOT = Path(__file__).resolve().parents[1]
CAPSTONE = ROOT / "capstone"
OUT = ROOT / "docs" / "capstone-final-submission.pdf"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()


def command_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"Unavailable: {exc}"


class Pdf:
    def __init__(self) -> None:
        self.doc = fitz.open()
        self.page = None
        self.margin = 54.0
        self.y = 54.0

    def new_page(self, title: str | None = None) -> None:
        self.page = self.doc.new_page(width=595, height=842)
        self.y = self.margin
        if title:
            self.heading(title)

    def ensure(self, needed: float = 60) -> None:
        if self.page is None or self.y + needed > 790:
            self.new_page()

    def heading(self, text: str) -> None:
        self.ensure(45)
        self.page.insert_text((self.margin, self.y), text, fontsize=18, fontname="helv", color=(0.05, 0.17, 0.30))
        self.y += 30

    def subheading(self, text: str) -> None:
        self.ensure(28)
        self.page.insert_text((self.margin, self.y), text, fontsize=12, fontname="helv", color=(0.05, 0.17, 0.30))
        self.y += 19

    def para(self, text: str) -> None:
        self.ensure(24)
        for paragraph in text.splitlines() or [""]:
            if not paragraph:
                self.y += 10
                continue
            for line in wrap(paragraph, width=88, replace_whitespace=False):
                self.ensure(15)
                self.page.insert_text((self.margin, self.y), line, fontsize=10, fontname="helv", color=(0.10, 0.12, 0.16))
                self.y += 13.5
        self.y += 8

    def bullet(self, text: str) -> None:
        self.ensure(24)
        self.page.insert_text((self.margin, self.y), "-", fontsize=10, fontname="helv")
        for line in wrap(text, width=84, replace_whitespace=False):
            self.ensure(15)
            self.page.insert_text((self.margin + 14, self.y), line, fontsize=10, fontname="helv", color=(0.10, 0.12, 0.16))
            self.y += 13.5
        self.y += 3

    def code(self, text: str) -> None:
        self.ensure(36)
        for line in text.splitlines():
            for part in wrap(line, width=92, replace_whitespace=False) or [""]:
                self.ensure(16)
                self.page.insert_text((self.margin, self.y), part, fontsize=8.5, fontname="cour")
                self.y += 12
        self.y += 9


def main() -> None:
    b = Pdf()
    remote = command_output(["git", "remote", "-v"])
    commits = command_output(["git", "log", "--oneline", "-10"])

    b.new_page()
    b.page.insert_text((54, 86), "Capstone Final Submission", fontsize=25, fontname="helv", color=(0.05, 0.17, 0.30))
    b.page.insert_text((54, 122), "Backend AI Engineering - Your 10x Solution", fontsize=12, fontname="helv")
    b.page.insert_text((54, 146), "Book Insights API", fontsize=12, fontname="helv")
    b.page.insert_text((54, 172), f"Generated: {date.today().isoformat()}", fontsize=10, fontname="helv")
    b.y = 220
    b.subheading("Submit")
    b.bullet("GitHub repository link")
    b.bullet("Overview document: capstone/My 10x Solution - Harshini Priya.md")
    b.subheading("GitHub")
    b.code(remote)

    b.new_page("Concepts")
    for item in [
        "API endpoints: FastAPI routes for books, search, recommendations, login, tagging, jobs, and reports.",
        "Database: SQLite persists users, books, jobs, reports, and usage/cost logs.",
        "Authentication: bearer tokens protect job, AI, report, and cost-log routes.",
        "Background jobs: import route uses FastAPI BackgroundTasks.",
        "Reporting: report route generates a PDF.",
        "Caching logic: list/search/recommendation endpoints use a 60-second cache.",
        "LLM integration: a narrow validated tagging/summarization endpoint logs estimated cost.",
    ]:
        b.bullet(item)
    b.para("No swaps were needed.")

    b.new_page("Run")
    b.code("cd capstone\npython -m pip install -r requirements.txt\npython -m uvicorn src.app:app --reload --port 8010")
    b.para("Open http://localhost:8010/docs and use demo@example.com / password123 for login.")
    b.subheading("Recent Commits")
    b.code(commits)

    b.new_page("Overview")
    b.code(read_text(CAPSTONE / "My 10x Solution - Harshini Priya.md"))
    b.doc.save(OUT)
    b.doc.close()
    print(OUT)


if __name__ == "__main__":
    main()
