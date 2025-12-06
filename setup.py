from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="pater-extension",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered product aggregation extension with predictive offer analytics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YOUR_USERNAME/pater",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Office/Business :: Financial :: Point-Of-Sale",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "black>=24.1.1",
            "flake8>=7.0.0",
            "isort>=5.13.2",
            "mypy>=1.8.0",
            "pylint>=3.0.3",
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.3",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "pre-commit>=3.6.0",
        ],
        "ml": [
            "torch>=2.3.1",
            "torch-geometric>=2.5.2",
            "lightgbm>=4.3.1",
            "fbprophet>=1.1.5",
            "statsmodels>=0.14.2",
        ],
        "docs": [
            "mkdocs>=1.5.3",
            "mkdocs-material>=9.5.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "pater-api=backend.main:app",
            "pater-train=scripts.train_models:main",
        ],
    },
    include_package_data=True,
    keywords="chrome-extension e-commerce price-prediction machine-learning ai shopping",
    project_urls={
        "Bug Reports": "https://github.com/YOUR_USERNAME/pater/issues",
        "Source": "https://github.com/YOUR_USERNAME/pater",
        "Documentation": "https://github.com/YOUR_USERNAME/pater/wiki",
    },
)
