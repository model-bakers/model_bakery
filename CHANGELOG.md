# Changelog

All notable changes to `model_bakery` will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased](https://github.com/model-bakers/model_bakery/tree/main)

### Added

### Changed

### Removed


## [1.3.0](https://pypi.org/project/model-bakery/1.3.0/)

### Added
- Add Django 3.2 LTS support [PR #176](https://github.com/model-bakers/model_bakery/pull/176)
- Add new `_bulk_create` parameter to `make` for using Django manager `bulk_create` with `_quantity` [PR #134](https://github.com/model-bakers/model_bakery/pull/134)
- Add the functionality to import Django models using the `app_name.ModelName` convention in `import_from_str` [PR #140](https://github.com/model-bakers/model_bakery/pull/140)
- Add the functionality to import recipes using `app_name.recipe_name` [PR #140](https://github.com/model-bakers/model_bakery/pull/140)
- Add new `one_to_one` parameter to `foreign_key` to allow usage of `_quantity` for recipes based on models with OneToOne fields [PR #169](https://github.com/model-bakers/model_bakery/pull/169)
- [docs] Improved documentation on Recipe's import string [PR #175](https://github.com/model-bakers/model_bakery/pull/175/)
- [dev] Add a unit test for `utils.seq` [PR #143](https://github.com/model-bakers/model_bakery/pull/143)
- [dev] Run CI against `main` Django branch to cover possible upcoming changes/deprecations [PR #159](https://github.com/model-bakers/model_bakery/pull/159)
- [dev] Add GH Action for package releasing [PR #168](https://github.com/model-bakers/model_bakery/pull/168)

### Changed

- Fixed a bug (introduced in 1.2.1) that was breaking creation of model instances with related model fields [PR #164](https://github.com/model-bakers/model_bakery/pull/164)
- Type hinting fixed for Recipe "_model" parameter  [PR #124](https://github.com/model-bakers/model_bakery/pull/124)
- Dependencies updates from [dependabot](https://dependabot.com/) PRs [#170](https://github.com/model-bakers/model_bakery/pull/170) - [#171](https://github.com/model-bakers/model_bakery/pull/171) - [#172](https://github.com/model-bakers/model_bakery/pull/172) - [#173](https://github.com/model-bakers/model_bakery/pull/173) - [#174](https://github.com/model-bakers/model_bakery/pull/174)
- [dev] Modify `setup.py` to not import the whole module for package data, but get it from `__about__.py`  [PR #142](https://github.com/model-bakers/model_bakery/pull/142)
- [dev] Add Dependabot config file [PR #146](https://github.com/model-bakers/model_bakery/pull/146)
- [dev] Update Dependabot config file to support GH Actions and auto-rebase [PR #160](https://github.com/model-bakers/model_bakery/pull/160)

### Removed
- `model_bakery.timezone.now` fallback (use `django.utils.timezone.now` instead)  [PR #141](https://github.com/model-bakers/model_bakery/pull/141)
- `model_bakery.timezone.smart_datetime` function (directly use `model_bakery.timezone.tz_aware` instead)  [PR #147](https://github.com/model-bakers/model_bakery/pull/147)
- Remove all signs of Django 1.11 (as we dropped it in 1.2.1) [PR #157](https://github.com/model-bakers/model_bakery/pull/157)
- Drop unsupported Django 3.0 from CI (https://www.djangoproject.com/download/#unsupported-versions) [PR #176](https://github.com/model-bakers/model_bakery/pull/176)


## [1.2.1](https://pypi.org/project/model-bakery/1.2.1/)

### Added
- Add ability to pass `str` values to `foreign_key` for recipes from other modules [PR #120](https://github.com/model-bakers/model_bakery/pull/120)
- Add new parameter `_using` to support multi database Django applications [PR #126](https://github.com/model-bakers/model_bakery/pull/126)
- [dev] Add instructions and script for running `postgres` and `postgis` tests. [PR #118](https://github.com/model-bakers/model_bakery/pull/118)

### Changed
- Fixed _model parameter annotations [PR #115](https://github.com/model-bakers/model_bakery/pull/115)
- Fixes bug when field has callable `default` [PR #117](https://github.com/model-bakers/model_bakery/pull/117)

### Removed
- [dev] Drop Python 3.5 support as it is retired (https://www.python.org/downloads/release/python-3510/) [PR #119](https://github.com/model-bakers/model_bakery/pull/119)
- [dev] Remove support for Django<2.2 ([more about Django supported versions](https://www.djangoproject.com/download/#supported-versions)) [PR #126](https://github.com/model-bakers/model_bakery/pull/126)

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
