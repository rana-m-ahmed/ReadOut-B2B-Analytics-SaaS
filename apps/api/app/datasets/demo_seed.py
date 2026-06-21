"""Demo dataset seeding service."""

from __future__ import annotations

import asyncio
import io
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile

from app.datasets.demo_generation import (
    DEMO_DATASET_FILENAME,
    DEMO_DATASET_SEED,
    generate_demo_dataset,
    write_generation_outputs,
)
from app.datasets.storage_service import DatasetStorageService
from app.datasets.upload_service import DatasetUploadService, UploadResult
from app.db.models import Dataset, DatasetColumnCreate, Workspace, WorkspaceCreate
from app.db.repositories import DatasetColumnRepository, DatasetRepository, WorkspaceRepository
from app.db.supabase_client import get_supabase_client


DEMO_OWNER_EMAIL = "demo-seed-owner@readout.local"
DEMO_OWNER_PASSWORD = "DemoSeedOwner!2026"
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
SCRIPT_OUTPUT_CSV_PATH = SCRIPTS_DIR / DEMO_DATASET_FILENAME
SCRIPT_METADATA_PATH = SCRIPTS_DIR / "demo-dataset-metadata.json"


@dataclass(slots=True)
class DemoSeedResult:
    """Result of provisioning the shared public demo dataset."""

    workspace: Workspace
    dataset: Dataset
    upload_result: UploadResult

    @property
    def status(self) -> str:
        return self.upload_result.status

    @property
    def quality_score(self) -> int | None:
        return self.upload_result.quality_score


class DemoSeedService:
    """Provision the public demo dataset through the same upload pipeline as user CSVs."""

    def __init__(
        self,
        *,
        workspace_repository: WorkspaceRepository | None = None,
        dataset_repository: DatasetRepository | None = None,
        dataset_column_repository: DatasetColumnRepository | None = None,
        upload_service: DatasetUploadService | None = None,
        storage_service: DatasetStorageService | None = None,
    ) -> None:
        self._workspaces = workspace_repository or WorkspaceRepository()
        self._datasets = dataset_repository or DatasetRepository()
        self._columns = dataset_column_repository or DatasetColumnRepository()
        self._storage = storage_service or DatasetStorageService()
        self._upload_service = upload_service or DatasetUploadService(
            dataset_repository=self._datasets,
            storage_service=self._storage,
        )
        self._client = get_supabase_client()

    def seed_demo_dataset(self, *, persist_script_outputs: bool = False) -> DemoSeedResult:
        if persist_script_outputs:
            write_generation_outputs(SCRIPT_OUTPUT_CSV_PATH, SCRIPT_METADATA_PATH, seed=DEMO_DATASET_SEED)
        artifacts = generate_demo_dataset(seed=DEMO_DATASET_SEED)

        demo_owner_id = self._ensure_demo_owner_user_id()
        workspace = self._ensure_demo_workspace(demo_owner_id)
        self._delete_existing_demo_datasets(workspace)

        upload = UploadFile(filename=DEMO_DATASET_FILENAME, file=io.BytesIO(artifacts.csv_bytes))
        upload_result = asyncio.run(
            self._upload_service.upload_dataset(
                workspace_id=workspace.id,
                user_id=demo_owner_id,
                upload=upload,
                description="Shared public demo sales dataset",
                dataset_name="Demo Sales Orders",
                source_type="demo_seed",
            )
        )
        if upload_result.profile:
            for column in upload_result.profile.columns:
                self._columns.create(
                    workspace.id,
                    DatasetColumnCreate(
                        dataset_id=upload_result.dataset.id,
                        name=column.name,
                        display_name=column.display_name,
                        data_type=column.data_type,
                        ordinal_position=column.ordinal_position,
                        is_nullable=column.is_nullable,
                        semantic_role=column.semantic_role,
                        sample_values=column.sample_values,
                    ),
                )

        return DemoSeedResult(
            workspace=workspace,
            dataset=upload_result.dataset,
            upload_result=upload_result,
        )

    def _ensure_demo_owner_user_id(self) -> UUID:
        for user in self._client.auth.admin.list_users():
            if getattr(user, "email", None) == DEMO_OWNER_EMAIL:
                return UUID(user.id)

        response = self._client.auth.admin.create_user(
            {
                "email": DEMO_OWNER_EMAIL,
                "password": DEMO_OWNER_PASSWORD,
                "email_confirm": True,
            }
        )
        return UUID(response.user.id)

    def _ensure_demo_workspace(self, owner_user_id: UUID) -> Workspace:
        for workspace in self._workspaces.list_for_owner(owner_user_id):
            if workspace.slug == "demo":
                return workspace

        return self._workspaces.create(
            owner_user_id,
            WorkspaceCreate(name="Public Demo Workspace", slug="demo"),
        )

    def _delete_existing_demo_datasets(self, workspace: Workspace) -> None:
        for dataset in self._datasets.list_for_workspace(workspace.id):
            if dataset.source_type != "demo_seed":
                continue
            self._storage.remove_dataset_artifacts(workspace.owner_user_id, dataset.id)
            self._datasets.delete(workspace.id, dataset.id)


def seed_demo_dataset(*, persist_script_outputs: bool = False) -> DemoSeedResult:
    """Seed the shared public demo dataset into the live project."""

    return DemoSeedService().seed_demo_dataset(persist_script_outputs=persist_script_outputs)
