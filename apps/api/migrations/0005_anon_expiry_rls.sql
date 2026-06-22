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
          and (
              is_anonymous = false
              or expires_at > now()
          )
    );
$$;


drop policy if exists workspace_owner_access on workspaces;
create policy workspace_owner_access
on workspaces
for all
to authenticated
using (
    owner_user_id = auth.uid()
    and (
        is_anonymous = false
        or expires_at > now()
    )
)
with check (
    owner_user_id = auth.uid()
    and (
        is_anonymous = false
        or expires_at > now()
    )
);
