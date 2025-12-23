FROM node:18-slim
WORKDIR /app
COPY package*.json ./
# HACK: Use 'npm ci' for faster, more stable builds in a pipeline
RUN npm install
COPY . .
RUN npm run build
# SKEPTICAL FIX: Next.js production needs 'npm start' on 0.0.0.0
ENV HOSTNAME "0.0.0.0"
CMD ["npm", "start"]