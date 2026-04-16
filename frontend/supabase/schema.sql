create table if not exists public.user_profiles (
  id bigint generated always as identity primary key,
  user_id uuid unique,
  email text unique not null,
  name text,
  auth_mode text,
  updated_at timestamptz default now()
);

create table if not exists public.delivery_issues (
  id bigint generated always as identity primary key,
  user_id uuid,
  worker_id text not null,
  disruption_type text not null,
  severity int not null,
  description text not null,
  latitude double precision,
  longitude double precision,
  location_source text,
  location_accuracy double precision,
  reporter_email text,
  backend_message text,
  triggered boolean default false,
  payout_amount numeric(10,2) default 0,
  created_at timestamptz default now()
);

alter table public.delivery_issues add column if not exists latitude double precision;
alter table public.delivery_issues add column if not exists longitude double precision;
alter table public.delivery_issues add column if not exists location_source text;
alter table public.delivery_issues add column if not exists location_accuracy double precision;
alter table public.user_profiles add column if not exists user_id uuid unique;
alter table public.delivery_issues add column if not exists user_id uuid;

alter table public.user_profiles
  add constraint user_profiles_user_id_fkey
  foreign key (user_id)
  references auth.users(id)
  on delete cascade;

alter table public.delivery_issues
  add constraint delivery_issues_user_id_fkey
  foreign key (user_id)
  references auth.users(id)
  on delete cascade;

alter table public.user_profiles enable row level security;
alter table public.delivery_issues enable row level security;

drop policy if exists "allow anon upsert user_profiles" on public.user_profiles;
drop policy if exists "user manages own profile" on public.user_profiles;
create policy "user manages own profile"
on public.user_profiles
for all
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "user inserts own delivery issues" on public.delivery_issues;
create policy "user inserts own delivery issues"
on public.delivery_issues
for insert
to authenticated
with check (auth.uid() = user_id);

drop policy if exists "user reads own delivery issues" on public.delivery_issues;
create policy "user reads own delivery issues"
on public.delivery_issues
for select
to authenticated
using (auth.uid() = user_id);
