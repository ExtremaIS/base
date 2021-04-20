#!/usr/bin/env bash

set -o errexit
set -o nounset
#set -o xtrace

##############################################################################
# constants

term_bold="### "
term_reset=" ###"

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

test -n "${RPMFULLNAME}" || die "RPMFULLNAME not set"
test -n "${RPMEMAIL}" || die "RPMEMAIL not set"

[ -d "/host" ] || die "/host not mounted"
[ -f "/host/${base_source}" ] || die "source not found: ${base_source}"

##############################################################################
# main

section "Configuring OS"
dnf install -y make rpm-build rpm-devel rpmdevtools rpmlint

section "Configuring user"
# shellcheck disable=SC2012
host_uid=$(ls -lnd "/host" | awk '{print $3}')
# shellcheck disable=SC2012
host_gid=$(ls -lnd "/host" | awk '{print $4}')
echo "Adding user docker:docker (${host_uid}:${host_gid})..."
groupadd --gid "${host_gid}" docker
useradd --uid "${host_uid}" --gid "${host_gid}" --create-home docker

section "Building .rpm"
sudo -u docker rpmdev-setuptree
sudo -u docker cp "/host/${base_source}" "/home/docker/rpmbuild/SOURCES/"
cd "/tmp"
tar -Jxf "/host/${base_source}" "${base_dir}/dist/rpm/base.spec"
sed \
  -e "s/{{VERSION}}/${base_version}/g" \
  -e "s/{{DATE}}/$(env LC_ALL=C date '+%a %b %d %Y')/" \
  -e "s/{{RPMFULLNAME}}/${RPMFULLNAME}/" \
  -e "s/{{RPMEMAIL}}/${RPMEMAIL}/" \
  "${base_dir}/dist/rpm/base.spec" \
  > "base.spec"
sudo -u docker rpmbuild -bs base.spec
sudo -u docker rpmbuild --rebuild "/home/docker/rpmbuild/SRPMS/"*".src.rpm"
sudo -u docker cp "/home/docker/rpmbuild/SRPMS/"*".src.rpm" "/host"
sudo -u docker cp "/home/docker/rpmbuild/RPMS/noarch/"*".rpm" "/host"
