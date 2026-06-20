# Boss Chess v1.0.0 Release Checklist

- Confirm the version is `1.0.0` in `pyproject.toml` and `boss_chess/__init__.py`
- Run the test suite locally
- Verify GUI launch on Windows, macOS, and Linux
- Verify `python main.py --gui` and `python main.py --terminal`
- Verify `boss-chess --gui` and `boss-chess --terminal`
- Confirm preferences save and reload correctly
- Confirm crash reports are written for unhandled GUI exceptions
- Build release artifacts from the tagged release workflow
- Attach artifacts to the GitHub Release
- Publish the release notes from `CHANGELOG.md`
