# Base `2.0.0` Release Notes

Date
: 2021-04-20

## Overview

This is the second major release of Base.  It is a complete rewrite!  See the
project README for an overview and the project manual for usage instructions.

## Major Differences

The major differences with previous versions are as follows:

Base can now be executed in a new Bash shell.  Running `base` configures the
Base environment in a new shell, and running `. base` also copies the
configuration of the current shell environment.  Running `. base_activate`
configures the Base environment in the current shell, like was done in
previous versions.

Base scripts in previous versions used callback functions for activation and
deactivation.  In the new version, library functions provide common
functionality without the need to write explicit callbacks.

For example, configuration in previous versions was written as follows:

```
_base_activate_pre () {
    EXAMPLE=foo
}

_base_deactivate_post () {
    unset EXAMPLE
}
```

The `EXAMPLE` environment variable is set on activation and unset on
deactivation.  In this release, the same functionality is implemented as
follows:

```
_base_var_set EXAMPLE foo
```

Any number of deactivation callback functions can be registered when
necessary.

In previous versions, each directory could only have a single `.base` script.
Because callbacks were used, one could not even source multiple Base scripts,
resulting in the necessity of copy-and-paste custom scripts.  In this release,
`.base` can be a script, a symbolic link, or a directory.  One can easily
combine multiple Base scripts (provided as well as custom) by putting them in
(and/or linking to them from) the `.base` directory.

Note that this release is incompatible with previous releases.  All Base
scripts must be rewritten to work with the new release.
