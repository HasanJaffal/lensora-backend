from httpx import AsyncClient

_COMPLETE_INDIVIDUAL = {
    "name": "Maya Deeb",
    "birthdate": "1998-04-12",
    "gender": "female",
    "city": "Tyre",
}


async def test_create_draft_allows_partial_data(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/intake",
        json={"status": "draft", "individualInfo": {"name": "Partial Person"}},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "draft"
    assert data["individualInfo"]["name"] == "Partial Person"


async def test_complete_requires_core_fields(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/intake",
        json={"status": "completed", "individualInfo": {"name": "No Birthdate"}},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation.error"
    fields = {detail["field"] for detail in body["error"]["details"]}
    assert "individualInfo.birthdate" in fields
    assert "motive.reasonForVisit" in fields


async def test_complete_succeeds_with_required_fields(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/intake",
        json={
            "status": "completed",
            "individualInfo": _COMPLETE_INDIVIDUAL,
            "motive": {"reasonForVisit": "Blurry vision at distance"},
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "completed"


async def test_checklists_are_captured_as_enumerated_arrays(
    api_client: AsyncClient,
) -> None:
    response = await api_client.post(
        "/api/v1/intake",
        json={
            "status": "draft",
            "motive": {
                "reasonForVisit": "Headaches on screens",
                "visualProblems": ["blurredVision", "doubleVision"],
                "functionalSigns": ["photophobia", "headache", "eyeStrain"],
            },
        },
    )

    assert response.status_code == 200
    motive = response.json()["data"]["motive"]
    assert motive["visualProblems"] == ["blurredVision", "doubleVision"]
    assert motive["functionalSigns"] == ["photophobia", "headache", "eyeStrain"]


async def test_invalid_checklist_value_is_rejected(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/intake",
        json={"status": "draft", "motive": {"visualProblems": ["notAProblem"]}},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation.error"


async def test_all_sections_are_representable(api_client: AsyncClient) -> None:
    payload = {
        "status": "draft",
        "individualInfo": {"name": "Full Sections", "profession": "Teacher"},
        "motive": {"reasonForVisit": "Check-up"},
        "themes": {"onset": "progressive", "timing": "Started last month"},
        "refractionHistory": {
            "eyeglasses": {"wears": True, "brand": "Ray-Ban"},
            "contactLenses": {"wears": False},
            "overallPreference": "eyeglasses",
        },
        "antecedents": {
            "ocularHistory": {"surgery": "None"},
            "generalHealth": {"diabetes": False, "hypertension": True},
            "medication": "Amlodipine",
            "familyHistory": {"refractive": "Myopia", "relationship": "Mother"},
        },
    }

    response = await api_client.post("/api/v1/intake", json=payload)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["themes"]["onset"] == "progressive"
    assert data["refractionHistory"]["eyeglasses"]["wears"] is True
    assert data["antecedents"]["generalHealth"]["hypertension"] is True


async def test_draft_can_be_saved_then_completed(api_client: AsyncClient) -> None:
    created = await api_client.post(
        "/api/v1/intake",
        json={"status": "draft", "individualInfo": {"name": "Later Complete"}},
    )
    intake_id = created.json()["data"]["id"]

    completed = await api_client.patch(
        f"/api/v1/intake/{intake_id}",
        json={
            "status": "completed",
            "individualInfo": _COMPLETE_INDIVIDUAL,
            "motive": {"reasonForVisit": "Eye strain"},
        },
    )

    assert completed.status_code == 200
    assert completed.json()["data"]["status"] == "completed"


async def test_completing_incomplete_draft_is_rejected(api_client: AsyncClient) -> None:
    created = await api_client.post(
        "/api/v1/intake",
        json={"status": "draft", "individualInfo": {"name": "Still Missing"}},
    )
    intake_id = created.json()["data"]["id"]

    response = await api_client.patch(
        f"/api/v1/intake/{intake_id}", json={"status": "completed"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation.error"


async def test_get_unknown_intake_returns_not_found(api_client: AsyncClient) -> None:
    response = await api_client.get(
        "/api/v1/intake/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"


async def test_list_filters_by_status(api_client: AsyncClient) -> None:
    await api_client.post(
        "/api/v1/intake",
        json={"status": "draft", "individualInfo": {"name": "Draft One"}},
    )
    await api_client.post(
        "/api/v1/intake",
        json={
            "status": "completed",
            "individualInfo": _COMPLETE_INDIVIDUAL,
            "motive": {"reasonForVisit": "Routine"},
        },
    )

    drafts = await api_client.get("/api/v1/intake", params={"status": "draft"})
    completed = await api_client.get("/api/v1/intake", params={"status": "completed"})

    assert all(item["status"] == "draft" for item in drafts.json()["data"])
    assert all(item["status"] == "completed" for item in completed.json()["data"])
    assert len(completed.json()["data"]) == 1


async def test_intake_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/intake")

    assert response.status_code == 401
