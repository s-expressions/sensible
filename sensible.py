#! /usr/bin/env python3

import argparse
import tarfile
import sys

import pose


def main():
    forms = pose.PoseReader(sys.stdin).read_all()
    for form in forms:
        print(repr(form))


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--prefix")
        parser.add_argument("-o", "--output")
        parser.add_argument("--add-file")
        args = parser.parse_args()
        main()
    except KeyboardInterrupt:
        print("")
        sys.exit(1)
