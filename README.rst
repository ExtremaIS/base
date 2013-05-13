base - base directory environment
=================================

**base** creates an environment with a base directory.  Execute **base** from
the base directory using "." at the beginning, so that it is executed within
your current environment, as follows::

  $ . base [label]

If you do not use the "." then the command will have no (lasting) effect.  The
*label* can be used to identify the environment.  If you do not specify one,
then the name of the base directory is used.

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

**base** adds two functions to your environment: `bcd` and `base_deactivate`.

The `bcd` function changes to directories relative to the base directory.
Similar to how the `cd` command changes to your HOME directory when no
arguments are given, `bcd` changes to your base directory when no arguments
are given.  Use the tab key to use auto-completion relative to the base
directory.

The `base_deactivate` function removes the effects of this script and restores
previous settings.  Note that nested base environments are not supported.

Scripts named `.base.activate.sh` and `.base.deactivate.sh` in the base
directory are sourced automatically when base is activated/deactivated, if
they exist.

Requirements
------------

**base** requires a BASH shell.

Installation
------------

**base** can be installed using the following command::

  $ sudo make install

By default, `make install` installs within `/usr/local`.  You can specify a
different destination directory by setting the `prefix` as in the following
example::

  $ sudo make prefix=/some/dir install

Availability
------------

This software is being pre-released on GitHub before the launch of the Yuzu
Technology website:

https://github.com/yuzutechnology/base

Author
------

Travis Cardwell <travis.cardwell@yuzutechnology.com>

Reporting Bugs
--------------

Please post bugs and feature requests to GitHub:

https://github.com/yuzutechnology/base/issues

If you do not have a GitHub account, feel free to write email to
<bugs@yuzutechnology.com>.  General feedback is also welcome.

Copyright
---------

Copyright (c) 2011-2013, Yuzu Technology, Inc.

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
