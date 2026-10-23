-- WO-2026-005 — READ-ONLY catalog verification
-- Run in the SQL Editor for project jdvlzgljfodltmzvdpld.
-- This script contains SELECT statements only; it does not alter the database.

-- 1) Confirm current database and inspect expected MKA-Core objects.
select current_database() as database_name, current_user as sql_role;

select
  n.nspname as schema_name,
  c.relname as object_name,
  c.relkind as object_kind,
  c.relrowsecurity as rls_enabled,
  c.relforcerowsecurity as force_rls
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname not in ('pg_catalog', 'information_schema')
  and c.relname in ('circulars', 'memory_items', 'memory_links', 'user_roles')
order by n.nspname, c.relname;

-- 2) Enumerate policies on expected objects (including policies that may
-- have been added manually and therefore are absent from migration history).
select schemaname, tablename, policyname, permissive, roles, cmd,
       qual as using_expression, with_check as with_check_expression
from pg_policies
where tablename in ('circulars', 'memory_items', 'memory_links', 'user_roles')
order by schemaname, tablename, policyname;

-- 3) Inspect table grants on expected objects.
select table_schema, table_name, grantee, privilege_type, is_grantable
from information_schema.role_table_grants
where table_schema = 'public'
  and table_name in ('circulars', 'memory_items', 'memory_links', 'user_roles')
order by table_name, grantee, privilege_type;

-- 4) Inspect function identity, security mode, owner and definition.
-- Review output carefully; definitions may contain sensitive implementation details.
select
  n.nspname as schema_name,
  p.proname as function_name,
  pg_get_function_identity_arguments(p.oid) as identity_arguments,
  pg_get_userbyid(p.proowner) as owner_name,
  p.prosecdef as security_definer,
  p.proconfig as function_settings,
  pg_get_function_result(p.oid) as result_type,
  pg_get_functiondef(p.oid) as definition
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.proname in ('search_knowledge', 'has_role')
order by p.proname, identity_arguments;

-- 5) Inspect explicit function EXECUTE grants.
select
  n.nspname as schema_name,
  p.proname as function_name,
  pg_get_function_identity_arguments(p.oid) as identity_arguments,
  coalesce(grantee.rolname, 'PUBLIC') as grantee,
  privilege_type,
  is_grantable
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
cross join lateral aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) acl
left join pg_roles grantee on grantee.oid = acl.grantee
where n.nspname = 'public'
  and p.proname in ('search_knowledge', 'has_role')
  and acl.privilege_type = 'EXECUTE'
order by p.proname, identity_arguments, grantee;

-- 6) Read recorded migration history. This does not detect manual DDL.
select version, name
from supabase_migrations.schema_migrations
order by version desc
limit 50;

-- 7) Inspect columns and constraints for any existing memory/knowledge objects.
select table_schema, table_name, column_name, data_type, is_nullable, column_default
from information_schema.columns
where table_schema not in ('pg_catalog', 'information_schema')
  and table_name in ('circulars', 'memory_items', 'memory_links', 'user_roles')
order by table_schema, table_name, ordinal_position;
