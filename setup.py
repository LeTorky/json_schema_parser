from pathlib import Path
from setuptools import setup, find_packages

setup(
    name="json-schema-parser",
    version="1.0.0",
    description="Convert between JSON schema definitions and Pydantic models",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Abdelrahman Torky",
    author_email="24torky@gmail.com",
    url="https://github.com/24torky/json-schema-parser",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
