# occacia-monorepo
AI-Powered Occasion Planning Marketplace (Group Y3-12)

## Google Calendar setup (local dev)

1. Create an OAuth client in Google Cloud Console using your local host (`http://localhost:3000/oauth/callback`) as the redirect URI and whitelist any variants you use (127.0.0.1, https, etc.).
2. Add the generated `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` plus the same redirect URI to your `.env` (or `.env.local`) along with a random `CALENDAR_TOKEN_ENCRYPTION_KEY`. You can use the example entries in `.env.example`.
3. Make sure the consent screen is in Testing mode and your account is added as a test user so Google allows connections before publishing.
4. Restart the backend (and frontend if you changed `NEXT_PUBLIC_GOOGLE_REDIRECT_URI`) so the new settings are loaded.

## Manual Server Restart

The production deployment workflow copies the app to `~/occacia-app` on the server.
If you run Docker Compose manually, do it from that directory or pass the compose file explicitly.

From inside the app directory:

```bash
cd ~/occacia-app
sudo docker compose down
sudo docker compose up --build -d
```

From any directory:

```bash
sudo docker compose \
  -f ~/occacia-app/docker-compose.yml \
  --env-file ~/occacia-app/.env \
  down

sudo docker compose \
  -f ~/occacia-app/docker-compose.yml \
  --env-file ~/occacia-app/.env \
  up --build -d
```

If you run `docker-compose` or `docker compose` from `~` without `-f`, Docker will fail with
`no configuration file provided: not found` because there is no compose file in that directory.
