create table if not exists public.governor_audit (
  id bigserial primary key,
  request_id text not null,
  request_type text not null,
  status text not null,
  actor_role text,
  payload jsonb,
  response jsonb,
  created_at timestamptz not null default now()
);
