FROM nginx:1.31.9-alpine-slim@sha256:5bfced78d24d644270bedb0a9968697042e38d5c03fb6354603df025279c1cbe
COPY nginx/site.conf /etc/nginx/conf.d/default.conf
COPY web/index.html web/health.json /srv/compass/
EXPOSE 8080
