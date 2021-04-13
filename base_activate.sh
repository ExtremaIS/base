#!/usr/bin/env bash

# # `base_activate` Source
#
# [Base](https://github.com/ExtremaIS/base) configures Bash shell
# environments relative to a directory.  It provides an easy and consistent
# way to load the configuration for diverse projects.
#
# This is the source code for the `base_activate` script, which configures the
# current Bash shell.  The source code includes literate-style documentation
# about the implementation, in Markdown format.  See the `README` or manual
# (`man base`) for usage documentation.
#
# ## Overview
#
# This script must be sourced, not executed normally.  The program has the
# following stages:
#
# 1. (`CURENV_1`) CLI arguments are processed.
# 2. (`CURENV_2`) The environment is configured.
# 3. (`CURENV_3`) The user uses the interactive shell.
# 4. (`CURENV_4`) The user deactivates the base configuration.
#
# It is best to read this script from top to bottom since execution order is
# relevant.

# ### Version
#
# The following variable sets the version.  This variable is available through
# all of the stages.
BASE_VERSION="2.0.0"

##############################################################################
# ## Process Management

# ### Function `_base_help`
#
# This function displays usage information.
#
# Side effects:
#
# * This function prints to `STDOUT`.  Note that the output can be redirected
#   to `STDERR` when called.
_base_help() {
  echo "Usage: base [label]             run in a new Bash shell"
  echo "       . base [label]           copy env and run in a new Bash shell"
  echo "       . base_activate [label]  run in the current Bash shell"
  echo "       base --help              show this usage information and exit"
  echo "       base --version           show version information and exit"
  echo ""
  echo "Base configures a Bash shell environment relative to the current"
  echo "directory.  See the manpage (man base) for details."
}

# ### Normal Execution
#
# This script is not meant to be executed normally.  The `--version` and
# `--help` options are supported, however.  In all other cases, the help is
# displayed on `STDERR` and the script exits.
#
# Bash notes:
#
# * When the program being executed (`${0}`) matches the source file
#   (`${BASH_SOURCE[0]}`), the program is being executed normally.
if [ "${BASH_SOURCE[0]}" == "${0}" ] ; then
  if [ "$#" -eq "1" ] ; then
    case "${1}" in
      "--version" )
        echo "base ${BASE_VERSION}"
        exit 0
        ;;
      "--help" )
        _base_help
        exit 0
        ;;
    esac
  fi

  _base_help >&2
  exit 2
fi

# ### Sourced Execution
#
# When sourced, CLI arguments are processed (`CURENV_1`).
#
# Environment variables:
#
# * `BASE_LABEL_CLI` is set to the label arugment when one is given.
# * `BASE_MODE` is set to `CURENV`.
if [ "$#" -gt "1" ] ; then
  _base_help >&2
  unset -f _base_help
  unset BASE_VERSION
  return 2
elif [ "$#" -eq "1" ] ; then
  case "${1}" in
    "--version" )
      echo "base ${BASE_VERSION}"
      unset -f _base_help
      unset BASE_VERSION
      return 0
      ;;
    "--help" )
      _base_help
      unset -f _base_help
      unset BASE_VERSION
      return 0
      ;;
    * )
      export BASE_LABEL_CLI="${1}"
      ;;
  esac
fi

# shellcheck disable=SC2034
BASE_MODE="CURENV"

# ### Cleaning
#
# The `_base_help` function is no longer used after this point, so it is
# unset.
unset -f _base_help

# After this point, the base environment is configured in the current Bash
# shell.  From the above code, only the following environment variables remain
# set:
#
# * `BASE_VERSION`
# * `BASE_MODE`
# * `BASE_LABEL_CLI`

##############################################################################
# ## Library Functions
#
# This section defines core library functions.
#
# These library functions are only available during environment configuration
# (`CURENV_2`).

# ### Function `_base_lib_array_contains`
#
# This function checks if a global array contains a specific value.
#
# Arguments:
#
# * `ARRAY` (string): global array name
# * `VALUE` (string): value to search for
#
# Returns:
#
# * `0` (`TRUE`): value found in array
# * `1` (`FALSE`): value not found in array
_base_lib_array_contains () {
  local array="${1}[@]" value
  for value in "${!array}" ; do
    [ "${value}" == "${2}" ] && return 0
  done
  return 1
}

# ### Function `_base_lib_array_append`
#
# This function appends a value to a global array.
#
# Arguments:
#
# * `ARRAY` (string): global array name
# * `VALUE` (string): value to append
_base_lib_array_append () {
  eval "${1}[\${#${1}[@]}]=\${2}"
}

# ### Function `_base_lib_set_insert`
#
# This function inserts a value into a global set.
#
# The set is represented as an array with unique values.  The value is
# appended to the array if the value is not found in the array.
#
# Arguments:
#
# * `SET` (string): global set name
# * `VALUE` (string): value to insert
_base_lib_set_insert () {
  _base_lib_array_contains "${1}" "${2}" \
    || _base_lib_array_append "${1}" "${2}"
}

##############################################################################
# ## Deactivation Callbacks
#
# The deactivation callback API provides a way to register functions that are
# called during deactivation.
#
# The deactivation callback API is only available during environment
# configuration (`CURENV_2`).
#
# Deactivation functions are managed using the `BASE_DEACTIVATION_CALLBACKS`
# array.
declare -a BASE_DEACTIVATION_CALLBACKS

# ### Function `_base_deactivation_callback_register`
#
# This function registers a function as a deactivation callback.
#
# This function uses `_base_lib_set_insert`, so it is idempotent.
#
# Arguments:
#
# * `FUNCTION` (string): function name
#
# Side effects:
#
# * The function name is inserted into `BASE_DEACTIVATION_CALLBACKS`.
_base_deactivation_callback_register () {
  _base_lib_set_insert "BASE_DEACTIVATION_CALLBACKS" "${1}"
}

##############################################################################
# ## Variable Management
#
# The variable management API provides a way to save initial environment
# variable values so that they can be restored during deactivation.
#
# The variable management API is only available during environment
# configuration (`CURENV_2`).
#
# The following arrays are used to track environment variable changes:
#
# * `BASE_VAR_VARS` stores the names of environment variables that are
#   modified.
# * `BASE_VAR_EXPORTS` stores the names of modified environment variables that
#   should be exported.
declare -a BASE_VAR_VARS
# shellcheck disable=SC2034
declare -a BASE_VAR_EXPORTS

# ### Function `_base_var_save`
#
# This function saves an environment variable before it is modified.
#
# The name of the environment variable is inserted into `BASE_VAR_VARS`.  The
# previous value is saved if it has not already been saved.  This ensures that
# the original value is saved even in cases when the environment variables is
# modified multiple times.  If the environment variable is exported, the name
# of the environment variable is inserted into `BASE_VAR_EXPORTS`.
#
# Arguments:
#
# * `VARIABLE` (string): global variable name
#
# Side effects:
#
# * The variable name is inserted into `BASE_VAR_VARS` if it is not already in
#   the array.
# * The previous value is saved in `BASE_VAR_PREV_${VARIABLE}` if it is not
#   already saved.
# * When a previous value is saved, the variable name is inserted into
#   `BASE_VAR_EXPORTS` if the original variable was exported.
#
# Bash notes:
#
# * This function makes use of Bash syntax like the following: `${!prev+x}`.
#   The exclamation point (`!`) creates an indirect expansion: the string
#   value of `${prev}` is used as the variable name.  The plus (`+`) syntax
#   indicates a value to use instead of the actual value of a variable.  The
#   condition `[[ -n "${!1+x}" && -z "${!prev+x}" ]]` is therefore true the
#   variable referred to by the first function argument (`${1}`) is set and
#   the variable referred to by "${prev}" is not set, regardless of the
#   values.
_base_var_save () {
  local prev="BASE_VAR_PREV_${1}"
  _base_lib_set_insert "BASE_VAR_VARS" "${1}"
  if [[ -n "${!1+x}" && -z "${!prev+x}" ]] ; then
    eval "${prev}=\${!1}"
    if [[ "$(declare -p "${1}")" =~ ^declare\ -[^x]*x[^x]*\  ]] ; then
      _base_lib_set_insert "BASE_VAR_EXPORTS" "${1}"
    fi
  fi
}

# ### Function `_base_var_set`
#
# This function sets an environment variable after saving an initial value.
#
# This function does not export the variable.  To export, do so explicitly
# after calling this function.
#
# Arguments:
#
# * `VARIABLE` (string): global variable name
# * `VALUE` (string): value to set
#
# Side effects:
#
# * The side effects of `_base_var_save` occur when a variable is first set.
# * The environment variable specified by `VARIABLE` is set to `VALUE`.
_base_var_set () {
  _base_var_save "${1}"
  eval "${1}=\${2}"
}

# ### Function `_base_var_unset`
#
# This function unsets an environment variable after saving an initial value.
#
# Arguments:
#
# * `VARIABLE` (string): global variable name
#
# Side effects:
#
# * The side effects of `_base_var_save` occur when a variable is first unset.
# * The environment variable specified by `VARIABLE` is unset.
_base_var_unset () {
  _base_var_save "${1}"
  unset "${1}"
}

##############################################################################
# ## Label Management
#
# The label management API provides a way to set the base label.
#
# The label management API is only available during environment configuration
# (`CURENV_2`).

# ### Function `_base_label_set`
#
# This function sets the base label.
#
# Arguments:
#
# * `LABEL` (string): new base label
#
# Side effects:
#
# * Environment variable `BASE_LABEL` is set to `LABEL`.
_base_label_set () {
  BASE_LABEL="${1}"
}

# ### Function `_base_label_set_default`
#
# This function sets the base label if one was not specified on the
# command-line.
#
# Arguments:
#
# * `LABEL` (string): default base label
#
# Side effects:
#
# * Environment variable `BASE_LABEL` is set to `LABEL` if `BASE_LABEL_CLI` is
#   not set.
_base_label_set_default () {
  test -z "${BASE_LABEL_CLI}" && BASE_LABEL="${1}"
}

##############################################################################
# ## User Interaction Functions
#
# User interaction functions are available for interacting with the user
# during environment configuration.
#
# User interaction functions are only available during environment
# configuration (`CURENV_2`).

# ### Function `_base_select`
#
# This function queries the user to select an option.
#
# An indexed list of options is displayed, and the user selects an option by
# index.  An invalid selection results in the deafult: the first option.  The
# selected option value (not index) is stored in the `BASE_SELECTION`
# environment variable.
#
# If only one option is passed, it is selected without querying the user.  If
# no options are passed, a warning is displayed and `BASE_SELECTION` is unset.
#
# Arguments:
#
# * `LABEL` (string): label to display in the selection prompt
# * `OPTION` (string): one or more options to select from
#
# Returns:
#
# * `0`: `BASE_SELECTION` is set
# * `1`: `BASE_SELECTION` is unset
#
# Side effects:
#
# * When multiple options are available, the list of options is displayed and
#   a selection is read.
# * Environment variable `BASE_SELECTION` is set or unset.
_base_select () {
  declare -g BASE_SELECTION

  if [ "$#" -le "1" ] ; then
    echo "warning: _base_select called without options" >&2
    unset BASE_SELECTION
    return 1
  fi

  if [ "$#" -eq "2" ] ; then
    BASE_SELECTION="${2}"
    return 0
  fi

  local args=( "$@" ) len=0 idx=1
  len=${#args[@]}

  while [ "${idx}" -lt "${len}" ] ; do
    echo "${idx}) ${args[$idx]}"
    (( idx++ ))
  done
  read -rp "Select ${1} [1]: " idx
  idx="$(echo "${idx}" | grep "^[0-9]\+$")"
  if [[ "${idx}" != "" && "${idx}" -gt "0" && "${idx}" -lt "${len}" ]] ; then
    BASE_SELECTION="${args[${idx}]}"
    return 0
  fi

  # shellcheck disable=SC2034
  BASE_SELECTION="${array[0]}"
  return 0
}

# ### Function `_base_select_dir`
#
# This function queries the user to select a directory.
#
# This function calls `_base_select` with directory names as options.  If no
# directories are found, a warning is displayed.
#
# Arguments:
#
# * `LABEL` (string): label to display in the selection prompt
# * `DIRECTORY` (string): parent directory path
# * `GLOB` (string): directory options pattern
#
# Returns:
#
# * `0`: `BASE_SELECTION` is set
# * `1`: `BASE_SELECTION` is unset
#
# Side effects:
#
# * When multiple options are available, the list of options is displayed and
#   a selection is read.
# * Environment variable `BASE_SELECTION` is set or unset.
_base_select_dir () {
  local opts=()
  while IFS= read -r -d $'\0'; do
    opts+=( "$(basename "${REPLY}" )" )
  done < <(find "${2}" -maxdepth 1 -type d -name "${3}" -print0 | sort -zrV)
  if [ "${#opts[@]}" -gt "0" ] ; then
    _base_select "${1}" "${opts[@]}"
    return $?
  else
    echo "warning: no ${1} directories found" >&2
    return 1
  fi
}

##############################################################################
# ## Core Configuration
#
# This section configures a base environment.

# ### Base Directory
#
# The full path of the base directory is stored in the `BASE` environment
# variable.
BASE="${PWD}"

# ### Base Label
#
# If the base label was not specified using a CLI argument, then it defaults
# to the basename of the base directory.
#
# Note that the base label can be changed in user configuration through the
# label management API.
if [ -n "${BASE_LABEL_CLI}" ] ; then
  BASE_LABEL="${BASE_LABEL_CLI}"
else
  BASE_LABEL="$(basename "${BASE}")"
fi

# ### Function `_base_ps_update`
#
# This function updates the terminal prompt and title.
#
# This is an internal function that should not be executed directly.  It is
# called via `PROMPT_COMMAND`.
#
# If the `BASE_NO_TITLE` environment variable is set, then the title is not
# updated.
#
# Side effects:
#
# * The prompt and title are updated by setting the `PS1` environment
#   variable.
_base_ps_update () {
  local lpath suffix
  if [ "${BASE}" == "${PWD}" ] ; then
    lpath="[${BASE_LABEL}] "
  elif [ "${BASE}/" == "${PWD:0:$((${#BASE}+1))}" ] ; then
    lpath="[${BASE_LABEL}] ${PWD:$((${#BASE}+1))}"
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
  if [ -n "${BASE_NO_TITLE+x}" ] ; then
    PS1="${lpath}${suffix}"
  else
    PS1="\[\e]2;${lpath}\a\]${lpath}${suffix}"
  fi
}

# ### Configure prompt
#
# The current value of the `PS1` environment variable is saved, and the
# `PROMPT_COMMAND` environment variable is set to `_base_ps_update`.
_base_var_save "PS1"
_base_var_set "PROMPT_COMMAND" "_base_ps_update"

# To execute another function each time the prompt is displayed, add the
# function to `PROMPT_COMMAND`.  For example, the following can be used to
# also run function `foo`:
#
#     PROMPT_COMMAND="foo;_base_ps_update"

# ### Function `bcd`
#
# This function changes to a directory relative to the base directory.
#
# This function is called directly from the command line.
#
# Arguments:
#
# * `DIR` (string): directory relative to the base directory (optional)
#
# Returns:
#
# * `0`: directory change succeeded
# * `1`: directory change failed
# * `2`: too many arguments
#
# Side effects:
#
# * The current directory is changed when successful.
# * An error is displayed when the directory does not exist.
# * Usage is displayed when called with too many arguments.
bcd () {
  if [ "$#" -gt "1" ] ; then
    echo "usage: bcd [dir]" >&2
    return 2
  fi
  cd "${BASE}/${1}" || return 1
  return 0
}

# ### Function `_base_bcd_complete`
#
# This function generates an array of completion options for the `bcd`
# command.
#
# This is an internal function that should not be executed directly.  It is
# registered as an autocompletion hook for `bcd` via the `complete` builtin.
#
# Arguments:
#
# * `COMMAND` (string): name of the command being completed (unused)
# * `PARAM` (string): `bcd` parameter than is requesting completion
#
# Side effects:
#
# * The `COMPREPLY` array is set to the list of possible completions.
_base_bcd_complete () {
  local curr="${BASE}" rest="${2##*/}"
  if [ ${#2} -gt ${#rest} ] ; then
    curr="${BASE}/${2%/*}"
  fi
  COMPREPLY=()
  while IFS= read -r -d $'\0'; do
    COMPREPLY+=( "${REPLY#${BASE}/}" )
  done < <(find "${curr}" -mindepth 1 -maxdepth 1 -type d -name "${rest}*" -print0)
  if [ ${#COMPREPLY[*]} -eq 1 ] ; then
    curr="${BASE}/${COMPREPLY[0]}"
    COMPREPLY=()
    while IFS= read -r -d $'\0'; do
      COMPREPLY+=( "${REPLY#${BASE}/}/" )
    done < <(find "${curr}" -maxdepth 1 -type d -print0)
    if [ ${#COMPREPLY[*]} -eq 1 ] ; then
      COMPREPLY=( "${COMPREPLY[0]%/}" )
    fi
  fi
}

# ### Configure `bcd` Completion
#
# `bcd` is configured to use the `_base_bcd_complete` function for completion.
complete -o filenames -F _base_bcd_complete bcd

# ### Function `base_deactivate`
#
# This function deactivates a base environment.
#
# Side effects:
#
# * Deactivation callbacks are called in reverse order.
# * Previous environment variables are restored.
# * Completion for the `bcd` command is removed.
# * Base functions and environment variables are unset.

base_deactivate () {
  local idx prev var
  for (( idx="${#BASE_DEACTIVATION_CALLBACKS[@]}"-1 ; idx>=0 ; idx-- )); do
    eval "${BASE_DEACTIVATION_CALLBACKS[${idx}]}"
  done

  for var in "${BASE_VAR_VARS[@]}" ; do
    prev="BASE_VAR_PREV_${var}"
    if [ -n "${!prev+x}" ] ; then
      eval "${var}=\${!prev}"
      if _base_lib_array_contains "BASE_VAR_EXPORTS" "${var}" ; then
        # shellcheck disable=SC2163
        export "${var}"
      fi
      unset "${prev}"
    else
      unset "${var}"
    fi
  done

  complete -r bcd

  unset BASE_VERSION BASE_MODE BASE BASE_LABEL
  unset BASE_VAR_VARS BASE_VAR_EXPORTS BASE_DEACTIVATION_CALLBACKS
  unset -f _base_lib_array_contains
  unset -f _base_lib_array_append
  unset -f _base_lib_set_insert
  unset -f _base_ps_update _base_bcd_complete bcd f base_deactivate
}

##############################################################################
# ## User Configuration
#
# Configuration scripts in the base directory are sourced to load any user
# configuration.  Configuration can be done in any of the following ways:
#
# * `.base` can be a Bash script.
# * `.base` can be a link to a Bash script, such as one in `/usr/share/base`.
# * `.base` can be a directory containing any number of Bash scripts and links
#   to Bash scripts.
#
# When a directory is used, the scripts are sourced in sorted order.  Numeric
# prefixes can be used, for example, to make the scripts load in the desired
# order.
if [ -e ".base" ] ; then
  for config in $(find -L ".base" -type f | sort) ; do
    # shellcheck disable=SC1090
    source "${config}"
  done
fi

##############################################################################
# ## Configuration Cleanup
#
# The functions and environment variables used for configuration are unset.
unset -f _base_select _base_select_dir
unset -f _base_label_set _base_label_set_default
unset -f _base_var_save _base_var_set _base_var_unset
unset -f _base_deactivation_callback_register
unset BASE_LABEL_CLI BASE_SELECTION

# The cache of commands is reset to ensure that any new `PATH` settings are
# used.
hash -r

# When the user uses the interactive shell (`CURENV_3`), the following
# environment variables remain set:
#
# * `BASE_VERSION` is the software version.
# * `BASE_MODE` is set to one of the following values:
#     * (`NEWENV` when this script is executed normally)
#     * (`CPYENV` when this script is sourced)
#     * `CURENV` when `base_activate` is sourced
# * `BASE` is the base directory path.
# * `BASE_LABEL` is the base label.
# * `BASE_VAR_VARS` is the array of modified environment variables.
# * `BASE_VAR_EXPORTS` is the array of modified environment variables that
#   were exported before base configuration.
# * `BASE_DEACTIVATION_CALLBACKS` is the array of deactivation callback
#   functions.
#
# The following functions remain set:
#
# * The core library functions:
#     * `_base_lib_array_contains`
#     * `_base_lib_array_append`
#     * `_base_lib_set_insert`
# * `_base_ps_update` updates the prompt.
# * `bcd` is used by the user.
# * `_base_bcd_complete` handle `bcd` completion.
# * `base_deactivate` is used by the user.
