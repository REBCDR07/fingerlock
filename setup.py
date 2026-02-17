from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="fingerlock",
    version="1.0.0",
    author="Elton Hounnou",
    description="Sécurité automatique par détection d'activité clavier/souris",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pynput>=1.7.0",
        "PyYAML>=5.4.0",
        "setuptools>=69.0.0",
    ],
    entry_points={
        "console_scripts": [
            "fingerlock=fingerlock.cli:main",
        ],
    },
)
