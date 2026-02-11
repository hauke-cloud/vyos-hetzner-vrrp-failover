"""Setup script for Hetzner VRRP Failover package"""

from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text().splitlines()
        if line.strip() and not line.startswith('#')
    ]

setup(
    name="hetzner-vrrp-failover",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Hetzner Cloud VRRP Failover Script for VyOS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/hetzner-vrrp-failover",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "hetzner-vrrp-failover=hetzner_vrrp_failover.cli:main",
        ],
    },
)
