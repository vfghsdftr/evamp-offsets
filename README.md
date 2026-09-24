# evamp-offsets

Specific offsets for evamp.

Update the C++ header in **offsets** and commit it to **main**. The
**Publish offset JSON** action validates the header and automatically updates
**offsets.json**. No executable rebuild is needed for changes to supported
offset values.

Evamp downloads:
https://raw.githubusercontent.com/vfghsdftr/evamp-offsets/main/offsets.json

## Updating the header

- Keep `ClientVersion` set to the exact Roblox release these values support.
- Keep any version/count banner consistent with the actual header.
- Use literal hexadecimal or decimal integers, not C++ expressions.
- Check the repository's **Actions** page for a successful publish after each update.
- Do not edit `offsets.json` directly; it is generated from the header.

The converter reads data only. It never compiles or executes the header.
Malformed, duplicate, incomplete, or out-of-range declarations fail without
replacing the last valid JSON. It does not discover or verify memory offsets.

Evamp still requires Roblox's latest Windows LIVE version, imtheo's offsets
and flags, and this file's version to match. Required feature fields must
validate. Unused lighting/sky refresh fields and optional material/render-view
lookups may remain zero when the program has another valid path. Missing
primary pointers or other required fields still block attachment.

Files here are public. Never include credentials or personal information.
