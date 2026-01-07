# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in measure-ai-proficiency, please report it responsibly.

### Where to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please report security issues by:

1. **Email:** Send details to the maintainer (check GitHub profile for contact info)
2. **GitHub Security Advisory:** Use the [Security Advisories](https://github.com/pskoett/measuring-ai-proficiency/security/advisories) feature

### What to Include

When reporting a security issue, please include:

- **Type of vulnerability** (e.g., code execution, information disclosure, etc.)
- **Full path** of the source file(s) affected
- **Location** of the vulnerable code (tag/branch/commit or direct URL)
- **Step-by-step instructions** to reproduce the issue
- **Proof-of-concept or exploit code** (if possible)
- **Impact** of the issue, including how an attacker might exploit it

### What to Expect

- **Acknowledgment:** We'll acknowledge receipt within 48 hours
- **Updates:** We'll provide updates on progress within 7 days
- **Timeline:** We aim to release a fix within 30 days for critical issues
- **Credit:** We'll credit you in the security advisory (unless you prefer to remain anonymous)

## Security Considerations

### What This Tool Does

measure-ai-proficiency is a **local filesystem scanner**:

- Reads files in directories you specify
- Does NOT send data over the network
- Does NOT execute code from scanned repositories
- Does NOT modify scanned repositories (read-only)

### Potential Risks

While this tool is designed to be safe, be aware of:

1. **File System Access**
   - The tool reads files in the directories you scan
   - Ensure you trust the repositories you're scanning
   - The tool respects file permissions

2. **YAML Configuration**
   - `.ai-proficiency.yaml` files are parsed with `yaml.safe_load()`
   - No arbitrary code execution from YAML files

3. **Git Commands**
   - The tool runs `git log` commands for commit history
   - Commands are non-destructive and read-only
   - Git timeout is configurable (default: 5 seconds)

4. **Subprocess Usage**
   - Git commands use `subprocess.run()` with timeout
   - No shell=True usage (prevents shell injection)
   - Commands use explicit argument arrays

### Best Practices for Users

- **Scan trusted repositories only** - While the tool is read-only, be cautious
- **Review YAML configs** - Check `.ai-proficiency.yaml` files before scanning
- **Use virtual environments** - Isolate the tool from your system Python
- **Keep updated** - Use the latest version for security fixes

## Vulnerability Disclosure Policy

We follow responsible disclosure:

1. **Private disclosure** - We'll work with you privately to understand and fix the issue
2. **Coordinated release** - We'll agree on a disclosure timeline
3. **Public disclosure** - After a fix is released, we'll publish a security advisory
4. **CVE assignment** - We'll request a CVE if appropriate

## Security Updates

Security updates will be:

- Released as patch versions (e.g., 0.2.1)
- Announced in GitHub Security Advisories
- Documented in CHANGELOG.md with `[SECURITY]` prefix
- Prioritized for immediate release

## Security Hall of Fame

We'd like to thank the following individuals for responsibly disclosing security issues:

*(No vulnerabilities reported yet)*

## Questions?

For general security questions (not vulnerabilities), you can:

- Open a GitHub Discussion
- Ask in GitHub Issues with the `security` label

Thank you for helping keep measure-ai-proficiency secure!
