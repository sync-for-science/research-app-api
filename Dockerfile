FROM python:3
MAINTAINER Josh Mandel

# Install required packages
#RUN apt-get update
#RUN apt-get install -y supervisor cron
#RUN apt-get clean

# Create the application directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Setup cron
#COPY crontab /etc/cron.d/reference-research-app-cron
#RUN chmod 0644 /etc/cron.d/reference-research-app-cron
#RUN touch /var/log/cron.log

# Install python dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the codebase
COPY . /usr/src/app

# Configure the app
#RUN pip install -e .
ENV FLASK_APP=/usr/src/app/app.py

RUN flask initdb
RUN flask create_providers

ENTRYPOINT ["flask"]
CMD ["run", "--host", "0.0.0.0"]
