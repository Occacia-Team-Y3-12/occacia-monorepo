# --- Dependencies Stage ---
FROM node:22-slim AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# --- Builder Stage ---
FROM node:22-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# --- Runtime Stage ---d
FROM node:22-slim AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV HOSTNAME="0.0.0.0"
ENV PORT=3000

# 1. Update package lists
# 2. Force upgrade the vulnerable packages (Trivy will love this)
# 3. Install curl
# 4. Burn the evidence (clear cache) to keep the image tiny
RUN apt-get update && \
    apt-get upgrade -y libc-bin libc6 && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]