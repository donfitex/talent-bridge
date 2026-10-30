"""Free Render services have no pre-deploy hook; migrate before starting one worker."""

import os
import subprocess
import sys


def main():
    subprocess.run(
        [
            sys.executable,
            "manage.py",
            "migrate",
            "--noinput",
            "--settings=config.settings.migration",
        ],
        check=True,
    )
    subprocess.run(
        [sys.executable, "manage.py", "createcachetable", "--settings=config.settings.migration"],
        check=True,
    )
    subprocess.run(
        [sys.executable, "manage.py", "seed_categories", "--settings=config.settings.migration"],
        check=True,
    )
    os.execvp("gunicorn", ["gunicorn", "config.wsgi:application", "--config", "gunicorn.conf.py"])


if __name__ == "__main__":
    main()
