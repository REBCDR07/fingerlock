from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="fingerlock",
    version="1.0.0",
    author="Elton Hounnou",
    author_email="votre-email@example.com",
    description="Sécurité automatique par détection d'activité clavier/souris",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/votre-username/fingerlock",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Monitoring",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
    install_requires=[
        "opencv-python>=4.5.0",
        "pynput>=1.7.0",
        "PyYAML>=5.4.0",
    ],
    entry_points={
        "console_scripts": [
            "fingerlock=fingerlock.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "fingerlock": ["config/*.yaml"],
    },
)
