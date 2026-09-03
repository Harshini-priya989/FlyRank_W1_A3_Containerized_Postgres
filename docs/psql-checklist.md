# PostgreSQL evidence checklist

Run the stack with `docker compose up --build`.

Open psql:

`docker exec -it taskdb psql -U postgres -d tasks`

Then run:

```sql
\dt
SELECT * FROM tasks;
```

Take a genuine screenshot of the database output and save it as `docs/postgres-data.png`.
