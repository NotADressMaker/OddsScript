#!/usr/bin/env python3
"""
Setup script for SportsBetLang
"""

import os

from setuptools import find_packages, setup

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


def read_text(*path_parts: str) -> str:
    with open(os.path.join(ROOT_DIR, *path_parts), "r", encoding="utf-8") as handle:
        return handle.read()


def read_version() -> str:
    version_globals: dict[str, str] = {}
    exec(read_text("sportsbetlang", "__version__.py"), version_globals)
    return version_globals["__version__"]


long_description = read_text("README.md")

setup(
    name="sportsbetlang",
    version=read_version(),
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
        "dev": [
            "mypy>=1.8,<2.0",
            "pytest>=7.4,<9.0",
            "pytest-cov>=4.1,<6.0",
            "ruff>=0.6.0,<1.0.0",
        ],
    },
    entry_points={
        'console_scripts': [
            'sportsbetlang=sportsbetlang.cli:main',
            'betlang=sportsbetlang.betlang_cli:main',
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
