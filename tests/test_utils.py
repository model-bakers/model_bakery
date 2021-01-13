from inspect import getmodule

import pytest

from model_bakery.utils import get_calling_module, import_from_str
from tests.generic.models import User


def test_import_from_str():
    with pytest.raises(AttributeError):
        import_from_str("tests.generic.UndefinedObject")

    with pytest.raises(ImportError):
        import_from_str("tests.generic.undefined_path.User")

    assert import_from_str("tests.generic.models.User") == User
    assert import_from_str(User) == User
    assert import_from_str("generic.User") == User


def test_get_calling_module():
    # Reference to this very module
    this_module = getmodule(test_get_calling_module)

    # Once removed is the `pytest` module calling this function
    pytest_module = get_calling_module(1)
    assert pytest_module != this_module
    assert "pytest" in pytest_module.__name__

    # Test functions
    def dummy_secondary_method():
        return get_calling_module(2), get_calling_module(3)

    def dummy_method():
        return (*dummy_secondary_method(), get_calling_module(1), get_calling_module(2))

    # Unpack results from the function chain
    sec_mod, sec_pytest_mod, dummy_mod, pytest_mod = dummy_method()

    assert sec_mod == this_module
    assert "pytest" in sec_pytest_mod.__name__
    assert dummy_mod == this_module
    assert "pytest" in pytest_mod.__name__

    # Raise an `IndexError` when attempting to access too many frames removed
    with pytest.raises(IndexError):
        assert get_calling_module(100)
