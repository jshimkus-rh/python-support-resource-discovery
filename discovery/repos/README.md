# Dynamic discovery of available distribution repositories.

The repositories are made available as sets defined as follows:
* `released: released distribution`
* `latest:   on the path to being released`
* `nightly:  the most recently generated distribution`

To support the tooling which consumes the result of repository discovery
the returned results are aggregated using set semantics in the following
manner:
* `released: nightly << latest << released`
* `latest:   nightly << released << latest`
* `nightly:  released << latest << nightly`

The result of this aggregation is that each set contains the discovered
repositories that most closely match the above described set definitions.


