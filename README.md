# Model Bakery: Smart fixtures for better tests

[![Build](https://img.shields.io/github/actions/workflow/status/model-bakers/model_bakery/ci.yml?branch=main)](https://github.com/model-bakers/model_bakery/actions?workflow=Tests)
[![Coverage](https://img.shields.io/badge/Coverage-97%25-success)](https://github.com/model-bakers/model_bakery/actions?workflow=Tests)
[![Latest PyPI version](https://img.shields.io/pypi/v/model_bakery.svg)](https://pypi.python.org/pypi/model_bakery/)
[![Documentation Status](https://readthedocs.org/projects/model-bakery/badge/?version=latest)](https://model-bakery.readthedocs.io/en/latest/?badge=latest)

*Model Bakery* offers you a smart way to create fixtures for testing in Django. With a simple and powerful API, you can create many objects with a single line of code.

> **Note:** Model Bakery is a rename of the legacy [Model Mommy project](https://pypi.org/project/model_mommy/).

## Installation

```bash
pip install model-bakery
```

## Supported Versions

Model Bakery follows the [Python](https://devguide.python.org/versions/) and [Django](https://docs.djangoproject.com/en/stable/internals/release-process/#supported-versions) release and support cycles. We drop support for Python and Django versions when they reach end-of-life.

## Basic usage

```python
# models.py
from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=30)
    email = models.EmailField()
    age = models.IntegerField()
    is_jards_macale_fan = models.BooleanField()
    bio = models.TextField()
    birthday = models.DateField()
    last_shopping = models.DateTimeField()

# test_models.py
from django.test import TestCase
from model_bakery import baker

class TestCustomerModel(TestCase):
    def setUp(self):
        self.customer = baker.make('shop.Customer')
        print(self.customer.__dict__)

"""
{'_state': <django.db.models.base.ModelState object at 0x1129a3240>,
 'age': 3841,
 'bio': 'vUFzMUMyKzlnTyiCxfgODIhrnkjzgQwHtzIbtnVDKflqevczfnaOACkDNqvCHwvtWdLwoiKrCqfppAlogSLECtMmfleeveyqefkGyTGnpbkVQTtviQVDESpXascHAluGHYEotSypSiHvHzFteKIcUebrzUVigiOacfnGdvijEPrZdSCIIBjuXZMaWLrMXyrsUCdKPLRBRYklRdtZhgtxuASXdhNGhDsrnPHrYRClhrSJSVFojMkUHBvSZhoXoCrTfHsAjenCEHvcLeCecsXwXgWJcnJPSFdOmOpiHRnhSgRF',
 'birthday': datetime.date(2019, 12, 3),
 'email': 'rpNATNsxoj@example.com',
 'is_jards_macale_fan': True,
 'id': 1,
 'last_shopping': datetime.datetime(2019, 12, 3, 21, 42, 34, 77019),
 'name': 'qiayYnESvqcYLLBzxpFOcGBIfnQEPx'}
"""
```

## Documentation

For more detailed information, check out the [full documentation](https://model-bakery.readthedocs.io/).

## Contributing

As an open-source project, Model Bakery welcomes contributions of many forms:

- Code patches
- Documentation improvements
- Bug reports

Take a look at our [contribution guidelines](CONTRIBUTING.md) for instructions
on how to set up your local environment.

## Maintainers

- [Bernardo Fontes](https://github.com/berinhard/)
- [Rustem Saiargaliev](https://github.com/amureki/)
- [Tim Klein](https://github.com/timjklein36)

## Creator

- [Vanderson Mota](https://github.com/vandersonmota/)

## License

Model Bakery is licensed under Apache License 2.0.
See the [LICENSE](LICENSE) file for more information.
