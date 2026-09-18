import pytest

from restoflow.services import customer_service, support_service


@pytest.fixture()
def client(db):
    return customer_service.create_client(
        db, full_name="Тест Тестов", phone="+70000000077")


def test_support_lifecycle(db, client):
    req = support_service.create_request(
        db, client_id=client.id, subject="Не положили соус",
        body="Заказ #1, отсутствует соус")
    assert req.status == "open"
    assert len(req.messages) == 1

    support_service.add_staff_message(db, req.id, "Админ", "Извините, начислим баллы")
    assert req.status == "in_progress"

    support_service.add_client_message(db, req.id, client.id, "Спасибо!")
    assert len(req.messages) == 3

    support_service.close_request(db, req.id)
    assert req.status == "closed"

    with pytest.raises(ValueError):
        support_service.add_client_message(db, req.id, client.id, "Ещё вопрос")

    support_service.reopen_request(db, req.id, client.id, "Продолжаю обращение")
    assert req.status == "in_progress"


def test_support_validation(db, client):
    from restoflow.utils.validators import ValidationError
    with pytest.raises(ValidationError):
        support_service.create_request(
            db, client_id=client.id, subject="Тема", body="")