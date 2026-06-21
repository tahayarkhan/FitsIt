create table public.recommendations (
  id uuid primary key default gen_random_uuid(),
  top_id uuid not null references public.clothing_items (id) on delete cascade,
  bottom_id uuid not null references public.clothing_items (id) on delete cascade,
  shoes_id uuid not null references public.clothing_items (id) on delete cascade,
  outerwear_id uuid references public.clothing_items (id) on delete cascade,
  score numeric not null,
  components jsonb not null default '{}',
  reasons jsonb not null default '[]',
  confidence text not null check (confidence in ('high', 'medium', 'low')),
  liked boolean not null default false,
  created_at timestamptz not null default now()
);


create unique index recommendations_unique_outfit_idx
  on public.recommendations (top_id, bottom_id, shoes_id);

ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT ON public.recommendations TO anon, authenticated, service_role;
