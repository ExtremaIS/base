#!/bin/bash
##############################################################################
# base - base directory environment
#   Python deactivation script
# URL: http://www.extellisys.com/products/base
##############################################################################
#
# This is a `base` deactivation script for Python projects.  To use it, create
# soft-links to the accompanying activation script and this deactivation
# script as follows:
#
#     $ cd ~/projects/example
#     $ ln -s /usr/local/share/base/python/.base.activate.sh
#     $ ln -s /usr/local/share/base/python/.base.deactivate.sh
#
# Activate the base with `. base [label]` and deactivate the base with
# `base_deactivate` as usual.
#
# This script automatically deactivates Python virtual environments when the
# base is deactivated.
#
##############################################################################

declare -F "deactivate" >/dev/null
if [ "$?" -eq "0" ] ; then
	deactivate
fi
