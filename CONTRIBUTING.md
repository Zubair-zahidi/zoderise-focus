# Contributing

Create a branch, keep changes focused, and describe the user-visible behavior and verification. Use a temporary `FOCUS_DATA_HOME` for development; do not commit personal SQLite files, exports, credentials, or logs.

Run `python -m unittest discover -s tests -v`. Add meaningful tests for persistence, restoration, timer behavior, and new workflows. For visual changes, inspect the actual rendered desktop and narrow-screen layouts. Preserve native labels and keyboard access, reduced-motion support, and the clear separation between demo and personal data.

New features should remain useful offline. Do not introduce tracking, external data uploads, or a public-server mode as a side effect of another change. Document limitations honestly.
