# Zulu Health Alerts API

## Project Overview

This project implements a Django REST Framework microservice that collects and serves public health alert data.  

The service is part of the **Event Intelligence Ecosystem**, where multiple microservices collaborate to collect, process, and analyse event-related data.

This service focuses on:

- Collecting public health event alerts from **ProMED**
- Processing and structuring the collected data
- Providing a REST API for retrieving alert information

---

# API Documentation

Swagger UI:
https://x93rjdxbu4.ap-southeast-2.awsapprunner.com/swagger/

---

# Running the Project with Docker

This project uses **Docker** to ensure a consistent runtime environment across development and deployment platforms.

## 1. Build the Docker Image

```bash
docker build -t zulu-health-alerts-api .
```

## 2. Run the Container

```bash
docker run -p 8000:8000 zulu-health-alerts-api
```

## 3. Access the API

Test endpoint:
http://localhost:8000/api/hello/

---

## Running Locally (Optional)

If you prefer running the project without Docker:

### 1. Create a Virtual Environment

```bash
python -m venv venv
```

### 2. Activate the Virtual Environment

Windows:

```bash
.\venv\Scripts\activate
```

Mac / Linux:

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Development Server

```bash
python manage.py runserver
```

Open in browser:
http://127.0.0.1:8000/api/hello/

## Project Structure

```bash
core/
```

Contains API logic and endpoint implementations.

```bash
core/views.py
```

Defines API functionality.

```bash
core/urls.py
```

Defines API routes.

```bash
seng3011/
```

Global Django project configuration.
⚠ Do not modify this folder unless necessary.

## Code Quality and Testing

Run all automated checks:

```bash
python run_checks.py
```

This script performs:

- **Linting** using flake8
- **Type checking** using mypy
- **Django configuration validation**
- **Test execution** using pytest

---

## Auto Fix Lint Issues

```bash
python fix_lint.py
```

This script will:

- Remove unused imports and variables (**autoflake**)
- Fix many formatting issues (**autopep8**)
- Reformat code consistently (**black**)
- Run flake8 again to verify remaining issues
