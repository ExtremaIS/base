Name:       base
Version:    1.1.2
Release:    1%{?dist}
Summary:    base directory environment
License:    MIT
URL:        http://www.extellisys.com/products/base
Source:     http://www.extellisys.com/static/products/base-1.1.2.tar.gz
BuildArch:  noarch
Requires:   bash,sed,findutils

%description
base creates an environment with a base directory.  The environment has a
clean prompt and terminal title, and it provides a command for changing
directories relative to the base directory.  Scripts can be written to
customize each base environment.

%prep
%setup -q

%build

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot} prefix=/usr

%clean
rm -rf %{buildroot}

%files
%{_bindir}/base
%{_datadir}/%{name}/
%{_defaultdocdir}/%{name}/
%{_mandir}/man1/

%changelog
* Tue Mar 11 2014 Travis Cardwell <travis.cardwell@extellisys.com> 1.1.2-1
- Initial version of the package
