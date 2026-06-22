from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[4]
MIGRATIONS_DIR = REPO_ROOT / "apps" / "api" / "migrations"
INIT_MIGRATION = MIGRATIONS_DIR / "0001_init.sql"
RLS_MIGRATION = MIGRATIONS_DIR / "0002_rls.sql"
CLEANUP_MIGRATION = MIGRATIONS_DIR / "0003_cleanup.sql"
RLS_FIX_MIGRATION = MIGRATIONS_DIR / "0004_rls_fix.sql"
ANON_EXPIRY_RLS_MIGRATION = MIGRATIONS_DIR / "0005_anon_expiry_rls.sql"


def test_migrations_apply_cleanly_and_enforce_source_type_constraint() -> None:
    database_url = os.getenv("READOUT_TEST_DATABASE_URL")
    psql_path = shutil.which("psql")

    if not database_url or not psql_path:
        pytest.skip(
            "requires READOUT_TEST_DATABASE_URL and psql to apply migrations against "
            "a throwaway PostgreSQL or Supabase-local database"
        )

    schema_name = f"mig_{uuid.uuid4().hex[:8]}"
    sql_script = f"""
    create extension if not exists pgcrypto;
    create schema if not exists auth;
    create table if not exists auth.users (
        id uuid primary key
    );
    create or replace function auth.uid()
    returns uuid
    language sql
    stable
    as $$
        select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
    $$;

    do $$
    begin
        create role authenticated nologin;
    exception
        when duplicate_object then
            null;
    end
    $$;

    create schema {schema_name};
    set search_path to {schema_name}, public;

    {INIT_MIGRATION.read_text(encoding='utf-8')}

    {RLS_MIGRATION.read_text(encoding='utf-8')}

    {CLEANUP_MIGRATION.read_text(encoding='utf-8')}

    {RLS_FIX_MIGRATION.read_text(encoding='utf-8')}

    {ANON_EXPIRY_RLS_MIGRATION.read_text(encoding='utf-8')}

    insert into auth.users (id)
    values ('00000000-0000-0000-0000-000000000001');

    insert into profiles (id, email, full_name)
    values ('00000000-0000-0000-0000-000000000001', 'owner@example.com', 'Owner User');

    insert into workspaces (id, owner_user_id, name, slug)
    values (
        '10000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000001',
        'Owner Workspace',
        'owner-workspace'
    );

    insert into datasets (
        id,
        workspace_id,
        created_by,
        name,
        source_type,
        storage_path
    )
    values (
        '20000000-0000-0000-0000-000000000001',
        '10000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000001',
        'Sales Dataset',
        'upload',
        'datasets/10000000-0000-0000-0000-000000000001/sales.csv'
    );

    insert into dataset_columns (
        id,
        dataset_id,
        name,
        display_name,
        data_type,
        ordinal_position
    )
    values (
        '30000000-0000-0000-0000-000000000001',
        '20000000-0000-0000-0000-000000000001',
        'total_revenue',
        'Total Revenue ($)',
        'numeric',
        1
    );

    do $$
    begin
        begin
            insert into datasets (
                workspace_id,
                created_by,
                name,
                source_type,
                storage_path
            )
            values (
                '10000000-0000-0000-0000-000000000001',
                '00000000-0000-0000-0000-000000000001',
                'Bad Dataset',
                'invalid_source',
                'datasets/10000000-0000-0000-0000-000000000001/bad.csv'
            );
            raise exception 'expected datasets_source_type_check to reject invalid source_type';
        exception
            when check_violation then
                null;
        end;
    end
    $$;

    insert into workspaces (
        id,
        owner_user_id,
        name,
        slug,
        is_anonymous,
        expires_at
    )
    values (
        '10000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000001',
        'Expired Anonymous Workspace',
        'expired-anon-workspace',
        true,
        now() - interval '1 hour'
    );

    set role authenticated;
    set request.jwt.claim.sub = '00000000-0000-0000-0000-000000000001';

    do $$
    declare
        visible_count integer;
    begin
        select count(*) into visible_count
        from workspaces
        where id = '10000000-0000-0000-0000-000000000002';

        if visible_count <> 0 then
            raise exception 'expected expired anonymous workspace to be hidden immediately by RLS';
        end if;
    end
    $$;
    """

    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False, encoding="utf-8") as handle:
        handle.write(sql_script)
        script_path = Path(handle.name)

    try:
        result = subprocess.run(
            [psql_path, database_url, "-v", "ON_ERROR_STOP=1", "-f", str(script_path)],
            check=False,
            capture_output=True,
            text=True,
        )
    finally:
        script_path.unlink(missing_ok=True)

    assert result.returncode == 0, result.stderr or result.stdout
