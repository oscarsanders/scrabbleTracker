# Security policy

## Supported versions

Only the latest release on `main` receives security fixes.

## Reporting a vulnerability

Please **do not open a public issue**. Use GitHub's *Report a vulnerability*
button (Security → Advisories) on this repository to send a private report.
Include steps to reproduce and the affected version. You can expect an
acknowledgement within a few days; this is a volunteer-maintained project.

Design assumptions and known residual risks are documented in
[`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md).

## Deployment hygiene

- Never commit `.env` or real credentials.
- Set a strong `SCRABBLE_ADMIN_PASSWORD` and change it after first login.
- Use a paid or external PostgreSQL and keep backups for real data
  (see [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)).
