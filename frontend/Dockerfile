# --- Dependencies Stage ---
# Install all NPM packages required for the build
FROM node:22-slim AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# --- Builder Stage ---
# Compile the Next.js application
FROM node:22-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# --- Runtime Stage ---
# Minimal production image containing only the compiled code
FROM node:22-slim AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV HOSTNAME="0.0.0.0"
ENV PORT=3000

# Install curl for container healthchecks and clear the apt cache
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a restricted non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy the standalone Next.js build and static assets
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Drop root privileges
USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]