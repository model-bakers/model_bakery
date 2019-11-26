"""
Migrate from model_mommy to model_bakery.

``python from_mommy_to_bakery.py --dry-run``

Please check your dependency files.
"""

import argparse
import os
import re

PACKAGE_NAME = r"\bmodel_mommy\b"
PACKAGE_NAME_PATTERN = re.compile(PACKAGE_NAME)
PACKAGE_RECIPES = r"\bmommy_recipes\b"
PACKAGE_RECIPES_PATTERN = re.compile(PACKAGE_RECIPES)
PACKAGE_LEGACY_MODULE = r"\bmommy\b"
PACKAGE_LEGACY_MODULE_PATTERN = re.compile(PACKAGE_LEGACY_MODULE)

LEGACY_AND_NEW = [
    {"old": PACKAGE_NAME_PATTERN, "new": r"model_bakery"},
    {"old": PACKAGE_RECIPES_PATTERN, "new": r"baker_recipes"},
    {"old": PACKAGE_LEGACY_MODULE_PATTERN, "new": r"baker"},
]
EXCLUDE = [
    "node_modules",
    "venv",
    ".git",
    "sql",
    "docs",
    "from_mommy_to_bakery.py",
    "Pipfile",
    "Pipfile.lock",
]


def _find_changes(content, pattern, new_value):
    new_content, substitutions = re.subn(pattern, new_value, content)
    return new_content, substitutions > 0


def _rename_recipe_file(to_be_renamed, dry_run):
    if dry_run is True:
        print("Will be renamed:")
    for old_recipe_file in to_be_renamed:
        root = old_recipe_file[: old_recipe_file.rfind("/")]
        if dry_run is False:
            os.rename(old_recipe_file, f"{root}/baker_recipes.py")
        else:
            print(old_recipe_file)


def _replace_legacy_terms(file_path, dry_run):
    try:
        content = open(file_path, "r").read()
    except UnicodeDecodeError:
        return
    changed = []
    for patterns in LEGACY_AND_NEW:
        old, new = patterns["old"], patterns["new"]
        content, has_changed = _find_changes(content, old, new)
        changed.append(has_changed)

    if any(changed):
        if dry_run is False:
            open(file_path, "w").write(content)
        else:
            print(file_path)


def _sanitize_folder_or_file(folder_or_file):
    folder_or_file = folder_or_file.strip()
    if folder_or_file.endswith("/"):
        # Remove trailing slash e.g.: '.tox/' -> '.tox'
        folder_or_file = folder_or_file[:-1]
    return folder_or_file


def check_files(dry_run):
    excluded_by_gitignore = [
        _sanitize_folder_or_file(folder_or_file)
        for folder_or_file in open(".gitignore").readlines()
    ]

    exclude = EXCLUDE[:]
    exclude.extend(excluded_by_gitignore)

    to_be_renamed = []
    for root, dirs, files in os.walk(".", topdown=True):
        dirs[:] = [directory for directory in dirs if directory not in exclude]

        for file_ in files:
            if file_ in exclude or not file_.endswith(".py"):
                continue

            file_path = f"{root}/{file_}"
            if file_ == "mommy_recipes.py":
                to_be_renamed.append(file_path)
            _replace_legacy_terms(file_path, dry_run)

    _rename_recipe_file(to_be_renamed, dry_run)


if __name__ == "__main__":
    description = "Help you to migrate from model_mommy to model_bakery."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="See which files will be changed.",
    )

    args = parser.parse_args()
    check_files(args.dry_run)
