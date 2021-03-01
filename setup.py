# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 15:35:37 2021

@author: Pavel Gostev
"""

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tekwfm2",
    version="0.1.0",
    author="Pavel Gostev",
    author_email="gostev.pavel@physics.msu.ru",
    description="Parser for Tektronix WFM v.2 binary files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vongostev/tekwfm2",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    include_package_data=True,
    install_requires = [
          'numpy'
          ],
)
