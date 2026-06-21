create or replace function cleanup_expired_anonymous_workspaces()
returns integer
language plpgsql
as $$
declare
    deleted_count integer;
begin
    with deleted_rows as (
        delete from workspaces
        where is_anonymous = true
          and expires_at is not null
          and expires_at < now()
        returning 1
    )
    select count(*) into deleted_count
    from deleted_rows;

    return deleted_count;
end;
$$;
