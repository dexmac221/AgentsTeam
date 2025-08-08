import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text(encoding="utf-8")

def get_version():
version_file = (HERE / "tinycli" / "__init__.py").read_text(encoding="utf-8")
for line in version_file.splitlines():
if line.startswith("__version__"):
return line.split("=")[1].strip().strip('"\'')
raise RuntimeError("Unable to find __version__ in tinycli/__init__.py")

setup(
name="tinycli",
version=get_version(),
description="A tiny Python CLI that prints the current date/time and exits.",
long_description=README,
long_description_content_type="text/markdown",
url="https://github.com/yourusername/tinycli",
author="Your Name",
author_email="you@example.com",
license="MIT",
packages=find_packages(include=["tinycli", "tinycli.*"]),
python_requires=">=3.8",
install_requires=[],
entry_points={
"console_scripts": [
"tinycli = tinycli.__main__:main",
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