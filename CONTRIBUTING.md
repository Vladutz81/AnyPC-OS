# Contributing

Thanks for helping! Short rules:

- Read [docs/LEGAL.md](docs/LEGAL.md) first. Never submit firmware, keys, game files or leaked code.
- Open an issue before large changes; small fixes can go straight to a PR.
- By contributing you agree your work is licensed GPL-3.0-or-later.
- Keep commits small, with clear messages. Sign off commits (`git commit -s`).
- Run the service tests before a PR: `cd shell/daemon && python3 -m unittest discover -s tests`.
- The UI has no build step: edit files in `shell/ui` and reload the page.
- New UI text goes into `shell/ui/js/i18n.js` in every language.

Areas that need help: image build, shell UI, hardware testing, documentation, translations.
