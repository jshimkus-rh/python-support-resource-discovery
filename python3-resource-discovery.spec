%define repo_name resource-discovery
%define repo_branch main

%define name python3-%{repo_name}
%define version 1.0.6
%define unmangled_version 1.0.6
%define release 1

Summary: %{name}
Name: %{name}
Version: %{version}
Release: %{release}
URL: https://gitlab.cee.redhat.com/vdo/open-sourcing/python/support/%{repo_name}
Source0: %{url}/-/archive/%{repo_branch}/%{repo_name}-%{repo_branch}.tar.gz
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
%setup -n %{repo_name}-%{repo_branch}

%build
python3 setup.py build

%install
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)

%changelog
* Tue Jul 26 2022 Joe Shimkus <jshimkush@redhat.com> - 1.0.6-1
- Make functional rpm for RHEL earlier than 9.0.
