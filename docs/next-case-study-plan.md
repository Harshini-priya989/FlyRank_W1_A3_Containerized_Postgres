# How To Add The Next Case Study

## Where It Goes

The next case study will go in:

```text
docs/portfolio-framed-cases.md
```

It should be added after the current capstone case, using the same Week 2 three-beat shape:

1. **The Problem** - what was hard, slow, unclear, or painful before the project.
2. **What I Did** - the decisions I made, what I built, and what I chose not to build.
3. **What Came Of It** - the working result, proof, numbers, screenshots, links, or lessons.

After editing the Markdown, regenerate the PDF:

```powershell
python scripts\generate_portfolio_cases_pdf.py
```

Then commit and push:

```powershell
git add docs/portfolio-framed-cases.md docs/portfolio-framed-cases.pdf
git commit -m "Add next portfolio case study"
git push
```

## Next Real Piece To Add

Next piece of work: **Book Insights API capstone demo after one more improvement**.

The specific next case will cover the capstone after I add one visible proof item, such as a short demo video/GIF, a deployed URL, or screenshots of the Swagger demo flow.

## Reminder Evidence

Reminder set as a calendar file:

```text
docs/next-case-study-reminder.ics
```

Reminder date:

```text
2026-09-13 09:00 Asia/Kolkata
```

Reminder title:

```text
Add next portfolio case study - Book Insights API
```

## Claude Project Context To Keep

Keep the Claude Project active with this standing instruction:

```text
Voice card: clear, honest, practical, warm, no buzzwords.

When helping me add a portfolio case, interview me one question at a time. Use the three-beat shape: the problem, what I did, what came of it. Use my actual project details and do not invent results.
```
