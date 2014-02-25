#!/bin/bash
##############################################################################
# base - base directory environment
#   Go deactivation script
# URL: http://www.extellisys.com/products/base
##############################################################################
#
# This is a `base` deactivation script for Go projects.  To use it, create
# soft-links to the accompanying activation script and this deactivation
# script as follows:
#
#     $ cd ~/projects/_go_/src/github.com/GITHUBNAME/example
#     $ ln -s /usr/local/share/base/go/.base.activate.sh
#     $ ln -s /usr/local/share/base/go/.base.deactivate.sh
#
# Activate the base with `. base [label]` and deactivate the base with
# `base_deactivate` as usual.
#
# This script automatically resets the PATH and unsets the GOROOT and GOPATH
# environment variables when the base is deactivated.
#
##############################################################################

export PATH=$PATH_ORIG
unset PATH_ORIG GOROOT GOPATH
