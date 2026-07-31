-- Migración: agrega creado_en al paciente (timestamp de alta), usado para la
-- métrica de "pacientes nuevos por mes" en el dashboard de estadísticas.
--
-- Los pacientes ya existentes van a quedar con creado_en = momento en que se
-- corre esta migración (no hay forma de recuperar la fecha real de alta
-- retroactivamente), por lo que el mes en el que se corre este script va a
-- mostrar un pico artificial en el gráfico de altas por mes.
--
-- Nota: Base.metadata.create_all() (app/main.py) solo crea tablas nuevas, no
-- agrega columnas a tablas existentes. Este script debe aplicarse manualmente
-- contra la base PostgreSQL de producción/staging (Supabase).
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_07_31_add_creado_en_paciente.sql

ALTER TABLE pacientes
    ADD COLUMN IF NOT EXISTS creado_en TIMESTAMP DEFAULT NOW();
