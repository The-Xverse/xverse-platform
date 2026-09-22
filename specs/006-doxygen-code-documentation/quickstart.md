# Quickstart: Doxygen Code Documentation

## Prerequisite

Install Doxygen 1.9.1 or newer and use Python 3.11 or newer.

## Validate and generate

From the repository root:

```sh
python3 scripts/check_doxygen.py
```

The command checks production docstring coverage, runs Doxygen, rejects warnings, and confirms:

```text
build/doxygen/html/index.html
```

To run Doxygen directly:

```sh
doxygen Doxyfile
```

Generated files are local build artifacts and are intentionally ignored by Git.

