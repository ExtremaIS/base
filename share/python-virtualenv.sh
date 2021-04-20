#!/usr/bin/env bash

# This base configuration script enables a Python virtual environment by
# prepending its `bin` directory to the `PATH`.

# If a directory or link named `virtualenv` exists, it is selected
# automatically.
#
# Otherwise, the user is prompted to select from all directories that start
# with `virtualenv`.  If there is only one, it is selected automatically.  If
# there are none, a warning is displayed.
#
# When `PATH` is modified, `python --version` is called so that the user can
# confirm the selected version.
if [ -e "virtualenv" ] ; then
  _base_var_set "PATH" "$(pwd)/virtualenv/bin:${PATH}"
  python --version
else
  _base_select_dir "Python virtual environment" "." "virtualenv*"
  if [ -n "${BASE_SELECTION}" ] ; then
    _base_var_set "PATH" "$(pwd)/${BASE_SELECTION}/bin:${PATH}"
    unset BASE_SELECTION
    python --version
  else
    echo "warning: no Python virtual environment loaded" >&2
  fi
fi
