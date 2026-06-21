"""Repository-to-RLS policy cross-reference.

The actual enforcement lives in `apps/api/migrations/0002_rls.sql`.
This module is intentionally thin documentation so repository edits stay paired
with the matching database policy assumptions.
"""

from __future__ import annotations


class RepositoryRLSNotes:
    """Cross-reference notes for repository methods and their backing RLS policies."""

    profiles = "ProfileRepository relies on `profiles_self_access` in 0002_rls.sql."
    workspaces = (
        "WorkspaceRepository create/read/update/delete methods rely on "
        "`workspace_owner_access`; anonymous users still own their throwaway "
        "workspace via auth.uid() ownership, while shared demo visibility comes "
        "from the workspaces-table `public_demo_read` select policy."
    )
    datasets = (
        "DatasetRepository workspace-scoped CRUD relies on `datasets_owner_access`; "
        "`get_demo_dataset()` relies on the datasets-table `public_demo_read` "
        "policy joined through the seeded demo workspace."
    )
    dataset_columns = (
        "DatasetColumnRepository relies on `dataset_columns_owner_access` for "
        "workspace-owned data and `public_demo_read` through datasets joins."
    )
    ask_sessions = (
        "AskSessionRepository relies on `ask_sessions_owner_access` plus "
        "`public_demo_read` for seeded demo-session visibility."
    )
    ask_messages = (
        "AskMessageRepository relies on `ask_messages_owner_access` and "
        "`public_demo_read` through ask_sessions joins."
    )
    dashboards = (
        "DashboardRepository relies on `dashboards_owner_access` and "
        "`public_demo_read` for seeded demo dashboards."
    )
    widgets = (
        "WidgetRepository relies on `widgets_owner_access` and "
        "`public_demo_read` through dashboards joins."
    )
    insights = "InsightRepository relies on `insights_owner_access` and `public_demo_read`."
    anomalies = "AnomalyRepository relies on `anomalies_owner_access` and `public_demo_read`."
