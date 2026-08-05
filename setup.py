from setuptools import setup, find_packages

setup(
    name="mc-preview",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "Pillow",
    ],
    entry_points={
        "console_scripts": [
            "preview=preview.cli:main",
        ],
    },
)
