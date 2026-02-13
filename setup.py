"""Setup script for taskuccino package."""
from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="taskuccino",
    version="0.1.0",
    author="Cyborg-Squirrel",
    description="A chat bot for forming positive habits and closing the loop on undone tasks.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Cyborg-Squirrel/Taskuccino",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "discord.py>=2.3.2",
        "requests>=2.31.0",
        "ollama>=0.0.1",
    ],
    extras_require={
        "dev": [
            "pylint>=2.17.0",
            "pytest>=7.0",
            "black>=23.0",
        ],
    },
)
