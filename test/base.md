Testing: base.sh
================

no source, no args
------------------

Run:

    $ base

Expect:

* stderr: usage
* exit 2

no source, args
---------------

Run:

    $ base test

Expect:

* stderr: usage
* exit 2

help
----

Run:

    $ base --help

Expect:

* stderr: usage
* exit 0

version
-------

Run:

    $ base --version

Expect:

* stdout: version
* exit 0

basic
-----

Run:

    $ mkdir -p ~/tmp/basetest/{one,two}/{three,four}
    $ cd ~/tmp/basetest
    $ . base

Expect:

* prompt: `[basetest] $`
* title: `[basetest]`

Run:

    $ cd one

Expect:

* prompt: `[basetest] /one$`
* title: `[basetest] /one`

Run:

    $ bcd t\tt\n

Expect:

* auto-completion: `two/three/`
* prompt: `[basetest] /two/three$`
* title: `[basetest] /two/three`

Run:

    $ bcd

Expect:

* prompt: `[basetest] $`
* title: `[basetest]`

Run:

    $ cd

Expect:

* prompt: `(basetest) ~$`
* title: `(basetest) ~`

Run:

    $ cd ~/tmp

Expect:

* prompt: `(basetest) ~/tmp$`
* title: `(basetest) ~/tmp`

Run:

    $ cd /var

Expect:

* prompt: `(basetest) /var$`
* title: `(basetest) /var`

Run:

    $ bcd one

Expect:

* prompt: `[basetest] /one$`
* title: `[basetest /one`

Run:

    $ base_deactivate

Expect:

* prompt: (normal)
* title: (normal)

Run:

    $ bcd

Expect:

* error: `bash: bcd: command not found`

Run:

    $ base_deactivate

Expect:

* error: `bash: base_deactivate: command not found`

label
-----

Run:

    $ cd ~/tmp/basetest
    $ . base raberu

Expect:

* prompt: `[raberu] $`
* title: `[raberu]`

Run:

    $ base_deactivate

Expect:

* prompt: (normal)
* title: (normal)

no title
--------

Run:

    $ export BASE_NO_TITLE=1
    $ . base

Expect:

* prompt: `[basetest] $`
* title: (normal)

Run:

    $ base_deactivate
    $ unset BASE_NO_TITLE

Expect:

* prompt: (normal)
* title: (normal)

(cleanup)
---------

Run:

    $ cd
    $ rm -rf ~/tmp/basetest
