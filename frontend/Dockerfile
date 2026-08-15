FROM node:22-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/src ./src
COPY frontend/vite.config.js .

RUN npm run build

# Serve with nginx
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Vite custom server fallback (optional – Vite's index.html already handles routing)
# If you need client‑side routing, uncomment the below:
#
#COPY --from=build /app/index.html /usr/share/nginx/html/404.html
#RUN echo 'location / { try_files $uri $uri/ /index.html; }' > /etc/nginx/conf.d/default.conf

EXPOSE 80