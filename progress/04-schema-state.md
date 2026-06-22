# Schema State

Schema source note: the repo did not contain the referenced project-plan Database Schema section, so the migration below is a reconstructed PostgreSQL/Supabase baseline from the requested table list, FK/cascade expectations, and explicit task constraints.

Deviations recorded from the original plan request:
- `dataset_columns.name` + `dataset_columns.display_name` split added. Rationale: raw CSV headers must never flow directly into SQL compilation or LLM prompts.
- `workspaces.is_anonymous` + `workspaces.expires_at` added. Rationale: anonymous workspaces need explicit lifecycle and TTL tracking.
- Migration `0003_cleanup.sql` adds `cleanup_expired_anonymous_workspaces()`. Rationale: deployment can schedule cleanup later, but the database needs a callable primitive now for deleting expired anonymous workspaces and cascading child rows.

2026-06-21 update:
- `0003_cleanup.sql` is the migration that defines anonymous-workspace cleanup behavior.
- `cleanup_expired_anonymous_workspaces()` is the callable SQL function name for deleting expired anonymous workspaces and letting existing FK cascades remove dependent rows.
- 2026-06-21 RLS verification update: live JWT-based isolation testing exposed a recursion bug in the public-demo RLS helper path. `datasets.public_demo_read` calls `is_public_demo_workspace(workspace_id)`, and the original helper queried `workspaces` without `SECURITY DEFINER`, which re-entered `workspaces.public_demo_read` and produced a `500` instead of allowing anonymous demo reads.
- `0004_rls_fix.sql` replaces `owns_workspace()` and `is_public_demo_workspace()` as `SECURITY DEFINER` helpers with `search_path = public` so child-table RLS checks can safely inspect `workspaces` without recursive policy re-entry.
- 2026-06-21 verification result: after applying `0004_rls_fix.sql` to the live Supabase project, `test_rls_isolation.py` passed against real JWT-backed sessions. Verified behaviors: User A cannot read User B private rows across datasets/widgets/insights/anomalies/ask_messages, anonymous users can read the public demo dataset, and one anonymous user cannot read another anonymous user's private workspace or uploaded dataset.
- 2026-06-21 profiling update: the `dataset_columns.name` / `display_name` split is now populated by real code, not just the schema. `schema_inference.py` slugifies raw CSV headers into safe internal names, and `profiler.py` preserves the original header in `display_name` while de-duplicating collisions for `name`.
- 2026-06-22 security update: live verification exposed that anonymous owners could still read their own expired TTL workspaces until cleanup ran. `0005_anon_expiry_rls.sql` fixes this by making `owns_workspace()` require `(is_anonymous = false OR expires_at > now())` and by updating `workspaces.workspace_owner_access` to deny expired anonymous workspace rows immediately, even before `cleanup_expired_anonymous_workspaces()` executes.

```sql
create extension if not exists pgcrypto;

create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create table if not exists profiles (
    id uuid primary key references auth.users (id) on delete cascade,
    email text,
    full_name text,
    avatar_url text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists workspaces (
    id uuid primary key default gen_random_uuid(),
    owner_user_id uuid not null references auth.users (id) on delete cascade,
    name text not null,
    slug text not null,
    is_anonymous boolean not null default false,
    expires_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint workspaces_owner_slug_key unique (owner_user_id, slug),
    constraint workspaces_anonymous_expiry_check check (
        (is_anonymous = false) or (expires_at is not null)
    )
);

create table if not exists datasets (
    id uuid primary key default gen_random_uuid(),
    workspace_id uuid not null references workspaces (id) on delete cascade,
    created_by uuid not null references auth.users (id) on delete cascade,
    name text not null,
    description text,
    source_type text not null default 'upload',
    storage_bucket text not null default 'datasets',
    storage_path text not null unique,
    file_size_bytes bigint not null default 0,
    row_count bigint not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint datasets_source_type_check check (
        source_type in ('upload', 'demo_seed')
    ),
    constraint datasets_file_size_bytes_check check (file_size_bytes >= 0),
    constraint datasets_row_count_check check (row_count >= 0)
);

create table if not exists dataset_columns (
    id uuid primary key default gen_random_uuid(),
    dataset_id uuid not null references datasets (id) on delete cascade,
    name text not null,
    display_name text,
    data_type text not null,
    ordinal_position integer not null,
    is_nullable boolean not null default true,
    semantic_role text,
    sample_values jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    constraint dataset_columns_dataset_name_key unique (dataset_id, name),
    constraint dataset_columns_dataset_ordinal_key unique (dataset_id, ordinal_position),
    constraint dataset_columns_ordinal_position_check check (ordinal_position > 0)
);

create table if not exists ask_sessions (
    id uuid primary key default gen_random_uuid(),
    workspace_id uuid not null references workspaces (id) on delete cascade,
    dataset_id uuid references datasets (id) on delete set null,
    created_by uuid not null references auth.users (id) on delete cascade,
    title text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists ask_messages (
    id uuid primary key default gen_random_uuid(),
    session_id uuid not null references ask_sessions (id) on delete cascade,
    role text not null,
    content text not null,
    sql_text text,
    chart_spec jsonb,
    created_at timestamptz not null default now(),
    constraint ask_messages_role_check check (role in ('system', 'user', 'assistant'))
);

create table if not exists dashboards (
    id uuid primary key default gen_random_uuid(),
    workspace_id uuid not null references workspaces (id) on delete cascade,
    created_by uuid not null references auth.users (id) on delete cascade,
    name text not null,
    description text,
    layout jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists widgets (
    id uuid primary key default gen_random_uuid(),
    dashboard_id uuid not null references dashboards (id) on delete cascade,
    dataset_id uuid references datasets (id) on delete set null,
    title text not null,
    widget_type text not null,
    query_text text,
    config jsonb not null default '{}'::jsonb,
    position integer not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint widgets_widget_type_check check (
        widget_type in ('metric', 'table', 'bar', 'line', 'pie', 'area', 'scatter')
    ),
    constraint widgets_position_check check (position >= 0)
);

create table if not exists insights (
    id uuid primary key default gen_random_uuid(),
    workspace_id uuid not null references workspaces (id) on delete cascade,
    dataset_id uuid references datasets (id) on delete set null,
    title text not null,
    body text not null,
    insight_type text not null,
    severity text not null default 'info',
    score numeric(5,4),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    constraint insights_insight_type_check check (
        insight_type in ('summary', 'trend', 'distribution', 'outlier')
    ),
    constraint insights_severity_check check (
        severity in ('info', 'warning', 'critical')
    ),
    constraint insights_score_check check (
        score is null or (score >= 0 and score <= 1)
    )
);

create table if not exists anomalies (
    id uuid primary key default gen_random_uuid(),
    workspace_id uuid not null references workspaces (id) on delete cascade,
    dataset_id uuid references datasets (id) on delete set null,
    detector_type text not null,
    metric_name text,
    severity text not null default 'warning',
    explanation text,
    anomaly_payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    constraint anomalies_detector_type_check check (
        detector_type in ('zscore', 'isolation_forest')
    ),
    constraint anomalies_severity_check check (
        severity in ('info', 'warning', 'critical')
    )
);
```
