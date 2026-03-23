from setuptools import setup, find_packages

setup(
    name="bijection",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pygments>=2.9.0",
        "pyyaml>=5.4.0",
    ],
    entry_points={
        "console_scripts": [
            "bijection=bijection.cli:main",
        ],
    },
    python_requires=">=3.8",
)
