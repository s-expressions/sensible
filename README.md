# Sensible

## S-expressions for Ansible

**Sensible** is a preprocessor that turns a file of S-expressions into
a set of YAML files for use with Ansible.

You can write playbooks, roles, and host groups as S-expressions. The
syntax is simpler and more consistent than YAML, and you can write
everything in one file instead of gardening a whole directory tree
full of little YAML files. The specific syntax we use is Portable
S-expressions (POSE).

## Status

Sensible is being used to configure real servers, but there are still
sharp edges and the UI is lacking convenience and polish.

## How to install

``` Shell
python3 -m pip install PyYAML
python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps pose_expr
```

## Usage

The command `sensible foo.pose` will generate Ansible files into the
current directory.

The command `sensible foo.pose -o foo` will generate them into a
subdirectory `foo`.
