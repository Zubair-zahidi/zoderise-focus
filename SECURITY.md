# Security and privacy

Zoderise Focus is a personal local workspace. Its SQLite database, JSON/CSV exports, Markdown files, and ZIP backups are unencrypted. It does not promise to prevent information leaks from a compromised device, a copied backup, or a public server configuration.

The default server binds to 127.0.0.1 with Streamlit CORS and XSRF protections enabled. The application does not implement authentication or multi-user isolation. Keep this configuration local; do not expose it on a LAN or the internet as a shared service.

Application telemetry is disabled. The app has no remote model provider, cloud sync, or automatic upload. Markdown preview does not execute raw HTML and omits Markdown images. External links remain user-controlled. Dependencies may require internet access during installation; the repository README's badges load externally on GitHub, not in the app.

Restore accepts only the documented backup format. Hash checking detects accidental corruption, not authenticity or malicious edits made with a recomputed hash. Schema and value validation protect application integrity, but a valid backup still replaces the workspace when explicitly confirmed. Use backups from a trusted source.

CSV cells beginning with spreadsheet-formula markers are escaped. ZIP paths are not extracted. Task and note mutations use SQL parameters. The local data directory inherits operating-system permissions; encryption and device access control remain the user's responsibility.

For a vulnerability, contact the maintainer through GitHub's private vulnerability reporting when available. Otherwise open an issue asking for a private contact channel without publishing exploit details, tokens, personal notes, or database files. Supported release: 1.0.x.
