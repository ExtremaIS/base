# Base Changelog

From version 2.0.0, this project uses [Semantic Versioning][SemVer], with
versions in `A.B.C` format.

[SemVer]: <https://semver.org/>

The format of this changelog is based on [Keep a Changelog][KaC], with the
following conventions:

* Level-two headings specify the release in `A.B.C (YYYY-MM-DD)` format, with
  newer versions above older versions.
* Level-two heading `Unreleased` is used to track changes that have not been
  released.
* Level-three headings are used to categorize changes as follows:
    1. Breaking
    2. Non-Breaking
* Changes are listed in arbitrary order and present tense.

[KaC]: <https://keepachangelog.com/en/1.0.0/>

## 2.0.1 (2022-02-28)

### Non-Breaking

* Use `docker-pkg` scripts to build packages

## 2.0.0 (2021-04-20)

### Breaking

* Rewrite `base.sh`, separating `base_deactivate.sh`
* Rewrite `share` scripts
* Add automated tests

## 1.1.2 (2014-03-11)

* `share/haskell.sh`: insert `$HOME/.cabal/bin` into `$PATH`

## 1.1.1 (2014-03-04)

* `share/go.sh`: add `~/.gows` support
* `base.sh`: update variable syntax for consistency

## 1.1.0 (2014-02-28)

* `base.sh`: switch to `.base` customization using callbacks
* `base.sh`: add `BASE_NO_TITLE` support
* `base.sh`: add `_base_select` utility function
* `share/python.sh`: initial release
* `share/go.sh`: initial release
* `share/haskell.sh`: initial release
* `test/*`: add test notes

## 1.0.2 (2013-06-03)

* `base.sh`: cleaned argument error handling
* `base.sh`: cleaned `--help` option
* `base.sh`: added `--version` option
* `base.sh`: use `basename` for automatic base label

## 1.0.1 (2013-05-13)

* `base.sh`: fixed prefix bugs where base/home directory names are prefixes of
  other directory names
* `base.sh`: added `.base.activate.sh` and `.base.deactivate.sh` script
  sourcing

## 1.0.0 (2011-07-17)

* Initial public release
