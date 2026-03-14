import os

os.system("flake8 .")
os.system("mypy .")
os.system("python manage.py check")
os.system("pytest --cov=. --cov-report=term-missing")
