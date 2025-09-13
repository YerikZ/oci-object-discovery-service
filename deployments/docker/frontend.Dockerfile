FROM node:20 AS build
WORKDIR /app

COPY oci_object_discovery_service/frontend/package*.json ./
RUN npm install

COPY oci_object_discovery_service/frontend/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY oci_object_discovery_service/frontend/nginx.conf /etc/nginx/conf.d/default.conf
