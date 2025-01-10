"""
CLI for stubgen-pyx, a tool for generating `.pyi` files from Cython modules.
"""
from argparse import ArgumentParser

from stubgen_pyx import stubgen


def main():
    parser = ArgumentParser(description="Generates `.pyi` files from Cython modules in a given package directory.")
    parser.add_argument("package_dir", type=str, help="The path to the package to generate stubs for.")
    args = parser.parse_args()

    stubgen(args.package_dir)


if __name__ == "__main__":
    main()