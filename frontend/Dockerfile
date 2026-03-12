# ==========================================
# STAGE 1: Dependencies
# ==========================================
FROM node:22-slim AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# ==========================================
# STAGE 2: Builder
# ==========================================
FROM node:22-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ==========================================
# STAGE 3: Runtime (minimal final image)
# ==========================================
FROM node:22-slim AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV HOSTNAME="0.0.0.0"
ENV PORT=3000

# 🛠️ THE FIX IS HERE 🛠️
# Do the heavy lifting while you are still ROOT.
# Added clean up commands so your image doesn't get bloated.
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Now that curl is installed, we lock down the permissions
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy only what's needed to run
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Put on the restricted suit
USER nextjs
EXPOSE 3000

# Go to sleep and wait for traffic
CMD ["node", "server.js"]