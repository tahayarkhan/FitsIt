-- Enable pgcrypto for gen_random_uuid() (Supabase-compatible, idempotent).
create extension if not exists pgcrypto with schema extensions;
