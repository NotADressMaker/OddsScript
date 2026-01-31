#!/usr/bin/env python3
"""
Setup script for SportsBetLang
"""

from setuptools import setup, find_packages
import os

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
with open(readme_path, 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="sportsbetlang",
    version="0.1.0",
    author="NotADressMaker",
    description="Advanced sports betting analytics library with ML and statistical analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NotADressMaker/SportsBetLang",
    packages=find_packages(include=['lib', 'lib.*', 'tools', 'tools.*', 'sportsbetlang', 'sportsbetlang.*']),
    py_modules=['lexer', 'parser', 'interpreter'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
        "Topic :: Scientific/Engineering :: Mathematics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires='>=3.7',
    install_requires=[
        # No external dependencies - uses only Python standard library
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'sportsbetlang=sportsbetlang.cli:main',
        ],
    },
    package_data={
        'lib': ['*.py'],
        'tools': ['*.py'],
    },
    include_package_data=True,
    zip_safe=False,
    keywords='sports betting analytics machine-learning statistics nhl nfl nba mlb',
    project_urls={
        'Documentation': 'https://github.com/NotADressMaker/SportsBetLang/tree/main/docs',
        'Source': 'https://github.com/NotADressMaker/SportsBetLang',
        'Tracker': 'https://github.com/NotADressMaker/SportsBetLang/issues',
    },
)
