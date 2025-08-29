-- Education sessions table for pedagogical workflows
create table if not exists education_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  topic text not null,
  process_type text not null,
  steps jsonb not null default '[]'::jsonb,
  current_index integer not null default 0,
  history jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Helpful indexes
create index if not exists idx_education_sessions_user on education_sessions(user_id);
create index if not exists idx_education_sessions_updated on education_sessions(updated_at desc);

-- Trigger to auto-update updated_at
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_education_sessions_updated_at on education_sessions;
create trigger trg_education_sessions_updated_at
before update on education_sessions
for each row
execute function set_updated_at();

