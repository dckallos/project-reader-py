from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="project-reader-py",
    version="1.0.0",
    author="Daniel",
    author_email="daniel@example.com",
    description="An MCP server that allows Cline to read project files while excluding any files captured in .gitignore",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/project-reader-py",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "project-reader-py=src.main:main",
        ],
    },
    data_files=[
        ("", ["mcp.json"]),
    ],
    include_package_data=True,
)
