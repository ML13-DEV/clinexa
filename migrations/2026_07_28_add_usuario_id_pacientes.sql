-- Migración: agrega usuario_id a pacientes (dueño del registro).
--
-- Crítico de seguridad: hasta ahora ningún query filtraba pacientes por el
-- médico autenticado, así que cualquier usuario logueado podía leer/editar/
-- borrar pacientes de otro médico. Esta columna es la base para el filtrado
-- por dueño en pacientes/notas/turnos/analisis (estos últimos tres cuelgan
-- de paciente_id y se filtran transitivamente, no tienen columna propia).
--
-- Esta base (Supabase nueva para el SaaS) arranca vacía, así que no hace
-- falta backfill: se agrega directamente como NOT NULL.
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_07_28_add_usuario_id_pacientes.sql

ALTER TABLE pacientes
    ADD COLUMN usuario_id INTEGER NOT NULL REFERENCES usuarios(id);

CREATE INDEX IF NOT EXISTS ix_pacientes_usuario_id ON pacientes (usuario_id);
