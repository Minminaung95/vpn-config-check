# VPN Config Check

A small, offline sing-box JSON linter with English and Myanmar diagnostics.
Created for VPN developers who want to catch common configuration mistakes without uploading credentials to an online checker.

## Run

Requires Python 3.10 or later. No third-party packages, network access, account, or API key required.

```sh
python vpn_config_check.py examples/basic.json
python vpn_config_check.py path/to/config.json --lang my
python vpn_config_check.py path/to/config.json --json
python -m unittest discover -s tests -v
```

မြန်မာဘာသာဖြင့် ပြရန် `--lang my` ထည့်ပါ။ မူရင်း config ကို မပြင်ပါ။ ဖိုင်ကို အင်တာနက်ပေါ် မပို့ပါ။

Exit codes: 0 = supported checks found no issues; 1 = issues found; 2 = input file could not be read.

## Checks

- Strict JSON parsing, including duplicate keys and nonstandard NaN/Infinity.
- Top-level configuration sections and item shapes.
- Duplicate inbound tags and duplicate outbound/endpoint tags.
- Present server/listen ports: integer range 1–65535.
- Selector and URLTest members; selector default membership.
- Outbound/endpoint detours, route final and nested rule outbound references.
- Diagnostics contain fixed field locations and indexes, never config values or arbitrary input keys.

## Limits

This is an initial, partial static linter, **not a complete sing-box validator or a VPN client**. It does not check connectivity, protocol-specific required fields, DNS rules, all nested port fields, dependency cycles, security, or version compatibility. Unknown fields are left alone. JSON comments are not supported. Run `sing-box check -c config.json` using your actual sing-box version after linting. The example uses direct routing only; it does not create an encrypted tunnel.

Field references: [selector](https://sing-box.sagernet.org/configuration/outbound/selector/), [dial](https://sing-box.sagernet.org/configuration/shared/dial/), [route](https://sing-box.sagernet.org/configuration/route/).

## Contributing

Report a reproducible issue with a synthetic example. Remove passwords, tokens, private keys, server addresses and personal information before sharing any file. Include the sing-box version. Add regression tests for checker fixes. Myanmar translations and documented compatibility improvements are welcome.

## Project status

Initial release, October 2026. Maintainer: Min Min Aung (GitHub: Minminaung95). No adoption, download or external contributor claims are made. AI assisted with the initial implementation; the maintainer should review changes before releasing them.

MIT license. Not affiliated with sing-box, Anthropic or OpenAI.
