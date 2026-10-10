-- 1. Create profiles table
create table public.profiles (
  id uuid not null references auth.users on delete cascade,
  full_name text,
  avatar_url text,
  skin_type text,
  language text,
  location text,
  updated_at timestamp with time zone,

  primary key (id)
);

-- Enable RLS for profiles
alter table public.profiles enable row level security;

create policy "Public profiles are viewable by everyone."
  on profiles for select
  using ( true );

create policy "Users can insert their own profile."
  on profiles for insert
  with check ( auth.uid() = id );

create policy "Users can update own profile."
  on profiles for update
  using ( auth.uid() = id );

-- 2. Create a trigger to automatically create a profile for a new user
create function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, full_name, avatar_url)
  values (new.id, new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'avatar_url');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- 3. Create scan_results table
create table public.scan_results (
  id uuid default gen_random_uuid() primary key,
  user_id uuid not null references auth.users on delete cascade,
  image_url text not null,
  top_prediction text not null,
  confidence numeric not null,
  all_predictions jsonb,
  patient_explanation text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS for scan_results
alter table public.scan_results enable row level security;

create policy "Users can view their own scan results."
  on scan_results for select
  using ( auth.uid() = user_id );

create policy "Users can insert their own scan results."
  on scan_results for insert
  with check ( auth.uid() = user_id );

create policy "Users can update their own scan results."
  on scan_results for update
  using ( auth.uid() = user_id );

create policy "Users can delete their own scan results."
  on scan_results for delete
  using ( auth.uid() = user_id );

-- 4. Create scan-images Storage Bucket
insert into storage.buckets (id, name, public) 
values ('scan-images', 'scan-images', true);

-- Enable RLS for storage bucket
create policy "Anyone can view scan images."
  on storage.objects for select
  using ( bucket_id = 'scan-images' );

create policy "Authenticated users can upload scan images."
  on storage.objects for insert
  with check ( bucket_id = 'scan-images' and auth.role() = 'authenticated' );

create policy "Users can update their own scan images."
  on storage.objects for update
  using ( bucket_id = 'scan-images' and auth.uid() = owner );

create policy "Users can delete their own scan images."
  on storage.objects for delete
  using ( bucket_id = 'scan-images' and auth.uid() = owner );
