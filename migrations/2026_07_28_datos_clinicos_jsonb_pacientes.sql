-- Migración: reemplaza las columnas hematología-específicas de pacientes
-- (sangrados, trombosis, gestas, vacunas, fim_descriptivo) por una única
-- columna datos_clinicos JSONB, catalogada por especialidad en
-- app/especialidades/config.py.
--
-- alergias y medico_cabecera NO se tocan: son comunes a cualquier
-- especialidad, quedan como columnas fijas.
--
-- Si esta base ya tiene pacientes cargados (no aplica a una Supabase
-- nueva y vacía), este script preserva esos datos moviéndolos al JSONB
-- antes de borrar las columnas viejas.
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_07_28_datos_clinicos_jsonb_pacientes.sql

ALTER TABLE pacientes
    ADD COLUMN IF NOT EXISTS datos_clinicos JSONB NOT NULL DEFAULT '{}';

UPDATE pacientes
SET datos_clinicos = datos_clinicos || jsonb_strip_nulls(
    jsonb_build_object(
        'sangrados', sangrados,
        'trombosis', trombosis,
        'gestas', gestas,
        'vacunas', vacunas,
        'fim_descriptivo', fim_descriptivo
    )
)
WHERE sangrados IS NOT NULL
   OR trombosis IS NOT NULL
   OR gestas IS NOT NULL
   OR vacunas IS NOT NULL
   OR fim_descriptivo IS NOT NULL;

ALTER TABLE pacientes
    DROP COLUMN IF EXISTS sangrados,
    DROP COLUMN IF EXISTS trombosis,
    DROP COLUMN IF EXISTS gestas,
    DROP COLUMN IF EXISTS vacunas,
    DROP COLUMN IF EXISTS fim_descriptivo;
