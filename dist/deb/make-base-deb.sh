#!/usr/bin/env bash

set -o errexit
set -o nounset
#set -o xtrace

##############################################################################
# constants

term_bold="$(tput bold)"
term_reset="$(tput sgr0)"

##############################################################################
# library

die () {
  echo "error: ${*}" >&2
  exit 1
}

section () {
  echo "${term_bold}${*}${term_reset}"
}

##############################################################################
# parse arguments

if [ "$#" -ne "1" ] ; then
  echo "usage: ${0} base-VERSION.tar.xz" >&2
  exit 2
fi

base_source="${1}"
base_dir="${base_source%.tar.xz}"
[ "${base_dir}" != "${base_source}" ] \
  || die "invalid source filename: ${base_source}"
base_version="${base_dir#base-}"
[ "${base_version}" != "${base_dir}" ] \
  || die "invalid source filename: ${base_source}"

##############################################################################
# confirm environment

test -n "${DEBFULLNAME}" || die "DEBFULLNAME not set"
test -n "${DEBEMAIL}" || die "DEBEMAIL not set"

[ -d "/host" ] || die "/host not mounted"
[ -f "/host/${base_source}" ] || die "source not found: ${base_source}"

##############################################################################
# main

section "Configuring OS"
apt-get update
apt-get upgrade -y
apt-get install -y \
  debhelper \
  devscripts \
  dh-make \
  sudo

section "Configuring user"
# shellcheck disable=SC2012
host_uid=$(ls -lnd "/host" | awk '{print $3}')
# shellcheck disable=SC2012
host_gid=$(ls -lnd "/host" | awk '{print $4}')
echo "Adding user docker:docker (${host_uid}:${host_gid})..."
groupadd --gid "${host_gid}" docker
useradd --uid "${host_uid}" --gid "${host_gid}" --create-home docker

section "Building .deb"
cd "/tmp"
tar -Jxf "/host/${base_source}"
[ -d "${base_dir}" ] || die "base directory not found: ${base_dir}"
cd "${base_dir}"
dh_make --single --yes -f "/host/${base_source}"
cd "debian"
rm -rf README.* base* ./*.ex source
sed -i "s/^  \\*.*/  * Release ${base_version}/" changelog
cd ..
cp dist/deb/control debian
cp dist/deb/copyright debian
cp dist/Makefile .
dpkg-buildpackage -us -uc
cd "/tmp"
rm -rf "${base_dir}"
sudo -u docker cp base* /host
