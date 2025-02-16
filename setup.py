from pathlib import Path

import setuptools

VERSION = "0.0.6"

NAME = "better_crud"

INSTALL_REQUIRES = [
    "fastapi>=0.111.0",
    "sqlalchemy>=2.0.30",
    "fastapi_pagination>=0.12.24",
    "pydantic>=2.7.3"
]


setuptools.setup(
    name=NAME,
    keywords=["fastapi", "crud", "async", "sqlalchemy", "pydantic"],
    version=VERSION,
    description="A better CRUD library for FastAPI.",
    url="https://github.com/bigrivi/better_crud",
    project_urls={
        "Source Code": "https://github.com/bigrivi/better_crud",
    },
    author="bigrivi",
    author_email="sunjianghong@gmail.com",
    license="Apache License 2.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Framework :: FastAPI",
        "Typing :: Typed",
    ],
    python_requires=">=3.9",
    install_requires=INSTALL_REQUIRES,
    packages=["better_crud", "better_crud/service",
              "better_crud/service/sqlalchemy"],
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
)
