-- Migración: agrega created_at a usuarios y pacientes.
--
-- No se usa para nada todavía (la sección de estadísticas del panel
-- owner es foto actual, sin series de tiempo), pero se agrega ahora
-- para no dejar un hueco irrecuperable: cualquier fila creada antes de
-- tener esta columna no puede tener su fecha real reconstruida después.
--
-- Filas existentes quedan con la fecha en que se corre esta migración
-- (no hay forma de saber la fecha real de alta), lo cual es aceptable
-- porque hasta ahora ese dato no se guardaba en ningún lado.
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_07_28_created_at_usuarios_pacientes.sql

ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();
