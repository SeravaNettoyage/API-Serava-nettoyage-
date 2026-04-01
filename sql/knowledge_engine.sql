create extension if not exists pgcrypto;

create table if not exists public.books (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  author text,
  source_type text not null,
  filename text not null,
  language text default 'fr',
  status text not null default 'uploaded',
  import_notes text,
  created_at timestamptz not null default now()
);

create table if not exists public.book_chunks (
  id uuid primary key default gen_random_uuid(),
  book_id uuid not null references public.books(id) on delete cascade,
  title text,
  chapter text,
  section text,
  page_start integer,
  page_end integer,
  chunk_index integer not null,
  content text not null,
  content_type text,
  keywords jsonb not null default '[]'::jsonb,
  embedding jsonb,
  source_ref text,
  created_at timestamptz not null default now()
);

create index if not exists idx_book_chunks_book_id on public.book_chunks(book_id);
create index if not exists idx_book_chunks_chunk_index on public.book_chunks(book_id, chunk_index);

create table if not exists public.knowledge_rules (
  id uuid primary key default gen_random_uuid(),
  book_id uuid not null references public.books(id) on delete cascade,
  source_chunk_id uuid not null references public.book_chunks(id) on delete cascade,
  rule_type text not null,
  surface text,
  fiber text,
  stain_type text,
  product text,
  equipment text,
  procedure_steps jsonb not null default '[]'::jsonb,
  dwell_time text,
  water_temp text,
  agitation_level text,
  risk text,
  forbidden_action text,
  safety_notes text,
  expected_result text,
  confidence_score numeric(4,3),
  source_quote text,
  created_at timestamptz not null default now()
);

create index if not exists idx_knowledge_rules_book_id on public.knowledge_rules(book_id);
create index if not exists idx_knowledge_rules_rule_type on public.knowledge_rules(rule_type);
