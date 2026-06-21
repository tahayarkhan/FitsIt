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


CREATE UNIQUE INDEX recommendations_unique_outfit
ON public.recommendations (
    top_id,
    bottom_id,
    shoes_id,
    COALESCE(outerwear_id, '00000000-0000-0000-0000-000000000000')
);

ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT ON public.recommendations TO anon, authenticated, service_role;
