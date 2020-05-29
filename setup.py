import os
import json
from setuptools import setup, find_packages
from typing import Union, Optional, List
from econuy import __version__


def reqs_pipfile_lock(pipfile_lock: Union[str, os.PathLike, None] = None,
                      exclude: Optional[List[str]] = None):
    if exclude is None:
        exclude = []
    if pipfile_lock is None:
        pipfile_lock = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "Pipfile.lock"
        )
    lock_data = json.load(open(pipfile_lock))
    return [package_name for package_name in
            lock_data.get("default", {}).keys() if package_name not in exclude]


packages = find_packages(".", exclude=["*.test", "*.test.*"])
pipfile_lock_requirements = reqs_pipfile_lock(exclude=None)

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="econuy",
    version=__version__,
    description="Wrangling Uruguay economic data so you don't have to.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Rafael Xavier",
    license="GPL-3.0",
    url="https://github.com/rxavier/econuy",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent"
    ],
    keywords=["uruguay", "economy", "economic", "statistics", "data"],
    install_requires=pipfile_lock_requirements,
    extras_require={
        "pgsql":  ["psycopg2==2.8.5"],
        "flask": ["flask==1.1.2",
                  "flask-sqlalchemy==2.4.1",
                  "flask-bootstrap==3.3.7.1",
                  "flask-wtf==0.14.3",
                  "python-dotenv==0.13.0",
                  "gunicorn==20.0.4"]},
    packages=packages,
    python_requires=">=3.6"
)
