base - base directory environment
=================================

**base** creates an environment with a base directory.  Execute **base** from
the base directory using `.` at the beginning, so that it is executed within
your current environment, as follows::

    $ . base [label]

The *label* can be used to identify the environment.  If you do not specify
one, then the name of the base directory is used.

The prompt and title of the terminal change according to what directory you
are in.  When within the base directory, the label in brackets and the current
path within the base directory are displayed.  For example, when in the `src`
directory under a base environment labelled *app*, the prompt would be
displayed as follows::

    [app] /src$

When outside the base directory, the label in parenthesis and the current path
are displayed.  For example, when in the `/etc` directory outside of a base
environment labelled *app*, the prompt would be displayed as follows::

    (app) /etc$

If an environment variable named `BASE_NO_TITLE` exists, then the title is
not changed.  This option is intended for use in terminals that do not have
titles.

**base** adds two functions to your environment: `bcd` and `base_deactivate`.

The `bcd` function changes to directories relative to the base directory,
using the tab key for auto-completion.  Similar to how the `cd` command
changes to your HOME directory when no arguments are given, `bcd` changes to
your base directory when no arguments are given.

The `base_deactivate` function removes the effects of this script and restores
previous settings.  Note that nested base environments are not supported.

Customization
-------------

Environments can be customized by placing a script named `.base` in the base
directory.  Such scripts can define functions named `_base_activate_pre`,
`_base_activate_post`, `_base_deactivate_pre`, and/or `_base_deactivate_post`
to specify commands to be run before activation, after activation, before
deactivation, and after deactivation respectively.  If there are any side-
effects when running one of the activation callbacks, take care to undo them
in one of the deactivation callbacks.

A utility function named `_base_select`, which allows the user to make a
selection from a number of options, is available for use in all callbacks
except `_base_deactivation_post`.  The first argument is a label that
represents what is being selected, and remaining arguments are the options.
The result is stored in the variable `BASE_SELECTION`.  If no options were
available, the variable is unset.  If only one option is available, then that
option is used without prompting.  Users select an option by number, and any
invalid input results in the first option being selected.

Some example base scripts are provided in the `share` directory, with
documentation in the comments.  Use the scripts by linking to them, or copy
and modify them as needed.

Requirements
------------

**base** requires a BASH shell.

Installation
------------

**base** can be installed on Debian-based distributions using the package
manager as follows:

    $ wget http://www.extellisys.com/static/products/base_1.1.0_all.deb
    $ sudo dpkg -i base_1.1.0_all.deb

**base** can be installed on RedHat-based distributions using the package
manager as follows:

    $ wget http://www.extellisys.com/static/products/base-1.1.0-1.noarch.rpm
    $ sudo rpm -i base-1.1.0-1.noarch.rpm

**base** can be installed from source using the following command::

    $ sudo make install

By default, `make install` installs within `/usr/local`.  You can specify a
different destination directory by setting the `prefix` as in the following
example::

    $ sudo make prefix=/some/dir install

Availability
------------

* Homepage: <http://www.extellisys.com/products/base>
* Source: <https://github.com/extellisys/base>

Author
------

Travis Cardwell &lt;<travis.cardwell@extellisys.com>&gt;

Reporting Bugs
--------------

Please submit any issues to:

<https://github.com/extellisys/base/issues>

If you do not have a [GitHub](https://github.com) account, feel free to submit
issues via email to <bugs@extellisys.com>.

Copyright
---------

Copyright (c) 2011-2014, Extellisys

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
