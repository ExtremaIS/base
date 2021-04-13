#!/usr/bin/env bash

# This base configuration script configures an environment for using a Go
# installation in `/usr/local/opt`.

# If environment variable `GOROOT` is not already set, then it is configured.
# If a link named `.go` exists, then the linked installation is used.
# Otherwise, the user is prompted to select from all directories in
# `/usr/local/opt` that start with `go-`.  If there is only one, it is
# selected automatically.  If there are none, a warning is displayed.
if [ -z "${GOROOT}" ] ; then
  if [ -h ".go" ] ; then
    _base_var_set "GOROOT" "$(readlink ".go")"
  elif [ -d "/usr/local/opt" ] ; then
    _base_select_dir "Go installation" "/usr/local/opt" "go-*"
    if [ -n "${BASE_SELECTION}" ] ; then
      _base_var_set "GOROOT" "/usr/local/opt/${BASE_SELECTION}"
      unset BASE_SELECTION
    else
      echo "warning: unable to set GOROOT" >&2
    fi
  else
    echo "warning: /usr/local/opt not found" >&2
    echo "warning: unable to set GOROOT" >&2
  fi
fi

# If environment variable `GOPATH` is not already set, then it is configured
# by traversing up the directory hierarchy until a `src` directory is found.
# If a `src` directory is not found, a warning is displayed.
if [ -z "${GOPATH}" ] ; then
  _base_gopath="${PWD}"
  while true ; do
    if [ "${_base_gopath}" == "/" ] ; then
      echo "warning: not in a Go workspace" >&2
      echo "warning: unable to set GOPATH" >&2
      break
    elif [ "$(basename "${_base_gopath}")" == "src" ] ; then
      _base_var_set "GOPATH" "$(dirname "${_base_gopath}")"
      break
    else
      _base_gopath="$(dirname "${_base_gopath}")"
    fi
  done
  unset _base_gopath
fi

# When `GOROOT` is set, it is exported.  When it contains a `bin` directory,
# that `bin` directory is prepended to the `PATH`.
if [ -n "${GOROOT}" ] ; then
  export GOROOT
  if [ -d "${GOROOT}/bin" ] ; then
    _base_var_set "PATH" "${GOROOT}/bin:${PATH}"
  fi
fi

# When `GOPATH` is set, it is exported.  When it contains a `bin` directory,
# that `bin` directory is prepended to the `PATH`.
if [ -n "${GOPATH}" ] ; then
  export GOPATH
  if [ -d "${GOPATH}/bin" ] ; then
    _base_var_set "PATH" "${GOPATH}/bin:${PATH}"
  fi
fi

# If the `go` command is found, then `go version` is called so that the user
# can confirm the selected version.  Otherwise a warning is displayed.
if command -v go >/dev/null 2>&1 ; then
  go version
else
  echo "warning: go command not found" >&2
fi
