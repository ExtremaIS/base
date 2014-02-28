#!/bin/bash
##############################################################################
# base - base directory environment
#   Go base script
# URL: http://www.extellisys.com/products/base
##############################################################################
# This is a base script for Go projects.  To use it, create a soft-link to
# this script from the base directory as follows:
#
#     $ cd ~/projects/_go_/src/github.com/GITHUBNAME/example
#     $ ln -s /usr/local/share/base/go.sh .base
#
# Activate the base with `. base [label]` and deactivate the base with
# `base_deactivate` as usual.
#
# The GOROOT and GOPATH environment variables are automatically set when the
# base is activated, if they are not already set.  Go installations are
# expected to be in directories named "go-VERSION" in /usr/local/opt.  (Note
# that directory names with spaces are not supported.)  If more than one Go
# installation is available, you will be prompted to select an installation to
# use.  Enter a selection by number, or just press enter to accept the
# default.  Create a soft-link in the base directory called ".go" to a
# specific version to select that version automatically, without prompting.
# If there is only one version available, it is selected without prompting.
# The PATH is modified appropriately.
#
# The base is expected to be within a Go workspace, as in the example above.
# If there is a Go dependencies workspace in a directory named `depsws` under
# the base directory, then it is used.
#
# The PATH is automatically reset, and the GOROOT and GOPATH environment
# variables are automatically unset when the base is deactivated.
##############################################################################

_base_activate_pre () {
    if [ -z "$GOROOT" ] ; then
        if [ -h ".go" ] ; then
            export GOROOT="$(readlink ".go")"
        elif [ -d "/usr/local/opt" ] ; then
            _base_select "Go installation" \
                $(ls -d /usr/local/opt/go-* 2>/dev/null | sort -rV)
            if [ -n "$BASE_SELECTION" ] ; then
                export GOROOT="$BASE_SELECTION"
                unset BASE_SELECTION
            else
                echo "warning: no Go installations found" >&2
                echo "warning: unable to set GOROOT" >&2
            fi
        else
            echo "warning: /usr/local/opt not found" >&2
            echo "warning: unable to set GOROOT" >&2
        fi
    fi
    if [ -z "$GOPATH" ] ; then
        GOPATH="$PWD"
        while [ 1 ] ; do
            if [ "$GOPATH" == "/" ] ; then
                echo "warning: not in a Go workspace" >&2
                echo "warning: unable to set GOPATH" >&2
                unset GOPATH
                break
            elif [ "$(basename "$GOPATH")" == "src" ] ; then
                GOPATH="$(dirname "$GOPATH")"
                break
            else
                GOPATH="$(dirname "$GOPATH")"
            fi
        done
    fi
    PATH_ORIG="$PATH"
    if [ -n "$GOROOT" ] ; then
        export PATH="$GOROOT/bin:$PATH"
    fi
    if [ -d "$PWD/depsws/bin" ] ; then
        export PATH="$PWD/depsws/bin:$PATH"
    fi
    if [ -n "$GOPATH" ] ; then
        export PATH="$GOPATH/bin:$PATH"
        if [ -d "$PWD/depsws" ] ; then
            GOPATH="$PWD/depsws:$GOPATH"
        fi
        export GOPATH
    fi
    go version
}

_base_deactivate_post () {
    export PATH=$PATH_ORIG
    unset PATH_ORIG GOROOT GOPATH
}
