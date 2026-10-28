# Multi-Stage Hardened Dockerfile for CourseSphere React Frontend
# Stage 1: Build the React application with Node.js 20 LTS
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency files
COPY package*.json ./

# Install dependencies cleanly
RUN npm ci || npm install

# Copy source code and configuration
COPY . .

# Build production assets using Vite
RUN npx vite build

# Stage 2: Serve compiled static files with Nginx (lightweight, secure, non-root)
FROM nginx:1.27-alpine AS runtime

# Remove default nginx welcome page
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled static files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with SPA routing and security headers
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Give nginx user ownership of cache and runtime folders
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /usr/share/nginx/html

USER nginx

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
