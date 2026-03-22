# occacia-monorepo
AI-Powered Occasion Planning Marketplace (Group Y3-12)

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
