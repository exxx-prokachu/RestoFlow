import pytest

from restoflow.models import UserRole
from restoflow.services import auth_service, customer_service


def test_user_admin_flow(db):
    user = auth_service.create_user(
        db, "operator1", "Оператор Один", "Pass1234", UserRole.CASHIER)
    assert auth_service.authenticate(db, "operator1", "Pass1234")

    auth_service.change_password(db, user.id, "NewPass1234")
    assert auth_service.authenticate(db, "operator1", "NewPass1234")
    assert auth_service.authenticate(db, "operator1", "Pass1234") is None

    admin = auth_service.create_user(
        db, "admin", "Главный Админ", "Admin1234", UserRole.ADMIN)
    with pytest.raises(ValueError):
        auth_service.toggle_user(db, admin.id)

    auth_service.toggle_user(db, user.id)
    assert auth_service.authenticate(db, "operator1", "NewPass1234") is None


def test_client_block_flow(db):
    client = customer_service.register_client(
        db, full_name="Клиент Блок", phone="+70000000099",
        password="Client1234")
    assert customer_service.authenticate_client(db, "+70000000099", "Client1234")

    customer_service.toggle_active(db, client.id)
    assert customer_service.authenticate_client(
        db, "+70000000099", "Client1234") is None

    customer_service.toggle_active(db, client.id)
    assert customer_service.authenticate_client(db, "+70000000099", "Client1234")