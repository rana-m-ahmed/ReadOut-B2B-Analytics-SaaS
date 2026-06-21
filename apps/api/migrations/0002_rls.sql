create or replace function owns_workspace(target_workspace_id uuid)
returns boolean
language sql
stable
as $$
    select exists (
        select 1
        from workspaces
        where id = target_workspace_id
          and owner_user_id = auth.uid()
    );
$$;

create or replace function is_public_demo_workspace(target_workspace_id uuid)
returns boolean
language sql
stable
as $$
    select exists (
        select 1
        from workspaces
        where id = target_workspace_id
          and slug = 'demo'
          and is_anonymous = false
    );
$$;

alter table profiles enable row level security;
alter table workspaces enable row level security;
alter table datasets enable row level security;
alter table dataset_columns enable row level security;
alter table ask_sessions enable row level security;
alter table ask_messages enable row level security;
alter table dashboards enable row level security;
alter table widgets enable row level security;
alter table insights enable row level security;
alter table anomalies enable row level security;

drop policy if exists profiles_self_access on profiles;
create policy profiles_self_access
on profiles
for all
to authenticated
using (id = auth.uid())
with check (id = auth.uid());

drop policy if exists workspace_owner_access on workspaces;
create policy workspace_owner_access
on workspaces
for all
to authenticated
using (owner_user_id = auth.uid())
with check (owner_user_id = auth.uid());

drop policy if exists public_demo_read on workspaces;
create policy public_demo_read
on workspaces
for select
to authenticated
using (is_public_demo_workspace(id));

drop policy if exists datasets_owner_access on datasets;
create policy datasets_owner_access
on datasets
for all
to authenticated
using (owns_workspace(workspace_id))
with check (owns_workspace(workspace_id));

drop policy if exists public_demo_read on datasets;
create policy public_demo_read
on datasets
for select
to authenticated
using (is_public_demo_workspace(workspace_id));

drop policy if exists dataset_columns_owner_access on dataset_columns;
create policy dataset_columns_owner_access
on dataset_columns
for all
to authenticated
using (
    exists (
        select 1
        from datasets
        where datasets.id = dataset_columns.dataset_id
          and owns_workspace(datasets.workspace_id)
    )
)
with check (
    exists (
        select 1
        from datasets
        where datasets.id = dataset_columns.dataset_id
          and owns_workspace(datasets.workspace_id)
    )
);

drop policy if exists public_demo_read on dataset_columns;
create policy public_demo_read
on dataset_columns
for select
to authenticated
using (
    exists (
        select 1
        from datasets
        where datasets.id = dataset_columns.dataset_id
          and is_public_demo_workspace(datasets.workspace_id)
    )
);

drop policy if exists ask_sessions_owner_access on ask_sessions;
create policy ask_sessions_owner_access
on ask_sessions
for all
to authenticated
using (owns_workspace(workspace_id))
with check (owns_workspace(workspace_id));

drop policy if exists public_demo_read on ask_sessions;
create policy public_demo_read
on ask_sessions
for select
to authenticated
using (is_public_demo_workspace(workspace_id));

drop policy if exists ask_messages_owner_access on ask_messages;
create policy ask_messages_owner_access
on ask_messages
for all
to authenticated
using (
    exists (
        select 1
        from ask_sessions
        where ask_sessions.id = ask_messages.session_id
          and owns_workspace(ask_sessions.workspace_id)
    )
)
with check (
    exists (
        select 1
        from ask_sessions
        where ask_sessions.id = ask_messages.session_id
          and owns_workspace(ask_sessions.workspace_id)
    )
);

drop policy if exists public_demo_read on ask_messages;
create policy public_demo_read
on ask_messages
for select
to authenticated
using (
    exists (
        select 1
        from ask_sessions
        where ask_sessions.id = ask_messages.session_id
          and is_public_demo_workspace(ask_sessions.workspace_id)
    )
);

drop policy if exists dashboards_owner_access on dashboards;
create policy dashboards_owner_access
on dashboards
for all
to authenticated
using (owns_workspace(workspace_id))
with check (owns_workspace(workspace_id));

drop policy if exists public_demo_read on dashboards;
create policy public_demo_read
on dashboards
for select
to authenticated
using (is_public_demo_workspace(workspace_id));

drop policy if exists widgets_owner_access on widgets;
create policy widgets_owner_access
on widgets
for all
to authenticated
using (
    exists (
        select 1
        from dashboards
        where dashboards.id = widgets.dashboard_id
          and owns_workspace(dashboards.workspace_id)
    )
)
with check (
    exists (
        select 1
        from dashboards
        where dashboards.id = widgets.dashboard_id
          and owns_workspace(dashboards.workspace_id)
    )
);

drop policy if exists public_demo_read on widgets;
create policy public_demo_read
on widgets
for select
to authenticated
using (
    exists (
        select 1
        from dashboards
        where dashboards.id = widgets.dashboard_id
          and is_public_demo_workspace(dashboards.workspace_id)
    )
);

drop policy if exists insights_owner_access on insights;
create policy insights_owner_access
on insights
for all
to authenticated
using (owns_workspace(workspace_id))
with check (owns_workspace(workspace_id));

drop policy if exists public_demo_read on insights;
create policy public_demo_read
on insights
for select
to authenticated
using (is_public_demo_workspace(workspace_id));

drop policy if exists anomalies_owner_access on anomalies;
create policy anomalies_owner_access
on anomalies
for all
to authenticated
using (owns_workspace(workspace_id))
with check (owns_workspace(workspace_id));

drop policy if exists public_demo_read on anomalies;
create policy public_demo_read
on anomalies
for select
to authenticated
using (is_public_demo_workspace(workspace_id));
