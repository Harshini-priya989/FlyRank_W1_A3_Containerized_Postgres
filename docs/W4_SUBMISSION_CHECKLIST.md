# W4 Auth submission checklist

- [x] Supabase Auth dependency added
- [x] `SUPABASE_URL` and `SUPABASE_KEY` documented in `.env.example`
- [x] `.env` remains git-ignored
- [x] `POST /auth/signup` route added
- [x] `POST /auth/login` route added
- [x] `POST /auth/logout` protected route added
- [x] `GET /public/info` open route added
- [x] `GET /protected/profile` protected route added
- [x] `GET /protected/dashboard` uses the same auth dependency
- [x] Protected routes use `Authorization: Bearer <token>`
- [x] Token verification uses `supabase.auth.get_user(token)`
- [x] Swagger bearer auth padlock is configured with FastAPI `HTTPBearer`
- [ ] Real Supabase project values added locally to `.env`
- [ ] Supabase email confirmation disabled for practice testing
- [ ] Signup/login/profile flow tested with real Supabase account
- [ ] Tampered token returns `401`
- [ ] Swagger screenshot saved as `docs/swagger-auth.png`
- [ ] Final changes pushed to GitHub
