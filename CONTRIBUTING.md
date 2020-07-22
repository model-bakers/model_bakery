## How to Contribute

This page list all the steps you need to follow to set up `model_bakery` and be able to code it. Here they are:

1. [Fork this repo](https://github.com/model-bakers/model_bakery/fork) and clone it to your computer:

```
git clone git@github.com:YOUR_USER/model_bakery.git
```

2. Install the dev dependencies:

```
pip install -r dev_requirements.txt
```

3. Change the code and run your tests with:

```
make test
```

4. We use [pre-commit](https://pre-commit.com/) to ensure a unique code formatting for the project. But, if you ran into any CI issues with that, make sure your code changes respect it:

```
make lint
```

If you don't follow the step 4, your PR may fail due to `black`, `isort` or flake8` warnings.
