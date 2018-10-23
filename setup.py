
import re
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("jsview/__init__.py") as fh:
    version = re.search(r'^__version__\s*=\s*"(.*)"', fh.read(), re.M).group(1)

setuptools.setup(
    name="jsview",
    version=version,
    author="Fabien Fleutot",
    author_email="fleutot+jsview@gmail.com",
    description="A smarter JSON indenter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fab13n/jsview",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": ['jsview = jsview:main']
    },
    classifiers=(
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
