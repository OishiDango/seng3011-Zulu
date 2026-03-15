import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# directories we never want to touch
EXCLUDES = ["venv", ".venv", "__pycache__", ".git", ".mypy_cache", ".pytest_cache"]


def run_command(command: list[str], description: str) -> None:
    print(f"\n=== {description} ===")
    print("Running:", " ".join(command))
    result = subprocess.run(command, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"Failed during: {description}")
        sys.exit(result.returncode)


def ensure_installed(tool: str) -> None:
    if shutil.which(tool) is None:
        print(f"Missing required tool: {tool}\n" f"Install it with: pip install {tool}")
        sys.exit(1)


def main() -> None:
    for tool in ["autoflake", "autopep8", "black", "flake8"]:
        ensure_installed(tool)

    exclude_str = ",".join(EXCLUDES)

    run_command(
        [
            "autoflake",
            "--remove-all-unused-imports",
            "--remove-unused-variables",
            "--recursive",
            "--in-place",
            f"--exclude={exclude_str}",
            ".",
        ],
        "Removing unused imports and variables",
    )

    run_command(
        [
            "autopep8",
            "--in-place",
            "--recursive",
            "--aggressive",
            "--aggressive",
            f"--exclude={exclude_str}",
            ".",
        ],
        "Applying autopep8 fixes",
    )

    run_command(
        [
            "black",
            ".",
            f"--exclude=({'|'.join(EXCLUDES)})",
        ],
        "Formatting code with black",
    )

    run_command(
        [
            "flake8",
            ".",
            f"--exclude={exclude_str}",
        ],
        "Final flake8 check",
    )

    print("\nAll lint auto-fixes completed.")


if __name__ == "__main__":
    main()
