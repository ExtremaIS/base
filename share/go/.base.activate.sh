#!/bin/bash
##############################################################################
# base - base directory environment
#   Go activation script
# URL: http://www.extellisys.com/products/base
##############################################################################
#
# This is a `base` activation script for Go projects.  To use it, create soft-
# links to this activation script and the accompanying deactivation script as
# follows:
#
#     $ cd ~/projects/_go_/src/github.com/GITHUBNAME/example
#     $ ln -s /usr/local/share/base/go/.base.activate.sh
#     $ ln -s /usr/local/share/base/go/.base.deactivate.sh
#
# Activate the base with `. base [label]` and deactivate the base with
# `base_deactivate` as usual.
#
# This script automatically sets the GOROOT and GOPATH environment variables
# when the base is activated, if they are not already set.  It expects Go
# installations to be in /usr/local/opt in directories named "go-VERSION".  If
# more than one Go installation is available, the script will prompt you to
# select an installation to use.  Enter a selection by number, or just press
# enter to accept the default.  Create a soft-link called ".go" to a specific
# version to use it automatically, without prompting.  If there is only one
# version available, it is used without prompting.  The script expects to be
# run from within a Go workspace, as in the example above.
#
# If there is a Go dependencies workspace in a directory named `depsws` under
# the base directory, then it is used.
#
##############################################################################

if [ -z "$GOROOT" ] ; then
	if [ -h ".go" ] ; then
		export GOROOT=$(readlink ".go")
	elif [ -d "/usr/local/opt" ] ; then
		groots=( $(ls -d /usr/local/opt/go-* | sort -rV) )
		groots_len=${#groots[*]}
		groots_sel=0
		groots_i=0
		if [ "$groots_len" -gt "0" ] ; then
			if [ "$groots_len" -gt "1" ] ; then
				while [ "$groots_i" -lt "$groots_len" ] ; do
					echo "$groots_i) ${groots[$groots_i]}"
					let "groots_i = $groots_i + 1"
				done
				read -p "Select Go installation [0]: " groots_i
				if [ "$groots_i" != "" -a "${groots[$groots_i]+exists}" ] ; then
					groots_sel="$groots_i"
				fi
			fi
			export GOROOT="${groots[$groots_sel]}"
		else
			echo "warning: no Go installations found; unable to set GOROOT" >&2
		fi
		unset groots groots_len groots_sel groots_i
	else
		echo "warning: /usr/local/opt not found; unable to set GOROOT" >&2
	fi
fi

if [ -z "$GOPATH" ] ; then
	GOPATH="$PWD"
	while [ 1 ] ; do
		if [ "$GOPATH" == "/" ] ; then
			echo "warning: not in Go workspace; unable to set GOPATH" >&2
			unset GOPATH
			break
		elif [ $(basename "$GOPATH") == "src" ] ; then
			GOPATH=$(dirname "$GOPATH")
			break
		else
			GOPATH=$(dirname "$GOPATH")
		fi
	done
fi

PATH_ORIG="$PATH"
if [ -n "$GOROOT" ] ; then
	export PATH="$GOROOT/bin:$PATH"
fi
if [ -d "$PWD/depsws/bin" ] ; then
	export PATH="$PWD/depsws/bin:$PATH"
fi
if [ -n "$GOPATH" ] ; then
	export PATH="$GOPATH/bin:$PATH"
	if [ -d "$PWD/depsws" ] ; then
		GOPATH="$PWD/depsws:$GOPATH"
	fi
	export GOPATH
fi
go version
