create table public.clothing_items (
  id uuid primary key default gen_random_uuid(),
  image_url text not null,
  storage_path text not null,
  category text check (category in ('top', 'bottom', 'shoes', 'outerwear', 'other')),
  primary_color jsonb,
  secondary_color jsonb,
  dominant_rgb jsonb,
  created_at timestamp default now()
);

ALTER TABLE public.clothing_items ENABLE ROW LEVEL SECURITY;

GRANT SELECT, INSERT ON public.clothing_items TO anon, authenticated, service_role;
