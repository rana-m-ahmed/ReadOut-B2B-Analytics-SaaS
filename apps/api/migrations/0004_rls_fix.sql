create or replace function owns_workspace(target_workspace_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
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
security definer
set search_path = public
as $$
    select exists (
        select 1
        from workspaces
        where id = target_workspace_id
          and slug = 'demo'
          and is_anonymous = false
    );
$$;
