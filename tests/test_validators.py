import pytest

from restoflow.utils.validators import (ValidationError, normalize_phone,
                                        password_strength, validate_address,
                                        validate_email, validate_password,
                                        validate_phone, validate_username)


def test_phone_normalize_variants():
    assert normalize_phone("+7 (916) 111-22-33") == "79161112233"
    assert normalize_phone("89161112233") == "79161112233"
    assert normalize_phone("9161112233") == "79161112233"


def test_phone_invalid():
    with pytest.raises(ValidationError):
        validate_phone("123")


def test_password_rules():
    with pytest.raises(ValidationError):
        validate_password("123")
    with pytest.raises(ValidationError):
        validate_password("abcdef")
    assert validate_password("Coffee2026!") == "Coffee2026!"


def test_username_rules():
    assert validate_username(" anna_01 ") == "anna_01"
    with pytest.raises(ValidationError):
        validate_username("я@")


def test_email_rules():
    assert validate_email(" Anna@Mail.RU ") == "anna@mail.ru"
    assert validate_email("") is None
    with pytest.raises(ValidationError):
        validate_email("anna@mail")


def test_address_rules():
    assert validate_address(" ул. Лесная, дом 12, кв 34 ") == "ул. Лесная, дом 12, кв 34"
    with pytest.raises(ValidationError):
        validate_address("Москва")


def test_strength():
    assert password_strength("Coffee2026!")["score"] >= 4