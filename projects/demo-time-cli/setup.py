import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text(encoding="utf-8")

setup(
    name="tiny-cli-datetime",
    version="0.1.0",
    description="A tiny Python CLI that prints the current date/time and exits.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/tinycli",
    author="Your Name",
    author_email="you@example.com",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "tiny-date = tiny_cli_datetime.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
    ],
    include_package_data=True,
    zip_safe=False,
)