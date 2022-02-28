Name:          base
Version:       {{VERSION}}
Release:       1%{?dist}
Summary:       Configure Bash shell environments relative to a directory
License:       MIT
URL:           https://github.com/ExtremaIS/base
Source0:       base-{{VERSION}}.tar.xz
BuildArch:     noarch
BuildRequires: bash,coreutils,gzip,make
Requires:      bash,coreutils,findutils
#ExcludeArch:

%description
Base configures Bash shell environments relative to a directory.  It provides
an easy and consistent way to load the configuration for diverse projects.

%prep
%setup -q

%build

%install
make install DESTDIR=%{buildroot} PREFIX=/usr

%check

%files
%{_bindir}/base
%{_bindir}/base_activate
%{_datadir}/%{name}/
%{_mandir}/man1/base.1.gz
%{_datadir}/doc/%{name}/

%changelog
* {{DATE}} {{RPMFULLNAME}} <{{RPMEMAIL}}> - {{VERSION}}-1
- Release {{VERSION}}
