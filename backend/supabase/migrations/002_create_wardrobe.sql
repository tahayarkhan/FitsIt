create table public.wardrobe (
  id uuid primary key default gen_random_uuid(),
  top_id uuid not null references public.clothing_items (id) on delete cascade,
  bottom_id uuid not null references public.clothing_items (id) on delete cascade,
  shoes_id uuid not null references public.clothing_items (id) on delete cascade,
  outerwear_id uuid references public.clothing_items (id) on delete cascade,
  score numeric not null,
  components jsonb not null default '{}',
  reasons jsonb not null default '[]',
  confidence text not null check (confidence in ('high', 'medium', 'low')),
  created_at timestamptz not null default now()
);

-- Postgres table-level UNIQUE constraints cannot use expressions (e.g. COALESCE).
-- A unique index preserves the intended semantics: treat NULL outerwear_id as one value.
create unique index wardrobe_unique_outfit_combo_idx
  on public.wardrobe (
    top_id,
    bottom_id,
    shoes_id,
    coalesce(outerwear_id, '00000000-0000-0000-0000-000000000000'::uuid)
  );


ALTER TABLE public.wardrobe ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT ON public.wardrobe TO anon, authenticated, service_role;
