%global modname resource-discovery

%define repo_name python-support-resource-discovery
%define repo_branch main

%define version 1.0.13
%define unmangled_version 1.0.13
%define release 1

Name: python3-%{modname}
Version: %{version}
Release: %{release}
Summary: python3-%{modname}
License: GPLv2
URL:     https://github.com/dm-vdo/%{repo_name}
Source0: %{url}/archive/refs/heads/%{repo_branch}.tar.gz

BuildArch: noarch

Group: Development/Libraries

# Build requirements.
%if 0%{?rhel} && 0%{?rhel} < 9
BuildRequires: python39
BuildRequires: python39-devel
BuildRequires: python39-rpm-macros
BuildRequires: python39-setuptools
BuildRequires: python39-six
BuildRequires: python39-pyyaml
%else
BuildRequires: python3
BuildRequires: python3-devel
BuildRequires: python3-eventlet
BuildRequires: python3-py
BuildRequires: python3-rpm-macros
BuildRequires: python3-setuptools
BuildRequires: python3-six
BuildRequires: python3-pyyaml
%endif

# Runtime requirements.
Requires: python3-utility-mill >= 1
%if 0%{?rhel} && 0%{?rhel} < 9
Requires: python39
Requires: python39-pyyaml
%else
Requires: python3
Requires: python3-pyyaml
%endif

%?python_enable_dependency_generator

%description
UNKNOWN

%prep
%autosetup -n %{repo_name}-%{repo_branch}

%build
%py3_build

%install
%py3_install

%files -n python3-%{modname}
%dir %{_sysconfdir}/permabit/python/support
%{_sysconfdir}/permabit/python/support/architectures-defaults.yml
%{_sysconfdir}/permabit/python/support/distributions-defaults.yml
%{_sysconfdir}/permabit/python/support/repos-defaults.yml
%{_bindir}/arches3
%{_bindir}/distros3
%{_bindir}/repos3
%{python3_sitelib}/discovery/
%{python3_sitelib}/python3_resource_discovery-%{version}*

%changelog
* Thu Jul 06 2023 Joe Shimkus <jshimkus@redhat.com> - 1.0.13-1
- Fixed handling of URI errors as input to repo filtering.

* Fri Jun 09 2023 Joe Shimkus <jshimkus@redhat.com> - 1.0.12-1
- Added an Architecture virtualization flag property.

* Tue Jun 06 2023 Joe Shimkus <jshimkus@redhat.com> - 1.0.11-1
- Changed default architecture to be that of the running machine.

* Mon Oct 24 2022 Joe Shimkus <jshimkus@redhat.com> - 1.0.10-1
- Changed package generation per Red Hat example.

* Mon Aug 08 2022 Joe Shimkus <jshimkus@redhat.com> - 1.0.9-1
- Distinguish between lack of repos and repo discovery errors.

* Fri Aug 05 2022 Joe Shimkus <jshimkus@redhat.com> - 1.0.8-1
- Re-raise exception on cache file open failure.

* Wed Aug 03 2022 Joe Shimkus <jshimkus@redhat.com> - 1.0.7-1
- Correct exclusive locking of cache files.

* Tue Jul 26 2022 Joe Shimkus <jshimkus@redhat.com> - 1.0.6-1
- Make functional rpm for RHEL earlier than 9.0.
