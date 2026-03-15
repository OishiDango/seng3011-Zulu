This is a Django Rest Framework that use for API creation

Window initialise steps:

1. Create a Virtual Environment:

python -m venv venv

2. Activate Virtual Environment:

.\venv\Scripts\activate

3. Install Dependencies:

pip install -r requirements.txt

4. Run the Development Server:

python manage.py migrate

python manage.py runserver

5. Check in your browser:

http://127.0.0.1:8000/api/hello/

Don't touch "seng3011" it's the global settings!

core/views.py: Write your API logic and functions here.

core/urls.py: Define the paths for your APIs here.

Lintest:
Run All Checks
To run all automated checks for the project:
python run_checks.py

This script runs:
Lint – checks code style and formatting using flake8
Type Check – verifies Python type hints using mypy
Django Check – validates Django configuration
Tests – runs the test suite using pytest

To automatically fix common linting problems, run:
python fix_lint.py

This script will:
Remove unused imports and variables (autoflake)
Automatically fix many PEP8 formatting issues (autopep8)
Reformat code consistently (black)
Run flake8 again to check remaining issues
