from __future__ import annotations

import json
import subprocess
from datetime import date
from pathlib import Path
from textwrap import wrap

import fitz


ROOT = Path(__file__).resolve().parents[1]
SCRAPER = ROOT / "scraper"
OUT = ROOT / "docs" / "w5-final-submission.pdf"


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
        self.y = 54.0
        self.margin = 54.0

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
        x = self.margin + 14
        for line in wrap(text, width=84, replace_whitespace=False):
            self.ensure(15)
            self.page.insert_text((x, self.y), line, fontsize=10, fontname="helv", color=(0.10, 0.12, 0.16))
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
    books = json.loads(read_text(SCRAPER / "output" / "books.json"))
    report = json.loads(read_text(SCRAPER / "output" / "run-report.json"))
    errors = json.loads(read_text(SCRAPER / "output" / "errors.json"))
    remote = command_output(["git", "remote", "-v"])
    git_log = command_output(["git", "log", "--oneline", "-12"])

    b = Pdf()
    b.new_page()
    b.page.insert_text((54, 86), "W5 Final Submission", fontsize=26, fontname="helv", color=(0.05, 0.17, 0.30))
    b.page.insert_text((54, 122), "FlyRank Internship - Backend Track - Week 5 Assignment A9", fontsize=12, fontname="helv")
    b.page.insert_text((54, 146), "The polite scraper", fontsize=12, fontname="helv")
    b.page.insert_text((54, 172), f"Generated: {date.today().isoformat()}", fontsize=10, fontname="helv")
    b.y = 220
    b.subheading("Submission Link")
    b.code(remote)
    b.subheading("Result")
    b.bullet(f"Valid unique records: {len(books)}")
    b.bullet(f"Failed pages recorded: {len(errors)}")
    b.bullet(f"Catalogue pages: {report['catalogue_pages']}")
    b.bullet(f"Discovered URLs: {report['discovered_urls']}")
    b.bullet(f"Cache hits on latest rerun: {report['cache_hits']}")

    b.new_page("Evidence")
    for item in [
        "Target is Books to Scrape, a public scraping practice sandbox.",
        "Scope is limited to the first three catalogue pages.",
        "robots.txt result is documented as 404/no robots file found.",
        "Every real request sends a clear user-agent, timeout, status check, cache, and delay.",
        "Each book record is normalized and validated with Pydantic before storage.",
        "A deliberate bad URL is skipped and reported while the 60 good records survive.",
        "The README includes schema, run command, politeness rules, ethics note, limitation, and report.",
    ]:
        b.bullet(item)

    b.subheading("Run Report")
    b.code(json.dumps(report, indent=2))

    b.new_page("Files To Submit")
    b.bullet("GitHub repository URL.")
    b.bullet("scraper/README.md")
    b.bullet("scraper/src/main.py")
    b.bullet("scraper/output/books.json")
    b.bullet("scraper/output/run-report.json")
    b.bullet("scraper/output/errors.json")
    b.bullet("docs/w5-final-submission.pdf, if the form asks for a document.")
    b.subheading("Recent Commits")
    b.code(git_log)

    b.new_page("Checklist")
    b.code(read_text(SCRAPER / "SUBMISSION_CHECKLIST.md"))
    b.doc.save(OUT)
    b.doc.close()
    print(OUT)


if __name__ == "__main__":
    main()
