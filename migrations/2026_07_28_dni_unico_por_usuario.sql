-- Migración: el DNI deja de ser único global y pasa a ser único por médico.
--
-- Con usuario_id ya agregado (ver 2026_07_28_add_usuario_id_pacientes.sql),
-- dos médicos distintos deben poder cada uno tener un paciente con el mismo
-- DNI (son historias clínicas independientes). Lo que no puede pasar es que
-- el mismo médico repita un DNI.
--
-- Requiere que la migración de usuario_id ya se haya aplicado.
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_07_28_dni_unico_por_usuario.sql

ALTER TABLE pacientes DROP CONSTRAINT IF EXISTS pacientes_dni_key;

ALTER TABLE pacientes
    ADD CONSTRAINT uq_paciente_usuario_dni UNIQUE (usuario_id, dni);
