# Week 1 A3 submission checklist

- [ ] Public GitHub repository updated (same repo as A1/A2)
- [ ] At least 6 honest A3 commits
- [ ] Dockerfile present
- [ ] compose.yaml has `api` and `db` services
- [ ] PostgreSQL uses named `taskdata` volume
- [ ] `.env` is git-ignored
- [ ] `.env.example` is committed
- [ ] No real secret is committed
- [ ] API uses parameterized Postgres queries
- [ ] Table auto-creates and seed rows are inserted only when empty
- [ ] CRUD works with 200/201/204/400/404 behavior
- [ ] `docker compose down` then `docker compose up` preserves rows
- [ ] README contains one-command run instructions
- [ ] README contains endpoint table and curl example
- [ ] Genuine PostgreSQL data screenshot added at `docs/postgres-data.png`
