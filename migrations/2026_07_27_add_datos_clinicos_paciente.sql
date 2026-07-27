-- Migración: agrega datos clínicos al paciente (peso, talla, IMC, diagnóstico
-- principal, ocupación, hábitos, medicación habitual, cirugías, transfusiones,
-- antecedentes personales y familiares).
--
-- Nota: Base.metadata.create_all() (app/main.py) solo crea tablas nuevas, no
-- agrega columnas a tablas existentes. Este script debe aplicarse manualmente
-- contra la base PostgreSQL de producción/staging (Supabase).
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_07_27_add_datos_clinicos_paciente.sql

ALTER TABLE pacientes
    ADD COLUMN IF NOT EXISTS peso DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS talla DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS imc DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS diagnostico_principal TEXT,
    ADD COLUMN IF NOT EXISTS ocupacion VARCHAR(150),
    ADD COLUMN IF NOT EXISTS habitos TEXT,
    ADD COLUMN IF NOT EXISTS medicacion_habitual TEXT,
    ADD COLUMN IF NOT EXISTS cirugias TEXT,
    ADD COLUMN IF NOT EXISTS transfusiones TEXT,
    ADD COLUMN IF NOT EXISTS antecedentes_personales TEXT,
    ADD COLUMN IF NOT EXISTS antecedentes_familiares TEXT;
