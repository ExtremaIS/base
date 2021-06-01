#!/usr/bin/env bash

# # `base` Source
#
# [Base](https://github.com/ExtremaIS/base) configures Bash shell
# environments relative to a directory.  It provides an easy and consistent
# way to load the configuration for diverse projects.
#
# This is the source code for the `base` script, which configures a new Bash
# shell.  The source code includes literate-style documentation about the
# implementation, in Markdown format.  See the `README` or manual (`man base`)
# for usage documentation.
#
# ## Overview
#
# This script can be run in two different ways:
#
# * When executed normally, the new Bash shell is passed environment variables
#   that are exported from the current Bash shell, but it is not passed other
#   environment variables or command aliases.  It sources `${HOME}/.bashrc`
#   when the file exists.  With this usage, referred to as `NEWENV`, the
#   program has the following stages:
#     1. (`NEWENV_1`) CLI arguments are processed.
#     2. (`NEWENV_2`) A new Bash shell process is executed, replacing the
#        current process.
#     3. (`NEWENV_3`) The environment is configured.
#     4. (`NEWENV_4`) The user uses the interactive shell.  Exiting the shell
#        does not require any special processing.
#
# * When sourced, the new Bash shell is passed all environment variables and
#   aliases from the current Bash shell.  In this case, it does *not* source
#   the `${HOME}/.bashrc` configuration.  With this usage, referred to as
#   `CPYENV`, the program has the following stages:
#     1. (`CPYENV_1`) CLI arguments are processed.
#     2. (`CPYENV_2`) The configuration of the current environment is loaded.
#     3. (`CPYENV_3`) A new Bash shell process is executed.  It is passed the
#        serialized environment configuration.
#     4. (`CPYENV_4`) The environment is configured.
#     5. (`CPYENV_5`) The user uses the interactive shell.
#     6. (`CPYENV_6`) When the user exits the shell, the environment in the
#        parent shell is cleaned.
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
# When executed normally, CLI arguments are processed (`NEWENV_1`) and a new
# Bash shell process is executed, replacing the current process (`NEWENV_2`).
# If the execution of the new process fails, an error is displayed and the
# program exits.
#
# Bash notes:
#
# * When the program being executed (`${0}`) matches the source file
#   (`${BASH_SOURCE[0]}`), the program is being executed normally.
#
# Environment variables:
#
# * `BASE_MODE` is set to `NEWENV`.
# * `BASE_NEW` is set to indicate that a new Base environment is being
#   configured.
# * `BASE_LABEL_CLI` is set to the label argument when one is given.
if [ "${BASH_SOURCE[0]}" == "${0}" ] ; then
  if [ "$#" -gt "1" ] ; then
    _base_help >&2
    exit 2
  elif [ "$#" -eq "1" ] ; then
    case "${1}" in
      "--version" )
        echo "base ${BASE_VERSION}"
        exit 0
        ;;
      "--help" )
        _base_help
        exit 0
        ;;
      * )
        export BASE_LABEL_CLI="${1}"
        ;;
    esac
  fi

  exec /usr/bin/env \
    BASE_MODE="NEWENV" \
    BASE_NEW=1 \
    bash --init-file "${BASH_SOURCE[0]}"

  echo "error: Base unable to execute a new Bash shell" >&2
  exit 1
fi

# ### Function `_base_select_env`
#
# This function selects a list of environment variable names to be copied to
# the new Bash shell process when sourcing this script.
#
# The output of `declare -p` may contain newlines, so this function outputs
# variable names that occur in `declare` syntax following a newline in the
# value of an environment variable.  This causes two issues:
#
# * Some variable names that are output may not actually exist.  This issue is
#   resolved by simply ignoring the variables that do not exist.
# * Some variable names may be output more than once.  This issue is resolved
#   by filtering the list through `sort -u`.
#
# Note that some environment variables that should not be copied are filtered
# from the output.
#
# Side effects:
#
# * This function prints to `STDOUT`.
_base_select_env () {
  local defn line var
  while IFS=$'\n' read -r line ; do
    if [[ "${line}" =~ ^declare\ - ]] ; then
      defn="${line#declare -* }"
      var="${defn%%=*}"
      case "${var}" in
        BASH_* | FUNCNAME | GROUPS | cmd | val  | \
        BASE* | decl | defn | line | var )
          ;;
        * )
          echo "${var}"
          ;;
      esac
    fi
  done < <(declare -p)
}

# ### Function `_base_load_env`
#
# This function queries the current Bash shell environment and outputs
# configuration commands that are to be executed in the new Bash shell
# environment.
#
# Environment variables are queried using the `declare -p` command.  Some
# environment variable values may contain newlines, so the output must be
# processed specially.  This implementation does so within Bash to avoid
# creating too many processes.
#
# Side effects:
#
# * This function prints to `STDOUT`.
_base_load_env () {
  local decl line var
  while IFS=$'\n' read -r var ; do
    decl=""
    while IFS=$'\n' read -r line ; do
      if [ -z "${decl}" ] ; then
        decl="${line}"
      else
        decl="${decl}\"\$'\\n'\"${line}"
      fi
    done < <(declare -p "${var}" 2>/dev/null)
    [ -z "${decl}" ] || echo "${decl}"
  done < <(_base_select_env | sort -u)
  alias -p
}

# ### Sourced Execution
#
# When sourced, CLI arguments are processed (`CPYENV_1`), the configuration of
# the current environment is copied (`CPYENV_2`), and a new Bash shell process
# is executed (`CPYENV_3`).  After the new process exits, the environment in
# the parent shell is cleaned (`CPYENV_6`).
#
# Environment variables:
#
# * `BASE_ENV` contains the configuration commands to execute in the new
#   process.  It is not passed to the new process.
# * `BASE_ENV_SER` contains the serialized configuration of the current Bash
#   shell.  It is passed to the new process.
# * `BASE_MODE` is set to `CPYENV`.
# * `BASE_NEW` is set to indicate that a new Base environment is being
#   configured.
# * `BASE_LABEL_CLI` is set to the label argument when one is given.
if [ -z "${BASE_NEW+x}" ] ; then
  if [ "$#" -gt "1" ] ; then
    _base_help >&2
    unset -f _base_help _base_select_env _base_load_env
    unset BASE_VERSION
    return 2
  elif [ "$#" -eq "1" ] ; then
    case "${1}" in
      "--version" )
        echo "base ${BASE_VERSION}"
        unset -f _base_help _base_select_env _base_load_env
        unset BASE_VERSION
        return 0
        ;;
      "--help" )
        _base_help
        unset -f _base_help _base_select_env _base_load_env
        unset BASE_VERSION
        return 0
        ;;
      * )
        export BASE_LABEL_CLI="${1}"
        ;;
    esac
  fi

  unset -f _base_help

  declare -a BASE_ENV
  readarray -t BASE_ENV < <(_base_load_env)
  unset -f _base_select_env _base_load_env

  /usr/bin/env \
    BASE_ENV_SER="$(declare -p BASE_ENV)" \
    BASE_MODE="CPYENV" \
    BASE_NEW=1 \
    bash --init-file "${BASH_SOURCE[0]}"

  unset BASE_VERSION BASE_ENV
  return 0
fi

# ### Cleaning
#
# Only the new Bash shell process executes code after this point.  The above
# functions and `BASE_NEW` environment variable are no longer used, so they
# are unset.
unset -f _base_help _base_select_env _base_load_env
unset BASE_NEW

# ### Function `_base_restore_env`
#
# This function loops through configuration commands and determines which ones
# should be executed.  It filters out environment variable declarations for
# which the environment variable already exists and is read-only.
#
# Environment variables:
#
# * `BASE_ENV` (global) must exist.
#
# Side effects:
#
# * This function prints to `STDOUT`.
_base_restore_env () {
  local defcmd envcmd var rstcmd
  for rstcmd in "${BASE_ENV[@]}" ; do
    if [[ "${rstcmd}" =~ ^declare ]] ; then
      defcmd="${rstcmd#declare -* }"
      var="${defcmd%%=*}"
      envcmd="$(declare -p "${var}" 2>/dev/null)"
      if [[ -z "${envcmd}" || "${envcmd}" =~ ^declare\ -[^r\ ]*\  ]] ; then
        echo "${rstcmd}"
      fi
    else
      echo "${rstcmd}"
    fi
  done
}

# ### New Shell Initialization
#
# When sourced, the new Bash shell is initialized by evaluating the serialized
# configuration commands, restoring the array, and then evaluating the
# commands selected by the `_base_restore_env` function.  Note that this
# evaluation cannot be done within a function, where the declarations would
# create variables local to the function.  The configuration environment
# variables are not longer used, so they are unset.
#
# The `_base_restore_env` function is no longer used, so it is unset.
#
# When executed normally, the new Bash shell is initialized by sourcing
# `${HOME}/.bashrc` if it exists.
if [ -n "${BASE_ENV_SER}" ] ; then
  eval "${BASE_ENV_SER}"
  while IFS=$'\n' read -r rstcmd ; do
    eval "${rstcmd}"
  done < <(_base_restore_env)
  unset BASE_ENV BASE_ENV_SER rstcmd
fi

unset -f _base_restore_env

if [ "${BASE_MODE}" = "NEWENV" ] ; then
  if [ -f "${HOME}/.bashrc"  ] ; then
    # shellcheck disable=SC1090
    source "${HOME}/.bashrc"
  fi
fi

# After this point, the Base environment is configured in the new Bash shell.
# From the above code, only the following environment variables remain set:
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
# (`NEWENV_3` and `CPYENV_4`).

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
# called during deactivation.  Deactivation is not necessary when configuring
# a Base environment in a new Bash shell, but configuration scripts must be
# compatible with both `base` and `base_activate`.
#
# The deactivation callback API is only available during environment
# configuration (`NEWENV_3` and `CPYENV_4`).

# ### Function `_base_deactivation_callback_register`
#
# This function simply unsets the deactivation callback since it is not used.
#
# Arguments:
#
# * `FUNCTION` (string): function name
#
# Side effects:
#
# * The referenced function is unset.
_base_deactivation_callback_register () {
  unset -f "${1}"
}

##############################################################################
# ## Variable Management
#
# The variable management API provides a way to save initial environment
# variable values so that they can be restored during deactivation.
# Deactivation is not necessary when configuring a Base environment in a new
# Bash shell, but configuration scripts must be compatible with both `base`
# and `base_activate`.
#
# The variable management API is only available during environment
# configuration (`NEWENV_3` and `CPYENV_4`).

# ### Function `_base_var_save`
#
# This function saves an environment variable before it is modified.
#
# Since deactivation is not needed in a new Bash shell, this function does
# nothing.
#
# Arguments:
#
# * `VARIABLE` (string): global variable name
_base_var_save () {
  return 0
}

# ### Function `_base_var_set`
#
# This function sets an environment variable after saving an initial value.
#
# Since deactivation is not needed in a new Bash shell, this function just
# sets the environment variable.
#
# Arguments:
#
# * `VARIABLE` (string): global variable name
# * `VALUE` (string): value to set
#
# Side effects:
#
# * The environment variable specified by `VARIABLE` is set to `VALUE`.
_base_var_set () {
  eval "${1}=\${2}"
}

# ### Function `_base_var_unset`
#
# This function unsets an environment variable after saving an initial value.
#
# Since deactivation is not needed in a new Bash shell, this function just
# unsets the environment variable.
#
# Arguments:
#
# * `VARIABLE` (string): global variable name
#
# Side effects:
#
# * The environment variable specified by `VARIABLE` is unset.
_base_var_unset () {
  unset "${1}"
}

##############################################################################
# ## Label Management
#
# The label management API provides a way to set the Base label.
#
# The label management API is only available during environment configuration
# (`NEWENV_3` and `CPYENV_4`).

# ### Function `_base_label_set`
#
# This function sets the Base label.
#
# Arguments:
#
# * `LABEL` (string): new Base label
#
# Side effects:
#
# * Environment variable `BASE_LABEL` is set to `LABEL`.
_base_label_set () {
  BASE_LABEL="${1}"
}

# ### Function `_base_label_set_default`
#
# This function sets the Base label if one was not specified on the
# command-line.
#
# Arguments:
#
# * `LABEL` (string): default Base label
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
# configuration (`NEWENV_3` and `CPYENV_4`).

# ### Function `_base_select`
#
# This function prompts the user to select an option.
#
# An indexed list of options is displayed, and the user selects an option by
# index.  An invalid selection results in the default: the first option.  The
# selected option value (not index) is stored in the `BASE_SELECTION`
# environment variable.
#
# If only one option is passed, it is selected without prompting the user.  If
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
  if [[ "${idx}" =~ ^[0-9]+$ && \
      "${idx}" -gt "0" && "${idx}" -lt "${len}" ]] ; then
    BASE_SELECTION="${args[${idx}]}"
    return 0
  fi

  # shellcheck disable=SC2034
  BASE_SELECTION="${array[0]}"
  return 0
}

# ### Function `_base_select_dir`
#
# This function prompts the user to select a directory.
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
# This section configures a Base environment.

# ### Base Directory
#
# The full path of the Base directory is stored in the `BASE` environment
# variable.
BASE="${PWD}"

# ### Base Label
#
# If the Base label was not specified using a CLI argument, then it defaults
# to the basename of the Base directory.
#
# Note that the Base label can be changed in user configuration through the
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

# ### Configure Prompt
#
# The `PROMPT_COMMAND` environment variable is set to `_base_ps_update`.
PROMPT_COMMAND="_base_ps_update"

# To execute another function each time the prompt is displayed, add the
# function to `PROMPT_COMMAND`.  For example, the following can be used to
# also run function `foo`:
#
#     PROMPT_COMMAND="foo;_base_ps_update"

# ### Function `bcd`
#
# This function changes to a directory relative to the Base directory.
#
# This function is called directly from the command line.
#
# Arguments:
#
# * `DIR` (string): directory relative to the Base directory (optional)
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
# This function deactivates a Base environment.
#
# When using a new Bash shell, deactivation is done by exiting the shell.
# This can be done using the `exit` command or by calling this function.
#
# Side effects:
#
# * The shell is exited.
base_deactivate () {
  exit 0
}

##############################################################################
# ## User Configuration
#
# Configuration scripts in the Base directory are sourced to load any user
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
unset -f _base_lib_array_contains _base_lib_array_append _base_lib_set_insert
unset BASE_LABEL_CLI BASE_SELECTION

# The cache of commands is reset to ensure that any new `PATH` settings are
# used.
hash -r

# When the user uses the interactive shell (`NEWENV_4` and `CPYENV_5`), the
# following environment variables remain set:
#
# * `BASE_VERSION` is the software version.
# * `BASE_MODE` is set to one of the following values:
#     * `NEWENV` when this script is executed normally
#     * `CPYENV` when this script is sourced
#     * (`CURENV` when `base_activate` is sourced)
# * `BASE` is the Base directory path.
# * `BASE_LABEL` is the Base label.
#
# The following functions remain set:
#
# * `_base_ps_update` updates the prompt.
# * `bcd` is used by the user.
# * `_base_bcd_complete` handle `bcd` completion.
# * `base_deactivate` is used by the user.
