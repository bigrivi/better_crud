from pathlib import Path
import os
import setuptools

INSTALL_REQUIRES = [
    "fastapi>=0.111.0",
    "sqlalchemy>=2.0.30",
    "fastapi_pagination>=0.12.24",
    "pydantic>=2.7.3"
]
about = {}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "better_crud", "_version.py"), "r", encoding="utf-8") as f:
    exec(f.read(), about)

setuptools.setup(
    name=about["__title__"],
    keywords=["fastapi", "better-crud", "crud",
              "async", "sqlalchemy", "pydantic"],
    version=about["__version__"],
    description=about["__description__"],
    url=about["__url__"],
    project_urls={
        "Documentation": "https://bigrivi.github.io/better_crud",
        "Source Code": "https://github.com/bigrivi/better_crud",
    },
    author=about["__author__"],
    author_email=about["__author_email__"],
    license=about["__license__"],
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
