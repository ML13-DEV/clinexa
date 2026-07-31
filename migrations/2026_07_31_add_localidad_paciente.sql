-- Migración: agrega localidad al paciente (dato demográfico fijo, común a
-- las 4 especialidades — no es un campo del catálogo de especialidades).
--
-- No hace falta correr esto contra una Supabase nueva y vacía:
-- Base.metadata.create_all() (app/main.py) ya crea la tabla en su forma
-- final. Corré este script a mano solo si estás actualizando una base que
-- ya tenía la tabla pacientes sin esta columna.
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_07_31_add_localidad_paciente.sql

ALTER TABLE pacientes
    ADD COLUMN IF NOT EXISTS localidad VARCHAR(150);
