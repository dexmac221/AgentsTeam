import pathlib
from setuptools import setup, find_packages

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="snake-game",
    version="0.1.0",
    author="Your Name",
    author_email="you@example.com",
    description="A classic Snake game implemented in Python using Pygame.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/snake-game",
    packages=find_packages(exclude=("tests",)),
    python_requires=">=3.8",
    install_requires=[
        "pygame>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "snake=snake.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Games/Entertainment :: Arcade",
    ],
    include_package_data=True,
    zip_safe=False,
)