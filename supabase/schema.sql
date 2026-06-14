-- GraphMind Studio: Supabase/PostgreSQL schema
-- Run this file in the Supabase SQL Editor before enabling BACKEND_MODE=supabase.

create extension if not exists vector with schema extensions;

create table if not exists workspaces (
  id text primary key,
  name text not null,
  description text,
  scenario text,
  source_scenario text,
  parent_workspace_id text,
  created_at timestamptz default now()
);

-- Safe upgrades for projects created with an earlier GraphMind schema.
alter table workspaces add column if not exists source_scenario text;
alter table workspaces add column if not exists parent_workspace_id text;

create table if not exists messages (
  id text primary key,
  workspace_id text not null references workspaces(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz default now()
);

create table if not exists memories (
  id text primary key,
  workspace_id text not null references workspaces(id) on delete cascade,
  memory_type text not null,
  subject text not null,
  relation text not null,
  object text not null,
  evidence text,
  confidence float default 0.8,
  importance float default 0.7,
  status text default 'active',
  mention_count integer default 1,
  first_seen_at timestamptz default now(),
  last_seen_at timestamptz default now(),
  source_message_id text,
  embedding extensions.vector(1536)
);

create index if not exists memories_workspace_idx on memories(workspace_id);
create index if not exists memories_subject_idx on memories(subject);
create index if not exists memories_relation_idx on memories(relation);
create index if not exists memories_status_idx on memories(status);
create index if not exists messages_workspace_idx on messages(workspace_id);

create table if not exists traces (
  id text primary key,
  workspace_id text not null references workspaces(id) on delete cascade,
  query text not null,
  payload jsonb not null,
  created_at timestamptz default now()
);

create index if not exists traces_workspace_idx on traces(workspace_id);

-- Optional RPC for a future fully vector-backed retrieval path.
-- The current project includes an inspectable local lexical similarity fallback,
-- while this function is ready for OpenAI embeddings stored in memories.embedding.
alter table workspaces enable row level security;
alter table messages enable row level security;
alter table memories enable row level security;
alter table traces enable row level security;

create or replace function match_memories(
  query_embedding extensions.vector(1536),
  match_workspace text,
  match_count integer default 12
)
returns table (
  id text,
  memory_type text,
  subject text,
  relation text,
  object text,
  evidence text,
  confidence float,
  importance float,
  status text,
  similarity float
)
language sql stable
as $$
  select
    m.id,
    m.memory_type,
    m.subject,
    m.relation,
    m.object,
    m.evidence,
    m.confidence,
    m.importance,
    m.status,
    1 - (m.embedding <=> query_embedding) as similarity
  from memories m
  where m.workspace_id = match_workspace
    and m.status in ('active', 'confirmed')
    and m.embedding is not null
  order by m.embedding <=> query_embedding
  limit match_count;
$$;
