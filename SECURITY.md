# Security Policy

## Supported scope

This repository maintains RPM packaging files, helper scripts, patches, and GitHub Actions workflows for Raspberry Pi Imager.

Security issues in this repository include problems such as:

- Unsafe packaging scripts or workflows.
- Incorrect file permissions in the RPM package.
- Packaging changes that introduce unintended executable content.
- Release artifact publishing problems.

Security issues in Raspberry Pi Imager itself should be reported to the upstream project.

Upstream project: https://github.com/raspberrypi/rpi-imager

## Reporting a vulnerability

If GitHub Security Advisories are enabled for this repository, please use a private security advisory.

If advisories are not available, open a minimal public issue that says a packaging security report is needed, without including exploit details. A maintainer can then arrange a private channel.

Please include:

- Affected package version or commit.
- A short description of the impact.
- Reproduction steps or affected files.
- Any suggested fix.
