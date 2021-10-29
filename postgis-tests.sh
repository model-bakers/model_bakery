#!/usr/bin/env bash
# -*- coding: utf-8 -*-
set -euo pipefail

###
### Run test suite against PostgreSQL DB with Postgis installed.
###
### This script will attempt to spin up a PostgreSQL Docker container against
### which the tests will be run. It will spin it down once the tests are finished,
### so if you are already running PostgreSQL locally, instead of using this
### script, simply run:
###
###     # TEST_DB=postgis PGUSER=postgres python -m pytest
###
### This script uses the `python` on the current `$PATH`, but can be overridden
### by setting the `PYTHON_CLI` environment variable.
###
### Usage:
###
###     ./postgis-tests.sh [-h|--help]
###
### Options:
###
###     -h, --help          print (this) help and exit
###

function help {
    # Print this file's contents, but only the lines that start
    # with `###` (documentation lines, above).
    sed -rn 's/^### ?//;T;p' "$0"
}

function HAS {
    # Check if the system has a certain program ($1) installed.
    # Output is silenced, but the function returns the result of
    # the `command` statement.
    command -v $1 > /dev/null 2>&1
    return $?
}

# Script variables
PROJECT_ROOT="$(dirname $(readlink -f "$0"))" # Same level as this file

# Dependency variables (e.g. PYTHON3_CLI=python3)
PYTHON=${PYTHON_CLI:-python}

DEPS="$PYTHON"

# Arg defaults
export PGPORT=${PGPORT:-5432}
export PGUSER=${PGUSER:-postgres}
export PGPASSWORD=${PGPASSWORD:-postgres}
export TEST_DB=${TEST_DB:-postgis}

# Argument parsing using "getopt"
OPTIONS=h
LONGOPTS=help

PARSED=$(getopt --options=$OPTIONS --longoptions=$LONGOPTS --name "$0" -- "$@")
PARSE_EXIT=$?

if [[ $PARSE_EXIT -ne 0 ]]; then
    exit $PARSE_EXIT
fi

eval set -- "$PARSED"

while true; do
    case "$1" in
        -h|--help)
            help
            shift
            exit 0
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Error. Exiting."
            exit 3
            ;;
    esac
done

# Grab the remaining positional argument(s) (not needed here)
# if [[ $# -ne 0 ]]; then
#     POSITIONAL_1=$1
#     POSITIONAL_1=$2
# else
#     echo "Missing positional args?"
#     exit 1
# fi

echo "Checking dependencies [$(echo ${DEPS} | sed 's/ /, /g')]..."
for dep in $DEPS; do
    MISSING_DEP=false

    if ! HAS $dep; then
        echo "You do not have '${dep}' installed, or it is not available on your PATH!"
        echo "If '${dep}' is not what it is called on your system, set the ${dep^^}_CLI environment variable."
        MISSING_DEP=true
    fi

    if [[ $MISSING_DEP = true ]]; then
        echo "Missing dependencies."
        exit 1
    fi
done

# Run the postgres container with all extensions installed
$PROJECT_ROOT/postgres-docker --port $PGPORT

# Run the tests
$PYTHON -m pytest

# Spin down the postgis container
$PROJECT_ROOT/postgres-docker --kill
