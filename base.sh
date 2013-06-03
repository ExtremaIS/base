#!/bin/bash

##############################################################################
# base.sh - base directory environment
##############################################################################
#
# Author: Travis Cardwell <travis.cardwell@yuzutechnology.com>
# URL: http://www.yuzutechnology.com/products/base (coming soon)
# Version: 1.0.1
# Copyright (c) 2011-2013, Yuzu Technology, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
##############################################################################

##############################################################################
# base creates an environment with a base directory.  The environment has a
# clean prompt and terminal title, and it provides a command for changing
# directories relative to the base directory.  See the man page for details.
##############################################################################

##############################################################################
# _base_ps_update: updates the terminal prompt and title
#
# Arguments: <none>
# Returns: <none>
# Side Effects:
#   * writes to PS1, updating both the prompt and title
#
# This is an internal function that should not be executed directly.  It is
# called via PROMPT_COMMAND.
##############################################################################
_base_ps_update () {
    local lpath suffix
    if [ "${BASE}" == "${PWD}" ] ; then
        lpath="[${BASE_LABEL}] "
    elif [ "${BASE}/" == "${PWD:0:$((${#BASE}+1))}" ] ; then
        lpath="[${BASE_LABEL}] ${PWD:${#BASE}}"
    elif [ "${HOME}" == "${PWD}" ] ; then
        lpath="(${BASE_LABEL}) ~"
    elif [ "${HOME}/" == "${PWD:0:$((${#HOME}+1))}" ] ; then
        lpath="(${BASE_LABEL}) ~${PWD:${#HOME}}"
    else
        lpath="(${BASE_LABEL}) ${PWD}"
    fi
    suffix="\$ "
    if [ "${USER}" == "root" ] ; then
        suffix="# "
    fi
    export PS1="\[\e]2;${lpath}\a\]${lpath}${suffix}"
}

##############################################################################
# _base_autocomplete: generates an array of completion options for bcd
#
# Arguments:
#   * $2 (string): the bcd parameter that is requesting completion
# Returns: <none>
# Side Effects:
#   * writes to COMPREPLY, for use in autocompletion
#
# This is an internal function that should not be executed directly.  It is
# registered as an autocompletion hook for bcd via the `complete` builtin.
##############################################################################
_base_autocomplete () {
    local curr rest
    curr="${BASE}"
    rest="${2##*/}"
    if [ ${#2} -gt ${#rest} ] ; then
        curr="${BASE}/${2%/*}"
    fi
    COMPREPLY=( $( find "${curr}" -mindepth 1 -maxdepth 1 -type d \
                                  -name "${rest}*" \
                 | sed "s#^${BASE}/\(.*\)\$#\1/#" ) )
    if [ ${#COMPREPLY[*]} -eq 1 ] ; then
        COMPREPLY=( $( find "${BASE}/${COMPREPLY[0]}" -maxdepth 1 -type d \
                     | sed "s#^${BASE}/\(.*\)\$#\1/#" ) )
        if [ ${#COMPREPLY[*]} -eq 1 ] ; then
            COMPREPLY=( ${COMPREPLY[0]%/} )
        fi
    fi
}

##############################################################################
# bcd: base change directory: changes to a directory relative to the base
#
# Arguments:
#   * $1 (string): a directory relative to the base (optional)
# Returns: <none>
# Side Effects:
#   * changes the current directory or prints an error if the directory does
#     not exist
#
# This function is called directly from the command line.
##############################################################################
bcd () {
    cd "${BASE}/${1}"
}

##############################################################################
# base_deactivate: deactivate base and restore previous settings
#
# Arguments: <none>
# Returns: <none>
# Side Effects:
#   * unsets variables and functions used by this script
#   * restores previous PS1 and PROMPT_COMMAND values when applicable
#   * removes autocompletion rules for bcd
#
# This function is called directly from the command line.
##############################################################################
base_deactivate () {
    unset PROMPT_COMMAND
    export PS1="${BASE_OLD_PS1}"
    unset BASE_OLD_PS1
    if [ -n "${BASE_OLD_PROMPT_COMMAND}" ] ; then
        export PROMPT_COMMAND="${BASE_OLD_PROMPT_COMMAND}"
        unset BASE_OLD_PROMPT_COMMAND
    fi
    complete -r bcd
    unset -f _base_ps_update
    unset -f _base_autocomplete
    unset -f bcd
    unset -f base_deactivate
    unset BASE_LABEL
    if [ -f "${BASE}/.base.deactivate.sh" ] ; then
        source "${BASE}/.base.deactivate.sh"
    fi
    unset BASE
}

##############################################################################
# (main): the following code is executed when the script is sourced
#
# Side Effects:
#   * current PS1 and PROMPT_COMMAND values are backed up when applicable
#   * variables used by this script are set
#   * autocompletion rules for bcd are added
##############################################################################
if [[ "$#" -gt 1 || "${1}" == "--help" ]]; then
    echo "Syntax: . base [label]" 1>&2
    echo "The \".\" at the beginning is required. " \
         "Type \"man base\" for details." 1>&2
else
    if [ -f ".base.activate.sh" ] ; then
        source ".base.activate.sh"
    fi
    export BASE_OLD_PS1="${PS1}"
    if [ -n "${PROMPT_COMMAND}" ] ; then
        export BASE_OLD_PROMPT_COMMAND="${PROMPT_COMMAND}"
    fi
    if [ "$#" -eq 1 ] ; then
        export BASE_LABEL="${1}"
    else
        export BASE_LABEL="$(basename "$(pwd)")"
    fi
    export BASE="${PWD}"
    export PROMPT_COMMAND="_base_ps_update"
    complete -o filenames -F _base_autocomplete bcd
fi
