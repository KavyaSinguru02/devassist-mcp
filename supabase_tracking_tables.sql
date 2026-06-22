create table if not exists tool_usage (
  id uuid primary key default gen_random_uuid(),
  tool_name text not null,
  created_at timestamptz default now()
);

create table if not exists feedback (
  id uuid primary key default gen_random_uuid(),
  tool_name text not null,
  vote text not null check (vote in ('up', 'down')),
  created_at timestamptz default now()
);

create table if not exists repository_cache (
  id uuid primary key default gen_random_uuid(),
  repo_url text unique not null,
  repo_name text,
  overview text,
  frameworks jsonb,
  architecture text,
  last_commit text,
  updated_at timestamptz default now()
);

grant select, insert, update on public.tool_usage to anon;
grant select, insert, update on public.feedback to anon;
grant select, insert, update on public.repository_cache to anon;

alter table public.tool_usage enable row level security;
alter table public.feedback enable row level security;
alter table public.repository_cache enable row level security;

drop policy if exists "Allow public tool usage insert" on public.tool_usage;
drop policy if exists "Allow public tool usage read" on public.tool_usage;
drop policy if exists "Allow public feedback insert" on public.feedback;
drop policy if exists "Allow public feedback read" on public.feedback;
drop policy if exists "Allow repository cache insert" on public.repository_cache;
drop policy if exists "Allow repository cache update" on public.repository_cache;
drop policy if exists "Allow repository cache read" on public.repository_cache;

create policy "Allow public tool usage insert"
on public.tool_usage for insert to anon with check (true);

create policy "Allow public tool usage read"
on public.tool_usage for select to anon using (true);

create policy "Allow public feedback insert"
on public.feedback for insert to anon with check (true);

create policy "Allow public feedback read"
on public.feedback for select to anon using (true);

create policy "Allow repository cache insert"
on public.repository_cache for insert to anon with check (true);

create policy "Allow repository cache update"
on public.repository_cache for update to anon using (true) with check (true);

create policy "Allow repository cache read"
on public.repository_cache for select to anon using (true);
