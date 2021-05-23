from setuptools import find_packages, setup

setup(
    name="tribun",
    version="0.9",
    packages=find_packages(),
    author="aubustou",
    author_email="survivalfr@yahoo.fr",
    description="Add configuration revision for Consul",
    url="https://www.github.com/aubustou/tribun",
    entry_points={"console_scripts": ["tribun = tribun.main:main"]},
    install_requires=[
        "click==8.0.0",
        "python-consul2==0.1.5",
        "dataclasses==0.8; python_version < '3.7'",
    ],
)
