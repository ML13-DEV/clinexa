-- Migración: Analisis pasa de columnas fijas de hemograma/hierro/
-- coagulación a un modelo híbrido: analisis queda como header
-- (id, paciente_id, fecha) y cada determinación individual (gb, hb,
-- hto, hepatograma, otros_analisis, etc.) pasa a una fila en
-- analisis_valores (analisis_id, analisis_key, valor).
--
-- Se eligió esto en vez de un JSONB en analisis (alternativa evaluada)
-- pensando en rangos_normales: con filas normalizadas, colorear un
-- valor contra su rango es un JOIN de SQL directo por
-- (especialidad, analisis_key), no un cruce a mano en Python contra un
-- blob JSON.
--
-- También crea rangos_normales (especialidad, analisis_key, valor_min,
-- valor_max), estructura preparada para la feature de colores a
-- futuro — todavía sin cargar datos ni tener lógica que la consulte.
--
-- Si esta base ya tiene análisis cargados (no aplica a una Supabase
-- nueva y vacía), este script preserva esos datos moviéndolos a
-- analisis_valores antes de borrar las columnas viejas.
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_07_28_analisis_hibrido_y_rangos_normales.sql

CREATE TABLE IF NOT EXISTS analisis_valores (
    id SERIAL PRIMARY KEY,
    analisis_id INTEGER NOT NULL REFERENCES analisis(id) ON DELETE CASCADE,
    analisis_key VARCHAR(50) NOT NULL,
    valor VARCHAR(255),
    UNIQUE (analisis_id, analisis_key)
);

CREATE INDEX IF NOT EXISTS ix_analisis_valores_analisis_id ON analisis_valores (analisis_id);
CREATE INDEX IF NOT EXISTS ix_analisis_valores_analisis_key ON analisis_valores (analisis_key);

CREATE TABLE IF NOT EXISTS rangos_normales (
    id SERIAL PRIMARY KEY,
    especialidad VARCHAR(50) NOT NULL,
    analisis_key VARCHAR(50) NOT NULL,
    valor_min DOUBLE PRECISION,
    valor_max DOUBLE PRECISION,
    UNIQUE (especialidad, analisis_key)
);

CREATE INDEX IF NOT EXISTS ix_rangos_normales_especialidad ON rangos_normales (especialidad);

-- Preserva datos existentes: una fila por columna no nula, por análisis.
INSERT INTO analisis_valores (analisis_id, analisis_key, valor)
SELECT id, campo.key, campo.valor
FROM analisis,
LATERAL (VALUES
    ('gb', gb::text), ('nt', nt::text), ('l', l::text), ('hb', hb::text),
    ('hto', hto::text), ('vcm', vcm::text), ('pqts', pqts::text),
    ('ferremia', ferremia::text), ('ferritina', ferritina::text),
    ('saturacion', saturacion::text), ('tibc', tibc::text),
    ('epo', epo::text), ('vit_b12', vit_b12::text), ('af', af::text),
    ('ldh', ldh::text), ('hepatograma', hepatograma), ('funcion_renal', funcion_renal),
    ('tp', tp::text), ('kptt', kptt::text), ('rino', rino::text),
    ('otros_analisis', otros_analisis)
) AS campo(key, valor)
WHERE campo.valor IS NOT NULL
ON CONFLICT (analisis_id, analisis_key) DO NOTHING;

ALTER TABLE analisis
    ALTER COLUMN paciente_id SET NOT NULL,
    DROP COLUMN IF EXISTS gb,
    DROP COLUMN IF EXISTS nt,
    DROP COLUMN IF EXISTS l,
    DROP COLUMN IF EXISTS hb,
    DROP COLUMN IF EXISTS hto,
    DROP COLUMN IF EXISTS vcm,
    DROP COLUMN IF EXISTS pqts,
    DROP COLUMN IF EXISTS ferremia,
    DROP COLUMN IF EXISTS ferritina,
    DROP COLUMN IF EXISTS saturacion,
    DROP COLUMN IF EXISTS tibc,
    DROP COLUMN IF EXISTS epo,
    DROP COLUMN IF EXISTS vit_b12,
    DROP COLUMN IF EXISTS af,
    DROP COLUMN IF EXISTS ldh,
    DROP COLUMN IF EXISTS hepatograma,
    DROP COLUMN IF EXISTS funcion_renal,
    DROP COLUMN IF EXISTS tp,
    DROP COLUMN IF EXISTS kptt,
    DROP COLUMN IF EXISTS rino,
    DROP COLUMN IF EXISTS otros_analisis;
