# Zulu Health Alerts API

## Project Overview
This project implements a Django REST Framework microservice for collecting and serving public health event alerts using ProMED data.

The service forms part of the Event Intelligence Ecosystem and provides structured alert data via REST APIs.

---

## Setup

Create virtual environment

python -m venv venv

Activate

.\venv\Scripts\activate

Install dependencies

pip install -r requirements.txt

---

## Run the Server

python manage.py migrate

python manage.py runserver

Open browser:

http://127.0.0.1:8000/api/hello/

---

##Swagger API documentation:

http://127.0.0.1:8000/swagger/

---

## Docker

Build image

docker build -t zulu-health-alerts-api .

Run container

docker run -p 8000:8000 zulu-health-alerts-api

---

## Code Quality

Run all checks

python run_checks.py

Includes:

- flake8
- mypy
- django check
- pytest

Auto fix lint issues

python fix_lint.py

---

## Project Structure

core/ – API logic  
scraper/ – data collection  
seng3011/ – Django project settings （Don't edit!!!)
