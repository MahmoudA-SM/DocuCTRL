---
title: DocuCTRL
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

# DocuCTRL

Document Control System deployed on Hugging Face Spaces + Supabase.

## Security configuration (required for public Spaces)

Set these environment variables in your Hugging Face Space secrets:

- `JWT_SECRET`: long random secret for signing tokens
- `SUPABASE_URL`: your Supabase project URL
- `SUPABASE_KEY`: service role key for private storage access
- `SUPABASE_BUCKET`: private bucket name
- `SUPABASE_SIGNED_URL_TTL`: signed URL expiry in seconds
- `ACCESS_TOKEN_EXPIRE_MINUTES`: token lifetime in minutes
- `COOKIE_SECURE`: `true` for HTTPS deployments
- `COOKIE_SAMESITE`: `lax` or `strict`
- `ALLOWED_ORIGINS`: comma-separated list of allowed origins (leave empty to allow all)
