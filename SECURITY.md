# Security Policy

## Supported versions

Only the latest released version of skillet receives security updates while
the project is in alpha. Once we reach 1.0 this policy will be revisited.

| Version | Supported |
| ------- | --------- |
| 0.1.x   | yes       |
| < 0.1   | no        |

## Reporting a vulnerability

Please **do not** report security issues via public GitHub issues.

Use GitHub's private vulnerability reporting:

1. Go to https://github.com/stephaneglaugier91/skillet/security/advisories
2. Click **Report a vulnerability**
3. Include a description, reproduction steps, and the affected version(s).

We will acknowledge receipt within 72 hours and aim to provide an initial
assessment within 7 days. If the report is valid, we'll coordinate a fix
and a disclosure timeline with you.

## Scope

skillet copies files from installed Python packages into a user-chosen
directory under `.claude/skills/`. In-scope concerns include (but are not
limited to):

- Path traversal during install or uninstall.
- Manifest tampering leading to arbitrary file deletion.
- Code execution triggered by metadata in an installed package.

Out of scope: anything that requires an attacker to already control the
contents of a Python package the user has installed (skillet trusts the
packages on `sys.path`).
