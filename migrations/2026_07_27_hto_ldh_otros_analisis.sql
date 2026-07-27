-- Migración: renombra HTD a HTO, agrega LDH y "Otros análisis" a la tabla de
-- análisis.
--
-- - HTD -> HTO: se renombra la columna (RENAME COLUMN preserva los datos ya
--   cargados, no hace falta backfill).
-- - LDH: nueva columna numérica, mismo criterio que el resto del hemograma.
-- - otros_analisis: nueva columna de texto libre para análisis no contemplados
--   en las columnas fijas existentes.
--
-- Nota: Base.metadata.create_all() (app/main.py) solo crea tablas nuevas, no
-- agrega ni renombra columnas en tablas existentes. Este script debe aplicarse
-- manualmente contra la base PostgreSQL de producción/staging (Supabase).
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_07_27_hto_ldh_otros_analisis.sql

ALTER TABLE analisis RENAME COLUMN htd TO hto;

ALTER TABLE analisis
    ADD COLUMN IF NOT EXISTS ldh DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS otros_analisis TEXT;
