import pytest

from model_bakery.utils import import_if_str, import_from_str

from tests.generic.models import User


class TestUtils:
    def test_import_from_str(self):
        with pytest.raises(AttributeError):
            import_from_str('tests.generic.UndefinedObject')

        with pytest.raises(ImportError):
            import_from_str('tests.generic.undefined_path.User')

        assert import_from_str('tests.generic.models.User') == User

    def test_import_if_str(self):
        with pytest.raises(AttributeError):
            import_if_str('tests.generic.UndefinedObject')

        with pytest.raises(ImportError):
            import_if_str('tests.generic.undefined_path.User')

        assert import_if_str('tests.generic.models.User') == User
        assert import_if_str(User) == User
