FROM node:22-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# No VITE_API_BASE build arg — nginx proxies the backend's routes on the same
# origin as the SPA (see nginx.conf), so the frontend always calls relative
# paths.
RUN npm run build

FROM nginx:alpine
RUN apk add --no-cache openssl
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.d/40-generate-self-signed-cert.sh /docker-entrypoint.d/40-generate-self-signed-cert.sh
RUN chmod +x /docker-entrypoint.d/40-generate-self-signed-cert.sh
EXPOSE 80 443
