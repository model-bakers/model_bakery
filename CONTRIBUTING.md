## How to Contribute

This page list all the steps you need to follow to set up `model_bakery` and be able to code it. Here they are:

1. [Fork this repo](https://github.com/model-bakers/model_bakery/fork) and clone it to your computer:

```
git clone git@github.com:YOUR_USER/model_bakery.git
```

2. [Install uv](https://docs.astral.sh/uv/getting-started/installation/). The commands below will create or update the environment automatically.

3. Change the code and run your tests with:

```
uv run pytest
```

4. We use [pre-commit](https://pre-commit.com/) for formatting, linting, and additional checks. To run all hooks:

```
uv run pre-commit run --all-files
```

5. Run the type checker:

```
uv run ty check model_bakery
```

To run `postgresql` and `postgis` specific tests:

1. [Install `docker`](https://docs.docker.com/get-docker/).

2. Install the `postgis` dependencies. Follow the
[instructions from the Django docs](https://docs.djangoproject.com/en/stable/ref/contrib/gis/install/geolibs/):

If you are on Ubuntu/Debian you run the following:

```shell
sudo apt update -y && sudo apt install -y binutils libproj-dev gdal-bin
```

3. Run the following script:

```shell
./postgis-tests.sh
```

That will spin up a `docker` container with `postgresql` and `postgis` enabled and run the full test
suite.
