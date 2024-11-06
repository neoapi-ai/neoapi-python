import os
import sys

from setuptools import find_packages, setup

assert os.path.exists("README.md"), "README.md not found."

try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except Exception as e:
    print(f"Error reading README.md: {e}", file=sys.stderr)
    long_description = ""

setup(
    name="neoapi-sdk",
    version="0.1.3",
    packages=find_packages(include=["neoapi", "neoapi.*"]),
    install_requires=[
        "aiohttp>=3.7.4",
        "backoff>=1.10.0",
        "pydantic>=1.8.2",
        "requests>=2.25.1",
    ],
    author="NeoAPI",
    author_email="hello@neoapi.ai",
    description="Integrate neoapi.ai LLM Analytics with your LLM pipelines.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/neoapi-ai/neoapi-python",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
