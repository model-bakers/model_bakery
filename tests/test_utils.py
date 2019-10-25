import pytest

from model_bakery.utils import import_from_str

from tests.generic.models import User


def test_import_from_str():
    with pytest.raises(AttributeError):
        import_from_str('tests.generic.UndefinedObject')

    with pytest.raises(ImportError):
        import_from_str('tests.generic.undefined_path.User')

    assert import_from_str('tests.generic.models.User') == User
    assert import_from_str(User) == User
