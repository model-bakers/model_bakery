# Changelog

All notable changes to `model_bakery` will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased](https://github.com/model-bakers/model_bakery/tree/main)

### Added

### Changed

### Removed

## [1.12.0](https://pypi.org/project/model-bakery/1.12.0/)

### Added
- Add support for CharField with max_length=None

### Changed
- Fix utils.seq with start=0

## [1.11.0](https://pypi.org/project/model-bakery/1.11.0/)

### Added
- Add psycopg3 support for Django 4.2

## [1.10.3](https://pypi.org/project/model-bakery/1.10.3/)

### Changed
- Enforce Python 3.7 as a minimum version in project metadata

### Removed
- dropped support for `FloatRangeField` as it was removed in Django 3.1
- [dev] Temporary drop Django 4.2 to package classifiers (waiting for build backend support)

## [1.10.2](https://pypi.org/project/model-bakery/1.10.2/)

### Changed
- [dev] Test Python 3.11 with Django 4.2
- [dev] Add Django 4.2 to package classifiers

## [1.10.1](https://pypi.org/project/model-bakery/1.10.1/)

### Changed
- [dev] Fix GitHub Action for publishing to PyPI

## [1.10.0](https://pypi.org/project/model-bakery/1.10.0/)

### Added
- Django 4.2 support

### Changed
- [dev] Switch to Python 3.11 release in CI
- [dev] Unify and simplify tox config with tox-py
- [dev] `pre-commit autoupdate && pre-commit run --all-files`
- [dev] Run `pyupgrade` with Python 3.7 as a base
- [dev] PEP 621: Migrate from setup.py and setup.cfg to pyproject.toml
- [dev] Convert `format` and some string interpolations to `fstring`

## [1.9.0](https://pypi.org/project/model-bakery/1.9.0/)

### Changed
- Fixed a bug with `seq` being passed a tz-aware start value [PR #353](https://github.com/model-bakers/model_bakery/pull/353)
- Create m2m when using `_bulk_create=True` [PR #354](https://github.com/model-bakers/model_bakery/pull/354)
- [dev] Use official postgis docker image in CI [PR #355](https://github.com/model-bakers/model_bakery/pull/355)

## [1.8.0](https://pypi.org/project/model-bakery/1.8.0/)

### Changed
- Improve `Baker.get_fields()` to subtract lists instead of extra set cast [PR #352](https://github.com/model-bakers/model_bakery/pull/352)

## [1.7.1](https://pypi.org/project/model-bakery/1.7.1/)

### Changed
- Remove warning for future Django deprecation [PR #339](https://github.com/model-bakers/model_bakery/pull/339)

## [1.7.0](https://pypi.org/project/model-bakery/1.7.0/)

### Changed
- Fixed a bug with overwritten `_save_kwargs` and other custom arguments [PR #330](https://github.com/model-bakers/model_bakery/pull/330)

## [1.6.0](https://pypi.org/project/model-bakery/1.6.0/)

### Added
- Python 3.11 support [PR #327](https://github.com/model-bakers/model_bakery/pull/327)
- Django 4.1 support [PR #327](https://github.com/model-bakers/model_bakery/pull/327)
- Added documentation for callables, iterables, sequences [PR #309](https://github.com/model-bakers/model_bakery/pull/309)

### Changed
- [dev] Replace changelog reminder action with a custom solution that can ignore Dependabot PRs [PR #328](https://github.com/model-bakers/model_bakery/pull/328)

### Removed
- Drop Python 3.6 support [PR #325](https://github.com/model-bakers/model_bakery/pull/325)
- Drop Django 2.2 support [PR #326](https://github.com/model-bakers/model_bakery/pull/326)

## [1.5.0](https://pypi.org/project/model-bakery/1.5.0/)

### Added
- Add py.typed export per [PEP 561](https://www.python.org/dev/peps/pep-0561/) [PR #158](https://github.com/model-bakers/model_bakery/pull/158)

### Changed
- Extend type hints in `model_bakery.recipe` module, make `Recipe` class generic [PR #292](https://github.com/model-bakers/model_bakery/pull/292)
- Explicitly add _fill_optional parameters to baker.make and baker.prepare to aid IDE autocomplete function. [PR #264](https://github.com/model-bakers/model_bakery/pull/264)
- Fixed errors with reverse M2M relationships [PR #299](https://github.com/model-bakers/model_bakery/pull/299)
- Fixed errors with reverse M2O relationships [PR #300](https://github.com/model-bakers/model_bakery/pull/300)
- Improve exception message for unknown field types [PR #301](https://github.com/model-bakers/model_bakery/pull/301)
- Fixed random generation of ContentType values when there is no database access [#290](https://github.com/model-bakers/model_bakery/pull/290)

## [1.4.0](https://pypi.org/project/model-bakery/1.4.0/)

### Added
- Added postgis version to test settings
- Add support for Python 3.10 [PR #244](https://github.com/model-bakers/model_bakery/pull/244)
- Support for Django 4.0 [PR #236](https://github.com/model-bakers/model_bakery/pull/236)

### Changed
- Validate `increment_by` parameter of `seq` helper when `value` is an instance of `datetime` [PR #247](https://github.com/model-bakers/model_bakery/pull/247)
- Fix a simple typo in `bulk_create` disclaimer in docs [PR #245](https://github.com/model-bakers/model_bakery/pull/245)
- Allow relation `_id` fields to use sequences [PR #253](https://github.com/model-bakers/model_bakery/pull/253)
- Fix bulk_create not working with multi-database setup [PR #252](https://github.com/model-bakers/model_bakery/pull/252)
- Conditionally support NullBooleanField, it's under deprecation and will be removed in Django 4.0 [PR #250](https://github.com/model-bakers/model_bakery/pull/250)
- Fix Django max version pin in requirements file [PR #251](https://github.com/model-bakers/model_bakery/pull/251)
- Improve type hinting to return the correct type depending on `_quantity` usage [PR #261](https://github.com/model-bakers/model_bakery/pull/261)

### Removed
- Drop official Django 3.1 support. Django 2.2 is still supported, and 3.1 will likely keep working, but it’s not tested [PR #236](https://github.com/model-bakers/model_bakery/pull/236)

## [1.3.3](https://pypi.org/project/model-bakery/1.3.3/)

### Added
- `_bulk_create` flag is not populating related objects as well [PR #206](https://github.com/model-bakers/model_bakery/pull/206)
- Add support for iterators on GFK fields when using _quantity param [PR #207](https://github.com/model-bakers/model_bakery/pull/207)
- Add support for iterators on many-to-many fields [PR#237](https://github.com/model-bakers/model_bakery/pull/237)

### Changed
- Fix typos in Recipes documentation page [PR #212](https://github.com/model-bakers/model_bakery/pull/212)
- Add `venv` to ignored folders of `flake8` and `pydocstyle` [PR#214](https://github.com/model-bakers/model_bakery/pull/214)
- Run `flake8` after code modifications when linting [PR#214](https://github.com/model-bakers/model_bakery/pull/214)
- Add typing for `baker.make` and `baker.prepare` [PR#213](https://github.com/model-bakers/model_bakery/pull/213)

## [1.3.2](https://pypi.org/project/model-bakery/1.3.2/)

### Changed
- Fixed a bug (introduced in [1.2.1](https://pypi.org/project/model-bakery/1.2.1/)) that was breaking imports of recipes from non-installed-app modules [PR #201](https://github.com/model-bakers/model_bakery/pull/201)
- Dependencies updates

## [1.3.1](https://pypi.org/project/model-bakery/1.3.1/)

### Added
- [dev] Add explanations to imports in `generators.py` to match with current supported Django versions [PR #179](https://github.com/model-bakers/model_bakery/pull/179)

### Changed
- Fix `requirements.txt` to cover Django 3.2 (everything from 2.2 till 4.0) [PR #182](https://github.com/model-bakers/model_bakery/pull/182)


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
