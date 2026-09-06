# GitHub submission steps

This local clone does not have a GitHub remote configured yet.

Create a public GitHub repository named:

```text
FlyRank_W1_A3_Containerized_Postgres
```

Then run these commands from the project folder:

```powershell
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/FlyRank_W1_A3_Containerized_Postgres.git
git add docs/final-submission.pdf scripts/generate_submission_pdf.py docs/GITHUB_SUBMISSION.md
git commit -m "Add final submission document"
git push -u origin main
```

Submit this GitHub link after replacing `YOUR_GITHUB_USERNAME`:

```text
https://github.com/YOUR_GITHUB_USERNAME/FlyRank_W1_A3_Containerized_Postgres
```

Before final submission, add a genuine PostgreSQL screenshot at `docs/postgres-data.png` after running:

```powershell
docker compose up --build
docker exec -it taskdb psql -U postgres -d tasks
```

Inside `psql`:

```sql
\dt
SELECT * FROM tasks;
```
