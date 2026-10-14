# Security and privacy

Focus is a personal local workspace, bound to 127.0.0.1 with Streamlit CORS and XSRF protections. It has no authentication or multi-user isolation. Do not expose it as a shared LAN or internet service.

The live SQLite database, automatic backups, plain ZIP backups, and JSON/CSV/Markdown exports are unencrypted. Optional `.focus` backup exports use AES-256-GCM with a fresh nonce and salt and a scrypt-derived key. Passwords are not stored. Wrong passwords and altered ciphertext fail authenticated decryption. Encryption protects that exported file; it does not encrypt the live workspace or protect a compromised device.

Application telemetry is disabled. No remote AI, cloud sync, or automatic upload is configured. Markdown preview omits images and raw HTML. Links open on user action. The rich editor keeps a local browser draft recovery copy; use the app only in a browser/device you trust. Restoring a workspace creates a new draft epoch so previous browser recovery copies do not override restored data.

Restore never executes uploaded SQL or extracts ZIP paths. It bounds file sizes, checks hashes, validates the known schema, values, foreign keys, and dependency cycles, writes a safety snapshot, then replaces data transactionally. Plain ZIP hashes detect corruption, not sender authenticity. Use trusted backups.

SQL mutations are parameterized; CSV formula-leading cells are escaped. Automatic backup retention removes only known backup filenames in the application's own backup directory. Desktop capture and reminders are optional local Windows facilities while the app is open; no system service, application monitoring, or remote control is installed.

Local file permissions and device security remain the user's responsibility. For vulnerabilities, use GitHub private vulnerability reporting when available, or request a private contact without publishing tokens or workspace data. Supported release: 1.1.x.
