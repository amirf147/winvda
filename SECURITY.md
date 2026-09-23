# Security Policy

## 1. Supported Versions

Security updates are applied to the active minor release branch. The table below summarizes the support lifecycle for `winvda` releases:

| Version | Supported |
| :--- | :--- |
| `0.1.x` | Yes |
| `< 0.1.0` | No |

## 2. Reporting a Vulnerability

If you identify a security vulnerability, privilege boundary defect, or memory safety violation in `winvda`, report it through private channels. Do not open public GitHub issues or public pull requests for undisclosed security vulnerabilities.

### Primary Reporting Channel
Submit reports through GitHub Private Vulnerability Reporting:
1. Navigate to the repository **Security** tab.
2. Select **Advisories** and click **Report a vulnerability**.
3. Include the following diagnostic data:
   - Minimal reproduction script
   - Host Windows build number (`sys.getwindowsversion().build`)
   - Process crash dump or exception traceback

### Secondary Contact
If GitHub Private Vulnerability Reporting is inaccessible, submit reports via email to `amirf147@gmail.com` with the subject line `[SECURITY] winvda vulnerability report`.

## 3. Vulnerability Response Timeline

The maintainer follows this structured coordination process:
1. **Acknowledgment:** Initial receipt confirmed within 48 hours.
2. **Triage:** Reproduction and root cause verification executed against target Windows builds.
3. **Remediation:** Fix developed and validated in a private advisory fork.
4. **Release:** Coordinated release published to PyPI alongside a GitHub Security Advisory within 14 days of triage confirmation.
