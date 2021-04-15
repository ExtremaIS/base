---
title: BASE
section: 1
hyphenate: false
...

# NAME

`base` - configure Bash shell environments relative to a directory

# SYNOPSIS

`base` [*label*]
:   run in a new Bash shell

`. base` [*label*]
:   copy env and run in a new Bash shell

`. base_activate` [*label*]
:   run in the current Bash shell

# DESCRIPTION

Base configures Bash shell environments relative to a directory.  It provides
an easy and consistent way to load the configuration for diverse projects.

# OPTIONS

\--help
:   show usage information and exit

\--version
:   show version information and exit

# ARGUMENTS

*label*
:   base environment label to use in the prompt and title

# Usage

Change to the directory that you would like to use as the "base directory" and
run base in one of the three following ways:

`base` [*label*]
:   When you run `base` normally, the base environment is configured in a new
    Bash shell.  Only environment variables that are exported in the parent
    shell are propagated.  `${HOME}/.bashrc` is sourced if it exists.

`. base` [*label*]
:   When you source `base`, the base enviornment is configured in a new Bash
    shell, but all environment variables and aliases from the parent shell are
    propagated.

`. base_activate` [*label*]
:   When you source `base_activate`, the base environment is configured in the
    current Bash shell.  Note that this method cannot be used to create a
    nested base environment.

The base label, displayed in the prompt and title, may be configured in the
following ways:

* It can be set in a configuration script.  (See CONFIGURATION below.)
* It can be set via the CLI using the *label* argument.
* The default value is the base directory name.

When a base environment is configured, the following two commands are
available:

`bcd` [*directory*]
:   This command changes to a directory relative to the base directory.  When
    no arguments are provided, it changes to the base directory.  Use tab
    completion for quick navigation.

`base_deactivate`
:   This command deactivates the base environment.  When using a base
    environment configured using `base_activate`, it restores the previous
    configuration.  When using a base environment configured in a new shell
    using `base`, it exits the new shell.  (In this case, `exit` may also be
    used.)

# PROMPT

The base prompt indicates your location in relation to the base directory.
When under the base directory, the label is displayed in brackets.  When
outside the base directory, the label is displayed in parentheses.

The following example prompts are for a base environment configured with a
base directory of `/home/user/proj`:

`[proj] $`
:   In the base directory (`/home/user/proj`)

`[proj] src$`
:   In the `src` directory under the base directory (`/home/user/proj/src`)

`(proj) ~$`
:   In the `${HOME}` directory, outside the base directory (`/home/user`)

`(proj) ~/tmp$`
:   In the `${HOME}/tmp` directory, outside the base directory
    (`/home/user/tmp`)

`(proj) /etc`
:   In the `/etc` directory, outside the base directory

`[proj] #`
:   A `#` prompt is used when `root`

# TITLE

The terminal title is updated with your location in relation to the base
directory, using the same syntax as the prompt.

To disable this feature, set the `BASE_NO_TITLE` environment variable.

# CONFIGURATION

A base environment is configured using one or more Bash scripts stored in
`.base` in the base directory.  `.base` can be a file, a link to a shared
script, or a directory containing any number of files, links, and directories.
The file(s)/link(s) are sourced (in sorted order) during base environment
configuration.  Configuration should support deactivation by using the
functions below.

Scripts that are included with base can be found in `/usr/share/base`.

The following environment variables are available:

`BASE_VERSION`
:   This variable is set to the base version.

`BASE_MODE`
:   This variable indicates the way that the base environment is being
    configured:

    * `NEWENV`: new shell (`base`)
    * `CPYENV`: new shell with copied environment (`. base`)
    * `CURENV`: current shell (`. base_activate`)

`BASE`
:   This variable is set to the base directory.

`BASE_LABEL`
:   This variable is set to the base label.

The following functions are available:

`_base_lib_array_contains` *array_name* *value*
:   This function checks if a global array contains a specific value.  It
    returns `0` if the value is found in the array or `1` otherwise.

`_base_lib_array_append` *array_name* *value*
:   This function appends a value to a global array.

`_base_lib_set_insert` *array_name* *value*
:   This function appends a value to a global array if the value is not
    already in the array.

`_base_var_save` *variable_name*
:   When configuring a base environment in the current shell, this function
    stores the current value of an environment variable so that it will be
    restored when the base environment is deactivated.

`_base_var_set` *variable_name* *value*
:   This function sets an environment variable.  When configuring a base
    environment in the current shell, it stores the previous value so that it
    will be restored when the base environment is deactivated.

`_base_var_unset` *variable_name*
:   This function unsets an environment variable.  When configuring a base
    environment in the current shell, it stores the previous value so that it
    will be restored when the base environment is deactivated.

`_base_label_set` *label*
:   This function sets the base label, taking precedence over CLI arguments.

`_base_label_set_default` *label*
:   This function sets the base label if one was not specified via a CLI
    argument.

`_base_deactivation_callback_register` *function_name*
:   This registers a function to be evaluated during deactivation.  When
    using a new Bash shell, deactivation is not neccesary, so the referenced
    function is unset.

`_base_select` *label* *option* `...`
:   This function prompts the user to select an option.  An indexed list of
    options is displayed, and the user selects an option by index.  An invalid
    selection results in the default: the first option.  The selected option
    value (not the index) is stored in the `BASE_SELECTION` environment
    variable.

    If only one option is passed, it is selected without prompting the user.
    If no options are passed, a warning is displayed and `BASE_SELECTION` is
    unset.  This function returns `0` when `BASE_SELECTION` is set or `1`
    otherwise.

`_base_select_dir` *label* *parent_directory* *glob*
:   This function prompts the user to select a directory that matches the
    specified glob (example: `virtualenv-*`).

Note that base configures `PROMPT_COMMAND` to use the `_base_ps_update`
function to update the prompt.  To configure another command to run at every
prompt, prefix it to `PROMPT_COMMAND` as follows:

    PROMPT_COMMAND="foo;${PROMPT_COMMAND}"

# PROJECT

GitHub:
:   <https://github.com/ExtremaIS/base>

Reporting issues:
:   GitHub: <https://github.com/ExtremaIS/base/issues>

    Email: <bugs@extrema.is>

Copyright:
:   Copyright (c) 2011-2021 Travis Cardwell

License:
:   The MIT License <https://opensource.org/licenses/MIT>
