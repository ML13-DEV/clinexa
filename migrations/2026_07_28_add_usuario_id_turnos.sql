-- Migración: agrega usuario_id a turnos (dueño del registro).
--
-- Turno puede existir sin paciente_id (walk-in con nombre_temp, todavía sin
-- ficha creada), así que el dueño no se puede derivar siempre a través del
-- paciente: necesita su propia columna, igual que se hizo para pacientes en
-- 2026_07_28_add_usuario_id_pacientes.sql.
--
-- Esta base (Supabase nueva para el SaaS) arranca vacía, así que no hace
-- falta backfill: se agrega directamente como NOT NULL.
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_07_28_add_usuario_id_turnos.sql

ALTER TABLE turnos
    ADD COLUMN usuario_id INTEGER NOT NULL REFERENCES usuarios(id);

CREATE INDEX IF NOT EXISTS ix_turnos_usuario_id ON turnos (usuario_id);
