import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_list_insights_empty(authorized_client: AsyncClient, test_dataset_id: str):
    response = await authorized_client.get(f"/datasets/{test_dataset_id}/insights")
    assert response.status_code == 200
    assert response.json() == []

# The generate endpoint requires scanning which requires valid dataset columns and data, 
# so we only test that it requires auth and dataset exists.
async def test_generate_insights_no_dataset(authorized_client: AsyncClient):
    import uuid
    fake_id = str(uuid.uuid4())
    response = await authorized_client.post(f"/datasets/{fake_id}/insights/generate")
    assert response.status_code == 404
