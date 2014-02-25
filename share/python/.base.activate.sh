#!/bin/bash
##############################################################################
# base - base directory environment
#   Python activation script
# URL: http://www.extellisys.com/products/base
##############################################################################
#
# This is a `base` activation script for Python projects.  To use it, create
# soft links to this activation script and the accompanying deactivation
# script as follows:
#
#     $ cd ~/projects/example
#     $ ln -s /usr/local/share/base/python/.base.activate.sh
#     $ ln -s /usr/local/share/base/python/.base.deactivate.sh
#
# Activate the base with `. base [label]` and deactivate the base with
# `base_deactivate` as usual.
#
# This script automatically activates Python virtual environments when the
# base is activated.  It expects Python virtual environments to be setup in
# directories named "virtualenv-VERSION" in the project root.  If more than
# one virtual environment is available, then script will prompt you to select
# an environment to use.  Enter a selection by number, or just press enter to
# accept the default.  Create a soft-link called "virtualenv" to a specific
# version to make it load automatically, without prompting.  If there is only
# one virtual environment available, it is loaded without prompting.
#
##############################################################################

if [ -e "virtualenv" ] ; then
	source "virtualenv/bin/activate"
	python --version
else
	venvs=( $(ls -d virtualenv* | sort -rV) )
	venvs_len=${#venvs[*]}
	venvs_sel=0
	venvs_i=0
	if [ "$venvs_len" -gt "0" ] ; then
		if [ "$venvs_len" -gt "1" ] ; then
			while [ "$venvs_i" -lt "$venvs_len" ] ; do
				echo "$venvs_i) ${venvs[$venvs_i]}"
				let "venvs_i = $venvs_i + 1"
			done
			read -p "Select virtual environment [0]: " venvs_i
			if [ "$venvs_i" != "" -a "${venvs[$venvs_i]+exists}" ] ; then
				venvs_sel="$venvs_i"
			fi
		fi
		source "${venvs[$venvs_sel]}/bin/activate"
		python --version
	else
		echo "warning: no virtual environment loaded" >&2
	fi
	unset venvs venvs_len venvs_sel venvs_i
fi
