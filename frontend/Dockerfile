FROM node:22-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# The browser (not this container) calls the API, so this must be an address
# reachable from the host — the backend is bound to 127.0.0.1:5001 there.
ARG VITE_API_BASE=http://localhost:5001
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
