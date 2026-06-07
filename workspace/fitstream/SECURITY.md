# 🔒 Security Policy — FitStream

## Supported Versions

| Version | Supported          |
|--------|--------------------|
| 0.1.x  | ✅ Active support  |

## Reporting a Vulnerability

If you discover a security vulnerability in FitStream, please **do NOT open a public issue**.

Instead, email us at: **security@fitstream.dev**

We will respond within 48 hours with:
- Confirmation of receipt
- Initial assessment of severity
- Expected timeline for a fix

### What to Include
- Detailed description of the vulnerability
- Steps to reproduce (proof of concept if available)
- Affected versions/components
- Potential impact

### What to Expect
- Critical: Hotfix within 24 hours
- High: Patch within 3 days
- Medium: Fix in next release (within 2 weeks)
- Low: Queue for next milestone

## Security Best Practices (for Deployers)

1. **CORS**: Set `FITSTREAM_CORS_ORIGINS` to restrict allowed origins in production
   ```bash
   export FITSTREAM_CORS_ORIGINS="https://myapp.com,https://admin.myapp.com"
   ```

2. **API Keys**: Enable authentication with `FITSTREAM_API_KEYS`
   ```bash
   export FITSTREAM_API_KEYS="sk-abc123,sk-def456"
   ```

3. **Rate Limiting**: Defaults are 30 req/min, 5 generation/min per IP

4. **File Uploads**: Restricted to images only (jpg, png, webp), max 50MB

5. **No models in Docker image**: Model weights must be mounted as volumes

## Dependencies

We use `pip-audit` and `dependabot` to track vulnerable dependencies.
Run locally:
```bash
pip-audit
```

## Acknowledgments

We follow responsible disclosure. Researchers who report valid vulnerabilities
will be acknowledged (with permission) in our releases.