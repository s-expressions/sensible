#! /usr/bin/env python3

import argparse
import tarfile
import sys

import pose


def is_head(head, x):
    return isinstance(x, list) and isinstance(x[0], pose.Symbol) and x[0].name == head


def dehead(head, x):
    if not is_head(head, x):
        raise Exception("What?")
    return x[1:]


def assoc(head, xs):
    for x in xs:
        if is_head(head, x):
            return x[1:]
    raise Exception("What?")


def main():
    tops = pose.PoseReader(sys.stdin).read_all()
    if len(tops) != 1:
        raise Exception("What?")
    top = dehead("ansible", tops[0])
    options = assoc("options", top)
    groups = assoc("groups", top)
    playbooks = assoc("playbooks", top)
    roles = assoc("roles", top)
    print(repr(options))
    print(repr(groups))
    print(repr(playbooks))
    print(repr(roles))


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
