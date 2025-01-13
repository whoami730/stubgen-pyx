from pathlib import Path

from setuptools import setup

from stubgen_pyx._version import __version__

setup(
    name="stubgen-pyx",
    version=__version__,
    packages=["stubgen_pyx"],
    entry_points={
        "console_scripts": [
            "stubgen-pyx = stubgen_pyx.__main__:main",
        ]
    },
    install_requires=["Cython~=3.0.11", "setuptools"],
    description="Generates `.pyi` files from Cython modules in a given package directory.",
    long_description=(Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
    author="Jonathan Townsend",
    url="https://github.com/jon-edward/stubgen-pyx",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
