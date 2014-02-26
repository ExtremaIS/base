#!/bin/bash
##############################################################################
# base - base directory environment
#   Python base script
# URL: http://www.extellisys.com/products/base
##############################################################################
# This is a base script for Python projects.  To use it, create a soft-link
# to this script from the base directory as follows:
#
#     $ cd ~/projects/example
#     $ ln -s /usr/local/share/base/python.sh .base
#
# Activate the base with `. base [label]` and deactivate the base with
# `base_deactivate` as usual.
#
# A Python virtual environment is automatically activated when the base is
# activated.  Python virtual environments are expected to be in directories
# named "virtualenv-VERSION" in the base directory.  If more than one virtual
# environment is available, you will be prompted to select an environment to
# use.  Enter a selection by number, or just press enter to accept the
# default.  Create a soft-link in the base directory called "virtualenv" to a
# specific version to select that version automatically, without prompting.
# If there is only one version available, it is selected without prompting.
#
# The Python virtual environment is automatically deactivated when the base is
# deactivated.
##############################################################################

_base_activate_pre () {
    if [ -e "virtualenv" ] ; then
        source "virtualenv/bin/activate"
        python --version
    else
        _base_select "virtual environment" \
            $(ls -d virtualenv* 2>/dev/null | sort -rV)
        if [ -n "$BASE_SELECTION" ] ; then
            source "$BASE_SELECTION/bin/activate"
            unset BASE_SELECTION
            python --version
        else
            echo "warning: no virtual environment loaded" >&2
        fi
    fi
}

_base_deactivate_post () {
    if [ "$(type -t "deactivate")" == "function" ] ; then
        deactivate
    fi
}
