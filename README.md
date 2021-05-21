# Base

[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

Base configures Bash shell environments relative to a directory.  It
provides an easy and consistent way to load the configuration for diverse
projects.

* [Overview](#overview)
* [Installation](#installation)
    * [Installation From Source](#installation-from-source)
* [Usage](#usage)
    * [Example Usage](#example-usage)
* [Alternative Software](#alternative-software)
    * [Explicit Configuration](#explicit-configuration)
    * [Automatic Configuration](#automatic-configuration)
* [Project](#project)
    * [Links](#links)
    * [Releases](#releases)
    * [Contribution](#contribution)
    * [License](#license)

## Overview

Base is intended to be used for command-line-based software development.  It
provides the following benefits:

* The same commands are used to activate and deactivate environments for all
  projects.  Simply store the Base environment configuration for a project in
  the project directory.
* Configure projects quickly by sharing Base environment configuration files.
  While you can write a custom file when needed, using an existing file is as
  simple as creating a symbolic link, and using multiple existing files is as
  simple as creating multiple symbolic links.
* It is easy to keep track of the current environment because Base
  environments are activated and deactivated explicitly, not automatically
  when changing directories.  When a Base environment is activated, you can
  change to any directory and continue to use the environment.
* The Base prompt is minimal, resulting in less unnecessary text in the
  terminal.  This makes the terminal easier to read, and it also makes logs
  easier to read when copying from the terminal to a project ticket or email.
* The terminal title mirrors the Base prompt, making it very easy to navigate
  tabbed terminals.
* Quickly navigate within the Base directory using the `bcd` command, which
  supports auto-completion.

## Installation

Base only runs in the Bash shell.  It has only been tested on Linux.

### Installation From Source

Get the latest release as follows:

```
$ git clone https://github.com/ExtremaIS/base.git
$ cd base
```

To install everything (scripts, sample Base scripts, manual, documentation)
to `/usr/local`, run the following

```
$ sudo make install
```

Alternatively, run the following to install only the scripts to `${HOME}/bin`:

```
$ make install-bin PREFIX="${HOME}"
```

## Usage

See the [manual](doc/base.1.md) (`man base` after installation) for usage
information.

### Example Usage

The following example demonstrates the Base prompt (and title):

```
username@localhost:~$ cd projects/public/example
username@localhost:~/projects/public/example$ base
[example] $ cd src
[example] src$ bcd test
[example] test$ cd
(example) ~$ cd /etc
(example) /etc$ exit
username@localhost:~/projects/public/example$
```

The `base` command configures the environment in a new Bash shell.  You can
use `exit` to exit the shell as usual.  Note that Base can alternatively be
used in two other ways.  By running `. base`, the current environment is
copied to the new Bash shell.  By running `. base_acivate`, the Base
environment is configured in the current shell.  In this case, running
`base_deactivate` deactivates the Base environment.

The Base label, which defaults to the name of the Base directory but can be
configured via the CLI or configuration file, is displayed in brackets
(`[example]`) when within the Base directory.  It is displayed in parentheses
(`(example)`) when outside the Base directory.

The following example demonstrates configuration of a project with a Python
virtual environment:

```
username@localhost:~$ mkdir -p projects/public/example
username@localhost:~$ cd projects/public/example
username@localhost:~/projects/public/example$ /usr/local/opt/python-3.9.4/bin/python -m venv virtualenv-3.9.4
username@localhost:~/projects/public/example$ ln -s /usr/share/base/python-virtualenv.sh .base
username@localhost:~/projects/public/example$ base
Python 3.9.4
[example] $ exit
username@localhost:~/projects/public/example$ /usr/local/opt/python-3.8.9/bin/python -m venv virtualenv-3.8.9
username@localhost:~/projects/public/example$ base
1) virtualenv-3.9.4
2) virtualenv-3.8.9
Select Python virtual environment [1]: 2
Python 3.8.9
[example] $
```

Base provides an easy way to prompt users to select environment options.  The
`python-virtualenv.sh` script prompts the user to select a virtual environment
when more than one is configured.

## Alternative Software

### Explicit Configuration

The [Environment Modules](https://github.com/cea-hpc/modules) software allows
you to modularize environment configuration, supporting multiple versions per
module.  Specific module versions are loaded and unloaded explicitly.  It
supports many shells.

### Automatic Configuration

There are many software projects that configure shell environments relative to
a directory by automatically executing scripts when changing directories.
Here are some of the most popular ones:

* [direnv](https://direnv.net/) - Shell scripts in the current and parent
  directories that are explicitly authorized are sourced.  It supports many
  shells.
* [autoenv](https://github.com/inishchith/autoenv) - Shell scripts in the
  current and parent directories are sourced.  It supports many shells.
* [OnDir](https://github.com/alecthomas/ondir) - Shell scripts are saved in a
  common configuration file in your `${HOME}` directory.  It supports a number
  of shells.
* [Shadowenv](https://shopify.github.io/shadowenv/) - Shadowlisp scripts in
  the first configuration directory found in the current and parent
  directories that is explicitly authorized are run.  It supports a number of
  shells.

## Project

### Links

* GitHub: <https://github.com/ExtremaIS/base>

### Releases

All releases are tagged in the `main` branch.  Release tags are signed using
the
[`security@extrema.is` GPG key](http://keys.gnupg.net/pks/lookup?op=vindex&fingerprint=on&search=0x1D484E4B4705FADF).

### Contribution

Issues and feature requests are tracked on GitHub:
<https://github.com/ExtremaIS/base/issues>

Issues may also be submitted via email to <bugs@extrema.is>.

### License

This project is released under the
[MIT License](https://opensource.org/licenses/MIT) as specified in the
[`LICENSE`](LICENSE) file.
