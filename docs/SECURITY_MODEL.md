# Security model

## Default-deny output

Rendered reports contain no JavaScript, forms, iframes, embedded objects, tracking pixels or remote runtime assets. Source links use `noopener noreferrer` when opening a new tab.

## Input handling

All supplied text is HTML-escaped. The contract validator rejects active-markup strings before rendering. URLs are limited to HTTP(S), but URL reputation is outside the current scope.

## Archive handling

The safe tar utility rejects absolute paths, parent traversal, symbolic links, hard links, device members, unsupported member types, excessive member counts and excessive uncompressed size. Extraction is performed member by member rather than with unrestricted `extractall`.

Issue archival uses an exclusive lock, staging directory, SHA-256 manifest and atomic directory replacement. An existing issue path may be reused only when its manifest is identical.

## Repository scan

The public-tree scanner looks for common token forms, private-key markers, personal machine paths, personal email domains, mainland-China phone patterns and literal secret assignments. This is defense in depth, not a substitute for GitHub secret scanning or human review.

## Out of scope

- authentication and multi-user authorization;
- network source acquisition;
- browser sandboxing;
- malware scanning of arbitrary uploads;
- legal, copyright or factual certification;
- production deployment hardening.
