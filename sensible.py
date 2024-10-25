#! /usr/bin/env python3

# Copyright 2019, 2023, 2024 Lassi Kortela
# SPDX-License-Identifier: MIT

import argparse
import configparser
import os
import string
import sys
import tarfile

import yaml

from pose_expr import Symbol
from pose_expr.reader import PoseReader


yaml_ext = ".yaml"


def is_object(x):
    return isinstance(x, list) and isinstance(x[0], Symbol)


def has_head(head, x):
    return is_object(x) and x[0].name == head


def dehead(head, x):
    if has_head(head, x):
        return x[1:]
    raise Exception("Not {} object".format(head))


def assoc_or_none(head, xs):
    for x in xs:
        if has_head(head, x):
            return x
    return None


def assoc(head, xs):
    for x in xs:
        if has_head(head, x):
            return x
    raise Exception("What?")


def complex_property(x, name):
    list = assoc_or_none(name, x)
    if not list:
        return None
    return list[1:]


def simple_property(x, name, predicate):
    def matches(x):
        if isinstance(predicate, type):
            return isinstance(x, predicate)
        else:
            return bool(predicate(x))

    list = assoc_or_none(name, x)
    if not list:
        return None
    if len(list) == 2 and matches(list[1]):
        return list[1]
    raise Exception("Bad property", list)


def value_to_yaml(value):
    if isinstance(value, Symbol):
        return str(value)
    return value


def path_join(*names):
    return "/".join(names)


class FileSystemReader:
    def __init__(self, root):
        self.root = root

    def open_text_file(self, path):
        return open(os.path.join(self.root, path), "r")

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, type, val, tb):
        self.close()


class FileSystemWriter:
    def __init__(self, root):
        self.root = root

    def open_text(self, path):
        path = os.path.join(self.root, path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return open(path, "w")

    def write_file(self, path, content):
        path = os.path.join(self.root, path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        new = path + ".new"
        with open(new, "w") as out:
            out.write(content)
        os.rename(new, path)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, type, val, tb):
        self.close()


class TarReader:
    pass


class TarWriter:
    def init(self, fileobj):
        self.fileobj = fileobj
        self.tar = tarfile.open(fileobj=fileobj, mode="w|")

    def open(name):
        info = tarfile.TarInfo(name=name)
        self.tar.addfile(info, StringIO(strings[i]))

    def close(self):
        self.fileobj.flush
        self.fileobj.close


class Sensible:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.mangled = {}

    def mangle(self, symbol):
        def mangle_char(ch):
            if ch in string.ascii_letters or ch in string.digits:
                return ch
            return "_"

        assert isinstance(symbol, Symbol)
        name = str(symbol)
        m = self.mangled.get(name)
        if not m:
            mangled_set = set(self.mangled.values())
            base = ""
            for ch in name:
                base += mangle_char(ch)
            i = 1
            m = base
            while m in mangled_set:
                i += 1
                m = "{}_{}".format(base, i)
            self.mangled[name] = m
        return m

    def write_yaml_file(self, path, data):
        path = path + yaml_ext
        with self.writer.open_text(path) as out:
            out.write(yaml.dump(data, default_flow_style=False, explicit_start=True))

    def generate_ansible_cfg(self, vars):
        def encode_value(value):
            if value is False:
                return "false"
            elif value is True:
                return "true"
            else:
                raise Exception("Bad ansible.cfg value", value)

        config = configparser.ConfigParser()
        config["defaults"] = {}
        config["defaults"]["inventory"] = "hosts" + yaml_ext
        for var in vars:
            var = dehead("var", var)
            name = var[0]
            value = var[1]
            config["defaults"][self.mangle(name)] = encode_value(value)
        with self.writer.open_text("ansible.cfg") as out:
            config.write(out)

    def generate_hosts_yaml_vars(self, vars):
        table = {}
        for var in vars:
            var = dehead("var", var)
            table[self.mangle(var[0])] = value_to_yaml(var[1])
        return table

    def generate_hosts_yaml_group_hosts(self, hosts):
        table = {}
        for host in hosts:
            host = dehead("host", host)
            table[
                self.mangle(simple_property(host, "name", Symbol))
            ] = self.generate_hosts_yaml_vars(complex_property(host, "vars"))
        return table

    def generate_hosts_yaml(self, groups):
        table = {}
        for group in groups:
            group = dehead("group", group)
            hosts = self.generate_hosts_yaml_group_hosts(
                complex_property(group, "hosts") or []
            )
            vars = self.generate_hosts_yaml_vars(complex_property(group, "vars") or [])
            table[self.mangle(simple_property(group, "name", Symbol))] = {
                "hosts": hosts,
                "vars": vars,
            }
        self.write_yaml_file("hosts", table)

    def generate_module_params(self, module_params):
        return {
            self.mangle(module_param[0]): value_to_yaml(module_param[1])
            for module_param in module_params
        }

    def generate_module_invocation(self, invocation):
        title = simple_property(invocation, "title", str)
        module_and_params = invocation[1]
        module_name = module_and_params[0]
        module_params = module_and_params[1:]
        other_things = invocation[2:]
        table = {"name": title}
        table[self.mangle(module_name)] = self.generate_module_params(module_params)
        for pair in other_things:
            table[self.mangle(pair[0])] = value_to_yaml(pair[1])
        return table

    def generate_role_subdirectory(self, dir, objects, class_name):
        self.write_yaml_file(
            path_join(dir, "main"),
            [
                self.generate_module_invocation(dehead(class_name, obj))
                for obj in objects
            ],
        )

    def generate_role_directory(self, role):
        role = dehead("role", role)
        role_name = simple_property(role, "name", Symbol)
        tasks_dir = path_join("roles", self.mangle(role_name), "tasks")
        handlers_dir = path_join("roles", self.mangle(role_name), "handlers")
        tasks = complex_property(role, "tasks")
        if not tasks:
            raise Exception("Role has no (tasks ...)")
        self.generate_role_subdirectory(tasks_dir, tasks, "task")
        handlers = complex_property(role, "handlers")
        if handlers:
            self.generate_role_subdirectory(handlers_dir, handlers, "handler")

    def generate_play_yaml(self, play):
        play = dehead("play", play)
        return {
            "name": self.mangle(simple_property(play, "name", Symbol)),
            "hosts": [self.mangle(host) for host in complex_property(play, "hosts")],
            "become": simple_property(play, "become", bool),
            "roles": [self.mangle(role) for role in complex_property(play, "roles")],
        }

    def generate_playbook_yaml(self, playbook):
        playbook = dehead("playbook", playbook)
        filename = simple_property(playbook, "name", str)
        self.write_yaml_file(
            filename,
            [
                self.generate_play_yaml(play)
                for play in complex_property(playbook, "plays")
            ],
        )

    def parse_top_level_forms(self, tops):
        options = groups = playbooks = roles = None
        for top in tops:
            if has_head("file-header", top):
                pass
            elif has_head("options", top):
                options = dehead("options", top)
            elif has_head("groups", top):
                groups = dehead("groups", top)
            elif has_head("playbooks", top):
                playbooks = dehead("playbooks", top)
            elif has_head("roles", top):
                roles = dehead("roles", top)
            else:
                raise Exception("Unknown top-level expression", top)
        self.generate_ansible_cfg(options)
        self.generate_hosts_yaml(groups)
        for role in roles:
            self.generate_role_directory(role)
        for playbook in playbooks:
            self.generate_playbook_yaml(playbook)

    def main(self, files):
        for file in files:
            with reader.open_text_file(file) as input:
                self.parse_top_level_forms(PoseReader(input).read_all())


def make_reader(args):
    return FileSystemReader(".")


def make_writer(args):
    return FileSystemWriter(args.output)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-V", "--version", help="show version")
        parser.add_argument(
            "-o",
            "--output",
            help="set output directory, or output tarfile name",
            default=".",
        )
        parser.add_argument(
            "--tar",
            help="read and write files in tar archive, not file system",
            default=".",
        )
        parser.add_argument("--prefix", help="prefix for use in output tar archive")
        parser.add_argument("files", nargs="+", help="S-expression file names")
        args = parser.parse_args()
        with make_reader(args) as reader:
            with make_writer(args) as writer:
                Sensible(reader, writer).main(args.files)
    except KeyboardInterrupt:
        print("")
        sys.exit(1)
