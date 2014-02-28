Testing: share/python.sh
========================

no environments
---------------

Run:

    $ mkdir -p ~/tmp/basetest
    $ cd ~/tmp/basetest
    $ ln -s /usr/local/share/base/python.sh .base
    $ . base

Expect:

* stderr: `warning: no virtual environment loaded`
* prompt: `[basetest] $`
* title: `[basetest]`

Run:

    $ base_deactivate

one environment
---------------

Run:

    $ /usr/local/opt/python-3.3.4/bin/pyvenv virtualenv-3.3.4
    $ . base

Expect:

* stdout: `Python 3.3.4`
* prompt: `[basetest] $`
* title: `[basetest]`
* `which python`: `~/tmp/basetest/virtualenv-3.3.4/bin/python`

Run:

    $ base_deactivate

Expect:

* prompt: (normal; not virtualenv-3.3.4)
* `which python`: `/usr/bin/python`

two environments
----------------

Run:

    $ /usr/local/opt/python-2.7.6/bin/virtualenv virtualenv-2.7.6
    $ . base

Expect:

* select menu: starting at 1, latest first
    * `1) virtualenv-3.3.4`
    * `2) virtualenv-2.7.6`
    * `Select virtual environment [1]: `

Select: `\n` (default)

Expect:

* stdout: `Python 3.3.4`

Run:

    $ base_deactivate
    $ . base

Select: `1`

Expect:

* stdout: `Python 3.3.4`

Run:

    $ base_deactivate
    $ . base

Select: `2`

Expect:

* stdout: `Python 2.7.6`

Run:

    $ base_deactivate
    $ . base

Select: `3` (out of range results in default)

Expect:

* stdout: `Python 3.3.4`

Run:

    $ base_deactivate
    $ . base

Select: `a` (invalid results in default)

Expect:

* stdout: `Python 3.3.4`

Run:

    $ base_deactivate
    $ . base

Select: `0` (special case 0 results in default)

Expect:

* stdout: `Python 3.3.4`

Run:

    $ base_deactivate

virtualenv
----------

Run:

    $ ln -s virtualenv-2.7.6 virtualenv
    $ . base

Expect:

* no select menu
* stdout: `Python 2.7.6`

Run:

    $ base_deactivate
    $ rm virtualenv

(cleanup)
---------

Run:

    $ cd
    $ rm -rf ~/tmp/basetest
