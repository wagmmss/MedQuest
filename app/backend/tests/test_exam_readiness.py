def test_exam_readiness_reports_gaps_and_limited_sample(client):
    client.post("/api/questions/1/attempt", json={"selected_letter": "B"})
    report = client.get("/api/stats/exam-readiness?institution=USP-SP").get_json()
    assert report["institution"] == "USP-SP"
    assert report["answered"] == 1
    assert report["areas"][0]["sample"] == "limited"
    assert report["areas"][0]["action"].startswith("/estudar?")


def test_exam_readiness_excludes_other_user_attempts(client):
    with client.application.app_context():
        from api.db import get_db
        db = get_db()
        db.execute(
            """INSERT INTO attempts
               (question_id, selected_letter, is_correct, answered_at, confidence, user_id)
               VALUES (1, 'B', 1, '2026-08-20T12:00:00+00:00', 'certeza', 'other-user')"""
        )
        db.commit()
    report = client.get("/api/stats/exam-readiness?institution=USP-SP").get_json()
    assert report["answered"] == 0
    assert sum(area["attempts"] for area in report["areas"]) == 0
