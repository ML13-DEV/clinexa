-- Migración: renombra el valor de rol 'admin' a 'owner'.
--
-- Mismo permiso de siempre (alta/baja de médicos, activar/desactivar,
-- asignar especialidad), solo cambia el nombre del valor para que sea
-- más claro qué representa. No agrega capacidades nuevas.
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_07_28_rol_admin_a_owner.sql

UPDATE usuarios SET rol = 'owner' WHERE rol = 'admin';
