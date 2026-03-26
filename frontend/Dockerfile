FROM node:20-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
RUN apk add --no-cache apache2-utils
ARG AUTH_USER=admin
ARG AUTH_PASS=changeme
RUN htpasswd -cb /etc/nginx/.htpasswd "$AUTH_USER" "$AUTH_PASS"
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
