# Changelog

All notable changes to `model_bakery` will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased](https://github.com/model-bakers/model_bakery/tree/master)

### Added

### Changed

### Removed

## [1.2.0](https://pypi.org/project/model-bakery/1.2.0/)

### Added
- Support to django 3.1 `JSONField` [PR #85](https://github.com/model-bakers/model_bakery/pull/85) and [PR #106](https://github.com/model-bakers/model_bakery/pull/106)
- Added type annotations [PR #100](https://github.com/model-bakers/model_bakery/pull/100)
- Support for Python 3.9 [PR #113](https://github.com/model-bakers/model_bakery/pull/113/)
- [dev] Changelog reminder (GitHub action)
- Add pytest example

### Changed
- Support for `prefix` in `seq` values ([PR #111](https://github.com/model-bakers/model_bakery/pull/111) fixes [Issue #93](https://github.com/model-bakers/model_bakery/issues/93))
- [dev] CI switched to GitHub Actions
- [dev] Freeze dev requirements
- [dev] Add Django 3.1 to test matrix [PR #103](https://github.com/model-bakers/model_bakery/pull/103) and [PR #112](https://github.com/model-bakers/model_bakery/pull/112)
- [dev] pre-commit to use local packages (so versions will match)
- [dev] consistent use of pydocstyle
- [dev] Updates to MANIFEST.in
- [dev] Correct field in recipe docs
- [dev] Adjust imports for Django 3.1 compatibility [PR #112](https://github.com/model-bakers/model_bakery/pull/112)

### Removed

## [1.1.1](https://pypi.org/project/model-bakery/1.1.1/)

### Added
- Support to Postgres fields: `DecimalRangeField`, `FloatRangeField`, `IntegerRangeField`, `BigIntegerRangeField`, `DateRangeField`, `DateTimeRangeField` [PR #80](https://github.com/model-bakers/model_bakery/pull/80)

### Changed
- Add isort and fix imports [PR #77](https://github.com/model-bakers/model_bakery/pull/77)
- Enable `seq` to be imported from `baker` [PR #76](https://github.com/model-bakers/model_bakery/pull/76)
- Fix PostGIS model registration [PR #67](https://github.com/model-bakers/model_bakery/pull/67)

### Removed

## [1.1.0](https://pypi.org/project/model-bakery/1.1.0/)

### Added
- Django 3.0 and Python 3.8 to CI [PR #48](https://github.com/model-bakers/model_bakery/pull/48/)

### Changed

- Improve code comments [PR #31](https://github.com/model-bakers/model_bakery/pull/31)
- Switch to tox-travis [PR #43](https://github.com/model-bakers/model_bakery/pull/43)
- Add black job [PR #42](https://github.com/model-bakers/model_bakery/pull/42)
- README.md instead of rst [PR #44](https://github.com/model-bakers/model_bakery/pull/44)
- New `start` argument in `baker.seq` [PR #56](https://github.com/model-bakers/model_bakery/pull/56)
- Fixes bug when registering custom fields generator via `settings.py` [PR #58](https://github.com/model-bakers/model_bakery/pull/58)
- The different IntegerField types now will generate values on their min/max range [PR #59](https://github.com/model-bakers/model_bakery/pull/59)

### Removed

## [1.0.2](https://pypi.org/project/model-bakery/1.0.2/)

### Added

### Changed
- Improvements on the migrations script

### Removed

## [1.0.1](https://pypi.org/project/model-bakery/1.0.1/)

### Added
- Python script to help developers on migrating from Model Mommy to Model Bakery

### Changed

### Removed

## [1.0.0](https://pypi.org/project/model-bakery/1.0.0/)

### Added

### Changed
- Rename model_mommy code to model_bakery

### Removed
