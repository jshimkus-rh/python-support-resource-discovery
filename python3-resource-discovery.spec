%define repo_name resource-discovery
%define repo_branch main

%define name python3-%{repo_name}
%define version 1.0.9
%define unmangled_version 1.0.9
%define release 1

Summary: %{name}
Name: %{name}
Version: %{version}
Release: %{release}
URL:     https://github.com/dm-vdo/python-support-resource-discovery
Source0: %{url}/archive/refs/heads/main.tar.gz
License: GPLv2
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch

%if 0%{?rhel} && 0%{?rhel} < 9
BuildRequires: python39
BuildRequires: python39-pyyaml
BuildRequires: python39-setuptools
Requires: python39
Requires: python39-pyyaml
%else
BuildRequires: python3
BuildRequires: python3-pyyaml
BuildRequires: python3-setuptools
Requires: python3
Requires: python3-pyyaml
%endif

Requires: python3-utility-mill >= 1

%description
UNKNOWN

%prep
%setup -n python-support-resource-discovery-%{repo_branch}

%build
python3 setup.py build

%install
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)

%changelog
* Mon Aug 08 2022 Joe Shimkus <jshimkush@redhat.com> - 1.0.9-1
- Distinguish between lack of repos and repo discovery errors.

* Fri Aug 05 2022 Joe Shimkus <jshimkush@redhat.com> - 1.0.8-1
- Re-raise exception on cache file open failure.

* Wed Aug 03 2022 Joe Shimkus <jshimkush@redhat.com> - 1.0.7-1
- Correct exclusive locking of cache files.

* Tue Jul 26 2022 Joe Shimkus <jshimkush@redhat.com> - 1.0.6-1
- Make functional rpm for RHEL earlier than 9.0.
