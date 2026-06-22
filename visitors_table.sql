create table if not exists public.visitors (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  session_id text,
  created_at timestamptz default now(),
  last_seen timestamptz default now()
);

grant select, insert, update on public.visitors to anon;

alter table public.visitors enable row level security;

drop policy if exists "Allow public email capture insert" on public.visitors;
drop policy if exists "Allow public email capture update" on public.visitors;
drop policy if exists "Allow public email capture select" on public.visitors;

create policy "Allow public email capture insert"
on public.visitors
for insert
to anon
with check (true);

create policy "Allow public email capture update"
on public.visitors
for update
to anon
using (true)
with check (true);

create policy "Allow public email capture select"
on public.visitors
for select
to anon
using (true);
