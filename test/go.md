Testing: share/go.sh
====================

(setup)
-------

Run:

    $ mkdir -p ~/tmp/basetest
    $ cd ~/tmp/basetest
    $ mkdir -p bin pkg src/github.com/uname/project

Prepare two versions of Go in `/usr/local/opt`:

* `/usr/local/opt/go-1.1-rc3`
* `/usr/local/opt/go-1.2`

no /usr/local/opt
-----------------

Run:

    $ cd ~/tmp/basetest/src/github.com/uname/project
    $ ln -s /usr/local/share/base/go.sh .base
    $ sudo mv /usr/local/opt /usr/local/_opt
    $ . base

Expect:

* stderr: `warning: /usr/local/opt not found`
* stderr: `warning: unable to set GOROOT`
* stderr: `bash: go: command not found`
* prompt: `[project] $`
* title: `[project]`

Run:

    $ base_deactivate
    $ sudo mv /usr/local/_opt /usr/local/opt

one installation
----------------

Run:

    $ sudo mv /usr/local/opt/go-1.1-rc3 /usr/local/opt/_go-1.1-rc3
    $ . base

Expect:

* stdout: `go version go1.2 linux/amd64`
* prompt: `[project] $`
* title: `[project]`
* `echo $GOROOT`: `/usr/local/opt/go-1.2`
* `echo $GOPATH`: `/home/tcard/tmp/basetest`
* `echo $PATH`: `~/tmp/basetest/bin:/usr/local/opt/go-1.2/bin:...`

Run:

    $ base_deactivate

Expect:

* `echo $GOROOT`: (not set)
* `echo $GOPATH`: (not set)
* `echo $PATH`: (normal)

Run:

    $ sudo mv /usr/local/opt/_go-1.1-rc3 /usr/local/opt/go-1.1-rc3

two installations
-----------------

Run:

    $ . base

Expect:

* select menu: starting at 1, latest first
    * `1) /usr/local/opt/go-1.2`
    * `2) /usr/local/opt/go-1.1-rc3`
    * `Select Go installation [1]: `

Select: `\n` (default)

Expect:

* stdout: `go version go1.2 linux/amd64`

Run:

    $ base_deactivate
    $ . base

Select: `1`

Expect:

* stdout: `go version go1.2 linux/amd64`

Run:

    $ base_deactivate
    $ . base

Select: `2`

Expect:

* stdout: `go version go1.1rc3 linux/amd64`

Run:

    $ base_deactivate
    $ . base

Select: `3` (out of range results in default)

Expect:

* stdout: `go version go1.2 linux/amd64`

Run:

    $ base_deactivate
    $ . base

Select: `a` (invalid results in default)

Expect:

* stdout: `go version go1.2 linux/amd64`

Run:

    $ base_deactivate
    $ . base

Select: `0` (special case 0 results in default)

Expect:

* stdout: `go version go1.2 linux/amd64`

Run:

    $ base_deactivate

.go
---

Run:

    $ ln -s /usr/local/opt/go-1.1-rc3 .go
    $ . base

Expect:

* no select menu
* stdout: `go version go1.1rc3 linux/amd64`

Run:

    $ base_deactivate
    $ rm .go

depsws
------

Run:

    $ mkdir -p depsws/{bin,pkg,src}
    $ . base

Select: `\n` (default)

Expect:

* stdout: `go version go1.2 linux/amd64`
* `echo $GOPATH`: `~/tmp/basetest/src/github.com/uname/project/depsws:~/tmp/basetest`
* `echo $PATH`: `~/tmp/basetest/bin:~/tmp/basetest/src/github.com/uname/project/depsws/bin:/usr/local/opt/go-1.2/bin:...`

Run:

    $ base_deactivate
    $ rm -rf depsws

presets
-------

Run:

    $ export GOROOT=/usr/local/opt/go-1.2
    $ export GOPATH=/tmp
    $ . base

Expect:

* stdout: `go version go1.2 linux/amd64`
* `echo $GOROOT`: `/usr/local/opt/go-1.2`
* `echo $GOPATH`: `/tmp`
* `echo $PATH`: `/tmp/bin:/usr/local/opt/go-1.2/bin:...`

Run:

    $ base_deactivate

Expect:

* `echo $GOROOT`: (not set)
* `echo $GOPATH`: (not set)
* `echo $PATH`: (normal)

outside of workspace
--------------------

Run:

    $ cd ~/tmp/basetest
    $ ln -s ~/projects/base/share/go.sh .base
    $ . base

Select: `\n` (default)

Expect:

* stderr: `warning: not in a Go workspace`
* stderr: `warning: unable to set GOPATH`
* stdout: `go version go1.2 linux/amd64`

Run:

    $ base_deactivate
    $ rm .base

(cleanup)
---------

Run:

    $ cd
    $ rm -rf ~/tmp/basetest
