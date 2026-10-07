# Huginn-Muninn offline index

Source: [Ringmast4r/Huginn-Muninn](https://github.com/Ringmast4r/Huginn-Muninn),
local source files read on October 7, 2026. The upstream README declares MIT.
Fingerbank and Satori attribution is retained in the interface and this record.
Individual source file SHA-256 values and the exact build time are recorded in
`huginn-provenance.json`. Rule dates are retained where supplied; build time is
not the age or validation date of an individual rule.

The 53,547,008-byte SQLite index contains:

- 388,354 distinct, syntactically valid, non-ignored Option 55 sequences from
  509,978 source rows. Excluded: 121,474 malformed rows and ten marked ignored;
  140 duplicate sequences were consolidated. Membership alone is not a device match.
- 1,374 exact Option 55 association rules in 777 source-specific references,
  derived from 481 Satori profiles and 557 combination rows. References overlap;
  these are not 777 unique device models. Rules without an exact Option 55
  sequence are outside this index. Packet types and additional constraints are
  retained and displayed as unverified when only a sequence is supplied.
- 40,289 six-digit vendor labels selected from 10,407,911 MAC vendor rows by
  overlap with the bundled OUI catalog's registered parent prefixes. They are
  corroborating corpus labels, not additional IEEE registrations or observed
  device counts. No full device MAC observations are imported.

The much larger device hierarchy, DHCP vendor strings, other protocol signatures,
and live container API are not bundled. There is no automatic network capture,
DHCP modification, device impersonation profile, or background corpus download.
All lookups use the packaged index offline. User inputs and local adapter reads
are not submitted to Huginn-Muninn or the portal.

Rebuild with `scripts/import_huginn.py PATH/TO/Huginn-Muninn`. The importer reads
the source databases in read-only mode and records checksums; it never changes
their tables. Upstream data quality is not silently repaired by guessing missing
delimiters or truncating out-of-range option values.

Privacy guidance references [RFC 7844](https://www.rfc-editor.org/rfc/rfc7844.html)
and [Microsoft's Wi-Fi address privacy documentation](https://support.microsoft.com/en-us/windows/experience/connectivity-networking/connect-to-a-wi-fi-network-in-windows).
Leetha's documented DHCP, discovery and stack fingerprinting informed the
explanation of remaining signals; its scanner is not embedded.
