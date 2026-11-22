from datetime import datetime, timedelta, timezone

from backend.app import models as m
from test_development import headers, pool


def test_mvp_open_close_feedback_and_repeat(client, pool, db_session):
    course, teacher, student = pool["course"], pool["teacher"], pool["student"]
    auth = headers(teacher)
    root = f"/api/asignaturas/{course.id}/flash-test"
    now = datetime.now(timezone.utc)

    def window(opens, closes):
        return client.put(root + "/ventana", headers=auth, json={"apertura": opens.isoformat(), "cierre": closes.isoformat()})

    assert window(now + timedelta(hours=2), now + timedelta(hours=1)).status_code == 422
    assert window(now + timedelta(hours=1), now + timedelta(hours=2)).status_code == 200
    invite = client.post(root + "/despacho", headers=auth, json=[student.id]).json()["items"][0]
    original = "/api/flash-test/" + invite["token"]
    assert client.get(original + "/info").json()["preguntas"] == []
    assert client.post(original + "/start").status_code == 409
    assert window(now - timedelta(hours=1), now + timedelta(hours=1)).status_code == 200
    assert client.post(original + "/start").status_code == 200
    assert client.post(original + "/answer", json={"question_id": pool["choice"]["id"], "answer": "A"}).status_code == 200
    assert window(now - timedelta(hours=1), now - timedelta(seconds=1)).status_code == 200
    assert client.get(original + "/info").json()["estado"] == "completado"

    db_session.expire_all()
    first = db_session.query(m.FlashTest).filter_by(token=invite["token"]).one()
    assert first.respuestas == {str(pool["choice"]["id"]): "A"}
    endpoint = f"/api/flash-tests/{first.id}"
    assert client.put(endpoint + "/retroalimentacion", json={"texto": "Comentario"}).status_code == 401
    assert client.put(endpoint + "/retroalimentacion", headers=auth, json={"texto": "Revisa el criterio."}).status_code == 200
    assert client.post(endpoint + "/repetir", headers=auth).status_code == 409
    assert window(now - timedelta(hours=1), now + timedelta(hours=1)).status_code == 200
    retry = client.post(endpoint + "/repetir", headers=auth)
    assert retry.status_code == 200
    token = retry.json()["token"]
    assert client.post(endpoint + "/repetir", headers=auth).status_code == 409
    repeat = client.get(f"/api/flash-test/{token}/info").json()
    assert repeat["estado"] == "pendiente" and repeat["respuestas"] == {}
    payload = {"token": invite["token"], "respuestas": {}, "tiempo_transcurrido": 0}
    result = client.post(original + "/submit", json=payload).json()
    assert result["retroalimentacion"] == "Revisa el criterio." and result["siguiente_token"] == token
    attempts = client.get(root + "/intentos", headers=auth).json()
    assert [record["estado"] for record in attempts] == ["completado", "pendiente"]
