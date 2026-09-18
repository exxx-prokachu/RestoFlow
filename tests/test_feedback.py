import pytest

from restoflow.services import customer_service, feedback_service


@pytest.fixture()
def client(db):
    return customer_service.create_client(
        db, full_name="Отзыв Тестов", phone="+70000000088")


def test_feedback_anonymous_and_stats(db, client):
    fb1 = feedback_service.create_feedback(
        db, client_id=client.id, rating=5, comment="Отлично",
        is_anonymous=True)
    fb2 = feedback_service.create_feedback(
        db, client_id=client.id, rating=3, comment="Нормально")

    items = feedback_service.list_feedback_detailed(db)
    names = {i["id"]: i["author"] for i in items}
    assert names[fb1.id] == "Аноним"
    assert names[fb2.id] == "Отзыв Тестов"

    stats = feedback_service.rating_stats(db)
    assert stats["count"] == 2
    assert stats["average"] == 4.0
    assert stats["distribution"][5] == 1
    assert stats["distribution"][3] == 1

    feedback_service.reply_feedback(db, fb2.id, "Спасибо за отзыв!")
    items = {i["id"]: i for i in feedback_service.list_feedback_detailed(db)}
    assert items[fb2.id]["reply"] == "Спасибо за отзыв!"