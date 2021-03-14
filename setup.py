#!/bin/env python
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hopalyser",
    version="1.0.0",
    author="Philipp Rothenhäusler",
    author_email="philipp.rothenhaeusler@gmail.com",
    description="A network hop analyser using ZeroMQ with MsgPack.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/prothen/hopalyser",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
