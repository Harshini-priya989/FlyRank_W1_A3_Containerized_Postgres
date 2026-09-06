from __future__ import annotations

import os
import subprocess
from datetime import date
from pathlib import Path
from textwrap import wrap

import fitz


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "w4-final-submission.pdf"


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace").strip()


def command_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"Unavailable: {exc}"


def add_wrapped(page: fitz.Page, text: str, x: float, y: float, chars: int, size: int = 10) -> float:
    for paragraph in text.splitlines() or [""]:
        if not paragraph:
            y += size
            continue
        for line in wrap(paragraph, width=chars, replace_whitespace=False):
            page.insert_text((x, y), line, fontsize=size, fontname="helv", color=(0.10, 0.12, 0.16))
            y += size * 1.35
    return y


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

    def ensure(self, needed: float = 80) -> None:
        if self.page is None or self.y + needed > 790:
            self.new_page()

    def heading(self, text: str) -> None:
        self.ensure(45)
        self.page.insert_text((self.margin, self.y), text, fontsize=18, fontname="helv", color=(0.05, 0.17, 0.30))
        self.y += 30

    def subheading(self, text: str) -> None:
        self.ensure(30)
        self.page.insert_text((self.margin, self.y), text, fontsize=12, fontname="helv", color=(0.05, 0.17, 0.30))
        self.y += 19

    def para(self, text: str) -> None:
        self.ensure(24)
        self.y = add_wrapped(self.page, text, self.margin, self.y, 88)
        self.y += 8

    def bullet(self, text: str) -> None:
        self.ensure(24)
        self.page.insert_text((self.margin, self.y), "-", fontsize=10, fontname="helv")
        self.y = add_wrapped(self.page, text, self.margin + 14, self.y, 84)
        self.y += 3

    def code(self, text: str) -> None:
        self.ensure(36)
        for line in text.splitlines():
            for part in wrap(line, width=92, replace_whitespace=False) or [""]:
                self.ensure(16)
                self.page.insert_text((self.margin, self.y), part, fontsize=8.5, fontname="cour", color=(0.02, 0.02, 0.02))
                self.y += 12
        self.y += 9


def main() -> None:
    b = Pdf()
    generated_on = os.getenv("SUBMISSION_DATE", date.today().isoformat())
    git_log = command_output(["git", "log", "--oneline", "-10"])
    remote = command_output(["git", "remote", "-v"]) or "No GitHub remote configured"
    swagger_exists = (ROOT / "docs" / "swagger-auth.png").exists()

    b.new_page()
    b.page.insert_text((54, 86), "W4 Final Submission", fontsize=26, fontname="helv", color=(0.05, 0.17, 0.30))
    b.page.insert_text((54, 122), "FlyRank Internship - Backend Track - Week 2 Assignment A4", fontsize=12, fontname="helv")
    b.page.insert_text((54, 146), "Auth - Login & protect", fontsize=12, fontname="helv")
    b.page.insert_text((54, 172), f"Generated: {generated_on}", fontsize=10, fontname="helv")
    b.y = 220
    b.subheading("Project")
    b.para("FastAPI backend with Supabase Auth, bearer-token protected routes, Swagger authorization, and the existing containerized PostgreSQL task API.")
    b.subheading("GitHub")
    b.code(remote)
    b.subheading("Evidence Note")
    if swagger_exists:
        b.bullet("Swagger screenshot is present at docs/swagger-auth.png.")
    else:
        b.bullet("Swagger screenshot is not present yet. Add docs/swagger-auth.png after testing with your Supabase token.")

    b.new_page("Implemented Requirements")
    for item in [
        "POST /auth/signup validates email/password and calls Supabase sign_up.",
        "POST /auth/login validates credentials and returns Supabase access and refresh tokens.",
        "POST /auth/logout is protected and returns 204.",
        "GET /public/info is open to everyone.",
        "GET /protected/profile verifies Authorization: Bearer <token> with Supabase get_user.",
        "GET /protected/dashboard reuses the same FastAPI dependency.",
        "Missing, malformed, invalid, and expired tokens return 401 JSON errors.",
        "FastAPI HTTPBearer is applied to protected routes so Swagger UI shows bearer auth padlocks.",
        ".env is ignored; .env.example documents Supabase placeholders without real secrets.",
    ]:
        b.bullet(item)

    b.subheading("Recent Commits")
    b.code(git_log)

    b.new_page("Run And Test")
    b.subheading("Setup")
    b.code("Copy-Item .env.example .env\n# Fill SUPABASE_URL and SUPABASE_KEY from Supabase Project Settings -> API\ndocker compose up --build")
    b.subheading("curl Flow")
    b.code(
        'curl -i -X POST http://localhost:8000/auth/signup -H "Content-Type: application/json" -d "{\\"email\\":\\"test@example.com\\",\\"password\\":\\"password123\\"}"\n'
        'curl -i -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d "{\\"email\\":\\"test@example.com\\",\\"password\\":\\"password123\\"}"\n'
        'curl -i http://localhost:8000/protected/profile -H "Authorization: Bearer PASTE_ACCESS_TOKEN_HERE"\n'
        "curl -i http://localhost:8000/protected/profile"
    )
    b.subheading("Swagger")
    b.para("Open http://localhost:8000/docs, click Authorize, paste the access token, and run GET /protected/profile.")

    b.new_page("Key Files")
    b.subheading(".env.example")
    b.code(read_text(".env.example"))
    b.subheading("Auth routes and dependency")
    b.code("Implemented in main.py and auth_service.py.")
    b.subheading("W4 Checklist")
    b.code(read_text("docs/W4_SUBMISSION_CHECKLIST.md"))

    b.doc.save(OUT)
    b.doc.close()
    print(OUT)


if __name__ == "__main__":
    main()
