# Release Checklist

Use this checklist when publishing a new RPM for an upstream Raspberry Pi Imager release.

## Prepare

- Confirm the upstream release tag exists at `raspberrypi/rpi-imager`.
- Update `rpi-imager.spec` with `scripts/update-version.py`.
- Review whether existing patches still apply and are still needed.
- Confirm the RPM `Release` value is correct for this packaging revision.

## Build

- Build locally on Fedora or wait for the GitHub Actions build.
- Confirm source and binary RPM artifacts were produced.
- Confirm the install smoke test passed.
- Review any dependency or file list changes.

## Publish

- Merge the update after the build passes.
- Create and push a tag using the `rpm-v<upstream-version>-<rpm-release>` format.
- Confirm the GitHub Release contains only the installable binary RPM.
- Confirm debug and source RPMs remain workflow artifacts only.

Example:

```bash
git tag rpm-v2.0.9-1
git push origin rpm-v2.0.9-1
```
