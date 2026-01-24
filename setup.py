"""
BitBound - High-Level Embedded Python Library

Setup script for installation.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="bitbound",
    version="0.1.0",
    author="BitBound Team",
    author_email="contact@bitbound.io",
    description="High-Level Embedded Python Library for declarative hardware programming",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bitbound/bitbound",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: MicroPython",
        "Topic :: System :: Hardware",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Scientific/Engineering",
    ],
    keywords="embedded, micropython, hardware, iot, sensors, gpio, i2c, spi",
    python_requires=">=3.7",
    install_requires=[
        # No required dependencies for CPython simulation mode
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=22.0",
            "mypy>=0.9",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/bitbound/bitbound/issues",
        "Documentation": "https://bitbound.readthedocs.io/",
        "Source": "https://github.com/bitbound/bitbound",
    },
)
