FROM tiangolo/uwsgi-nginx-flask:flask-python3.5

MAINTAINER Johannes Elferich <elferich@ohsu.edu>

# Add app configuration to Nginx
COPY nginx.conf /etc/nginx/conf.d/

# Copy sample app
COPY ./app /app
