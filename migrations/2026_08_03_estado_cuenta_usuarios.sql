-- Migración: agrega estado y nombre a usuarios, reemplaza el booleano
-- activo por un estado de cuenta más granular (pendiente/activo/
-- rechazado/suspendido), necesario para el flujo de registro público
-- con aprobación del owner (Fase A de suscripciones).
--
-- Backfill: activo=True -> 'activo', activo=False -> 'suspendido'.
-- Ninguna fila existente pudo haber quedado en pendiente/rechazado
-- porque ese flujo no existía antes de esta migración.
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_08_03_estado_cuenta_usuarios.sql

ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS estado VARCHAR(50);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nombre VARCHAR(150);

UPDATE usuarios SET estado = CASE WHEN activo THEN 'activo' ELSE 'suspendido' END
WHERE estado IS NULL;

ALTER TABLE usuarios ALTER COLUMN estado SET NOT NULL;
ALTER TABLE usuarios ALTER COLUMN estado SET DEFAULT 'activo';

ALTER TABLE usuarios DROP COLUMN activo;
