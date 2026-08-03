-- Agrega email a usuarios, necesario para poder mandar el mail de reset
-- de contraseña (username no está garantizado que sea una dirección
-- real, ej. usuarios de seed como "drhemato").
--
-- Nullable a propósito: las cuentas ya existentes quedan sin email
-- hasta que el owner o el propio médico lo carguen; no rompe nada
-- existente. De acá en más /registro lo pide como requerido.
--
-- En una base nueva (create_all sin datos previos) no hace falta correr
-- esto: la tabla ya se crea con esta columna.
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_08_03_email_usuarios.sql

ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS email VARCHAR(255);
