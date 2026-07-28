from setuptools import setup, find_packages

setup(
    name="overlord",
    version="2.0.0",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "cryptography>=41.0.0",
    ],
)
