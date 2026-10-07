-- Esquema del segundo cerebro Fase 2 — proyecto bunker-staging
-- Ejecutar en: Supabase Dashboard -> SQL Editor (pegado completo, Run).
-- Alternativa sin pgvector: ver bloque comentado al final.
-- La anon key ya usada por paper_runner inserta en public.journal gracias a
-- las politicas RLS permisivas de abajo (journal: insert/select para anon).
-- NOTA: relajar RLS de este modo es aceptable porque el proyecto es
-- bunker-staging y la tabla no contiene secretos; endurecer si el proyecto
-- deja de ser solo de staging.

-- extension pgvector (falla si no esta habilitada en el proyecto: usar el
-- bloque fallback de abajo y registrar la decision)
create extension if not exists vector;

-- 1) journal de decisiones/deliberaciones (no perder campos del SQLite:
-- ts, estrategia, evento, senal, decision, motivo, detalle(JSON),
-- equity_mtm, fecha_dato + fuente y dedupe_key para idempotencia)
create table if not exists public.journal (
    id          bigint generated always as identity primary key,
    ts          timestamptz not null default now(),
    estrategia  text not null,
    evento      text not null,
    senal       text,
    decision    text not null,
    motivo      text,
    detalle     jsonb,
    equity_mtm  double precision,
    fecha_dato  date,
    fuente      text not null default 'paper_runner_v1',
    dedupe_key  text not null unique
);
create index if not exists journal_fecha_idx on public.journal (fecha_dato);
create index if not exists journal_evento_idx on public.journal (evento);

alter table public.journal enable row level security;
create policy journal_anon_insert on public.journal for insert to anon with check (true);
create policy journal_anon_select on public.journal for select to anon using (true);

-- 2) knowledge: embeddings de contexto de mercado. CREADA PERO NO USADA AUN:
-- el retrieval semantico sigue condicionado a un consumidor concreto.
create table if not exists public.knowledge (
    id              bigint generated always as identity primary key,
    embedding       vector(1536),
    contenido       text not null,
    fuente          text not null,
    fecha_descarga  timestamptz not null default now(),
    hash            text not null unique
);
create index if not exists knowledge_embedding_idx on public.knowledge
    using ivfflat (embedding vector_cosine_ops) with (lists = 100);

alter table public.knowledge enable row level security;
create policy knowledge_anon_insert on public.knowledge for insert to anon with check (true);
create policy knowledge_anon_select on public.knowledge for select to anon using (true);

-- FALLBACK si 'create extension vector' falla (pgvector no habilitado):
--   create table public.knowledge (
--       id bigint generated always as identity primary key,
--       contenido text not null,
--       fuente text not null,
--       fecha_descarga timestamptz not null default now(),
--       hash text not null unique
--   );
--   (sin columna embedding ni indice; documentar la decision)
