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

comment on column dataset_columns.name is 'Safe internal column name: snake_case, sanitized, deduplicated, and never a reserved word.';
comment on column dataset_columns.display_name is 'Original CSV header shown in the UI only; never sent directly to SQL compilation or LLM prompts.';

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

create index if not exists idx_workspaces_owner_user_id on workspaces (owner_user_id);
create index if not exists idx_datasets_workspace_id on datasets (workspace_id);
create index if not exists idx_dataset_columns_dataset_id on dataset_columns (dataset_id);
create index if not exists idx_ask_sessions_workspace_id on ask_sessions (workspace_id);
create index if not exists idx_ask_messages_session_id on ask_messages (session_id);
create index if not exists idx_dashboards_workspace_id on dashboards (workspace_id);
create index if not exists idx_widgets_dashboard_id on widgets (dashboard_id);
create index if not exists idx_insights_workspace_id on insights (workspace_id);
create index if not exists idx_anomalies_workspace_id on anomalies (workspace_id);

drop trigger if exists set_profiles_updated_at on profiles;
create trigger set_profiles_updated_at
before update on profiles
for each row
execute function set_updated_at();

drop trigger if exists set_workspaces_updated_at on workspaces;
create trigger set_workspaces_updated_at
before update on workspaces
for each row
execute function set_updated_at();

drop trigger if exists set_datasets_updated_at on datasets;
create trigger set_datasets_updated_at
before update on datasets
for each row
execute function set_updated_at();

drop trigger if exists set_ask_sessions_updated_at on ask_sessions;
create trigger set_ask_sessions_updated_at
before update on ask_sessions
for each row
execute function set_updated_at();

drop trigger if exists set_dashboards_updated_at on dashboards;
create trigger set_dashboards_updated_at
before update on dashboards
for each row
execute function set_updated_at();

drop trigger if exists set_widgets_updated_at on widgets;
create trigger set_widgets_updated_at
before update on widgets
for each row
execute function set_updated_at();
