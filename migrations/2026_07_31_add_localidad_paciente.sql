-- Migración: agrega localidad al paciente (dato demográfico, no clínico).
--
-- Nota: Base.metadata.create_all() (app/main.py) solo crea tablas nuevas, no
-- agrega columnas a tablas existentes. Este script debe aplicarse manualmente
-- contra la base PostgreSQL de producción/staging (Supabase).
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_07_31_add_localidad_paciente.sql

ALTER TABLE pacientes
    ADD COLUMN IF NOT EXISTS localidad VARCHAR(150);
