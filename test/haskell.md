Testing: share/haskell.sh
=========================

(setup)
-------

Run:

    $ mkdir -p ~/tmp/basetest
    $ cd ~/tmp/basetest
    $ ln -s /usr/local/share/base/haskell.sh .base

Prepare two versions of Haskell in `/usr/local/opt`:

* `/usr/local/opt/ghc-7.4.2-2012.4.0.0`
* `/usr/local/opt/ghc-7.6.3-2013.2.0.0`

no /usr/local/opt
-----------------

Run:

    $ sudo mv /usr/local/opt /usr/local/_opt
    $ . base

Expect:

* stderr: `warning: /usr/local/opt not found`
* prompt: `[basetest] $`
* title: `[basetest]`

Run:

    $ base_deactivate
    $ sudo mv /usr/local/_opt /usr/local/opt

no installations
----------------

Run:

    $ sudo mv /usr/local/opt/ghc-7.4.2-2012.4.0.0 /usr/local/opt/_ghc-7.4.2-2012.4.0.0
    $ sudo mv /usr/local/opt/ghc-7.6.3-2013.2.0.0 /usr/local/opt/_ghc-7.6.3-2013.2.0.0
    $ . base

Expect:

* stderr: `warning: no Haskell installations found`
* prompt: `[basetest] $`
* title: `[basetest]`

Run:

    $ base_deactivate

one installation
----------------

Run:

    $ sudo mv /usr/local/opt/_ghc-7.4.2-2012.4.0.0 /usr/local/opt/ghc-7.4.2-2012.4.0.0
    $ . base

Expect:

* stdout: `The Glorious Glasgow Haskell Compilation System, version 7.4.2`
* prompt: `[basetest] $`
* title: `[basetest]`
* `echo $PATH`: `/usr/local/opt/ghc-7.4.2-2012.4.0.0/bin:...`

Run:

    $ base_deactivate

Expect:

* `echo $PATH`: (normal)

Run:

    $ sudo mv /usr/local/opt/_ghc-7.6.3-2013.2.0.0 /usr/local/opt/ghc-7.6.3-2013.2.0.0

two installations
-----------------

Run:

    $ . base

Expect:

* select menu: starting at 1, latest first
    * `1) /usr/local/opt/ghc-7.6.3-2013.2.0.0`
    * `2) /usr/local/opt/ghc-7.4.2-2012.4.0.0`
    * `Select Haskell installation [1]: `

Select: `\n` (default)

Expect:

* stdout: `The Glorious Glasgow Haskell Compilation System, version 7.6.3`

Run:

    $ base_deactivate
    $ . base

Select: `1`

Expect:

* stdout: `The Glorious Glasgow Haskell Compilation System, version 7.6.3`

Run:

    $ base_deactivate
    $ . base

Select: `2`

Expect:

* stdout: `The Glorious Glasgow Haskell Compilation System, version 7.4.2`

Run:

    $ base_deactivate
    $ . base

Select: `3` (out of range results in default)

Expect:

* stdout: `The Glorious Glasgow Haskell Compilation System, version 7.6.3`

Run:

    $ base_deactivate
    $ . base

Select: `a` (invalid results in default)

Expect:

* stdout: `The Glorious Glasgow Haskell Compilation System, version 7.6.3`

Run:

    $ base_deactivate
    $ . base

Select: `0` (special case 0 results in default)

Expect:

* stdout: `The Glorious Glasgow Haskell Compilation System, version 7.6.3`

Run:

    $ base_deactivate

.haskell
--------

Run:

    $ ln -s /usr/local/opt/ghc-7.6.3-2013.2.0.0 .haskell
    $ . base

Expect:

* no select menu
* stdout: `The Glorious Glasgow Haskell Compilation System, version 7.6.3`

Run:

    $ base_deactivate
    $ rm .haskell

.cabal-sandbox/bin
------------------

Run:

    $ mkdir -p .cabal-sandbox/bin
    $ . base

Select: `\n` (default)

Expect:

* stdout: `The Glorious Glasgow Haskell Compilation System, version 7.6.3`
* `echo $PATH`: `~/tmp/basetest/.cabal-sandbox/bin:/usr/local/opt/ghc-7.6.3-2013.2.0.0/bin:...`

Run:

    $ base_deactivate
    $ rm -rf .cabal-sandbox

(cleanup)
---------

Run:

    $ cd
    $ rm -rf ~/tmp/basetest
