import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_list_anomalies_empty(authorized_client: AsyncClient, test_dataset_id: str):
    response = await authorized_client.get(f"/datasets/{test_dataset_id}/anomalies")
    assert response.status_code == 200
    assert response.json() == []

async def test_scan_anomalies_no_dataset(authorized_client: AsyncClient):
    import uuid
    fake_id = str(uuid.uuid4())
    response = await authorized_client.post(f"/datasets/{fake_id}/anomalies/scan")
    assert response.status_code == 404

async def test_dismiss_anomaly_not_found(authorized_client: AsyncClient):
    import uuid
    fake_id = str(uuid.uuid4())
    response = await authorized_client.delete(f"/anomalies/{fake_id}")
    assert response.status_code == 404
