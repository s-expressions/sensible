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

## Rationale

Sensible is intentionally "dumb": it supports only a very limited
S-expression surface syntax ([POSE -- Portable
S-expressions](https://github.com/s-expressions/pose)) and does not
have its own programming language (Scheme or Lisp dialect). If it were
to have its own syntax and Lisp dialect, people would never agree on
which one. Some would want Scheme, some Common Lisp, and some Clojure.
And even if that question was settled, people would not agree on which
language subset and extensions to offer.

It's easy to use any existing Lisp dialect and implementation to
generate S-expressions suitable for Sensible, and this is what people
should do.

Sensible itself is written in Python since everyone who has Ansible
will also have Python. An earlier prototype was written in Scheme.
