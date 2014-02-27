#!/bin/bash
##############################################################################
# base - base directory environment
#   Haskell base script
# URL: http://www.extellisys.com/products/base
##############################################################################
# This is a base script for Haskell projects.  To use it, create a soft-link to
# this script from the base directory as follows:
#
#     $ cd ~/projects/example
#     $ ln -s /usr/local/share/base/haskell.sh .base
#
# Activate the base with `. base [label]` and deactivate the base with
# `base_deactivate` as usual.
#
# The PATH environment variable is automatically modified when the base is
# activated.  Haskell installations are expected to be in directories named
# "ghc-VERSION" in /usr/local/opt.  If more than one Haskell installation is
# available, you will be prompted to select an installation to use.  Enter a
# selection by number, or just press enter to accept the default.  Create a
# soft-link in the base directory called ".haskell" to a specific version to
# select that version automatically, without prompting.  If there is only one
# version available, it is selected without prompting.  If a
# .cabal-sandbox/bin directory is found in the base directory, then it
# prepended to the PATH.
#
# The PATH is automatically reset when the base is deactivated.
##############################################################################

_base_activate_pre() {
    local haskell
    if [ -h ".haskell" ] ; then
        haskell="$(readlink ".haskell")"
    elif [ -d "/usr/local/opt" ] ; then
        _base_select "Haskell installation" \
            $(ls -d /usr/local/opt/ghc-* 2>/dev/null | sort -rV)
        if [ -n "$BASE_SELECTION" ] ; then
            haskell="$BASE_SELECTION"
            unset BASE_SELECTION
        else
            echo "warning: no Haskell installations found" >&2
        fi
    else
        echo "warning: /usr/local/opt not found" >&2
    fi
    if [ -n "$haskell" ] ; then
        PATH_ORIG="$PATH"
        export PATH="$haskell/bin:$PATH"
        if [ -d "$PWD/.cabal-sandbox/bin" ] ; then
            export PATH="$PWD/.cabal-sandbox/bin:$PATH"
        fi
        ghc --version
    fi
}

_base_deactivate_post() {
    if [ -n "$PATH_ORIG" ] ; then
        export PATH=$PATH_ORIG
        unset PATH_ORIG
    fi
}
