from setuptools import setup, find_packages

setup(
    name="dq-ge-framework",
    version="0.1.0",
    description="Data Quality Framework based on Great Expectations",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "great-expectations==1.11.3",
        "sqlalchemy>=2.0.23",
        "pandas>=2.1.4",
        "pyspark>=3.4.0,<4",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.3",
        "pydantic-settings>=2.1.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "dq=dq_framework.cli:main",
        ],
    },
)
