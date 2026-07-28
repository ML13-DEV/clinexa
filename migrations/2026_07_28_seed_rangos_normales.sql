-- Migración: carga valores de referencia (rangos_normales) para que
-- paciente.html empiece a colorear resultados fuera de rango
-- (colorearValor() en paciente.html, GET /especialidades/analisis/rangos).
--
-- Fuentes: bibliografía clínica general (MedlinePlus, Mayo Clinic Labs,
-- MSD Manual, StatPearls/NCBI, Cleveland Clinic, Johns Hopkins, entre
-- otras), no un lab específico. Revisados con el equipo médico antes de
-- cargar esta migración; quedan marcados los que siguen abiertos a
-- ajuste:
--   - hb, hto, ferritina: el catálogo no registra sexo del paciente, así
--     que se cargó un rango unisex de compromiso en vez del real
--     partido por sexo (ej. hb: 13-18 hombres / 12-16 mujeres -> 12-17).
--   - epo, vit_b12, af, ldh, vitamina_d, tsh: alta variabilidad entre
--     fuentes/labs: valores intermedios, no un dato de un lab puntual.
--   - troponina y BNP (cardiologia) quedan sin cargar a propósito: el
--     corte depende demasiado del ensayo específico (convencional vs.
--     ultrasensible) como para adivinar un número genérico sin riesgo
--     clínico real. Cargar cuando se tenga el valor de corte del
--     laboratorio que se use.
--   - circunferencia_cintura (nutricion) y escala_dolor (neurologia)
--     tampoco se cargan: la primera depende del sexo del paciente, la
--     segunda es una escala subjetiva, no un valor de laboratorio.
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_07_28_seed_rangos_normales.sql

INSERT INTO rangos_normales (especialidad, analisis_key, valor_min, valor_max) VALUES
    -- Hematología
    ('hematologia', 'gb', 4.5, 11.0),
    ('hematologia', 'nt', 40, 60),
    ('hematologia', 'l', 20, 40),
    ('hematologia', 'hb', 12, 17),
    ('hematologia', 'hto', 36, 50),
    ('hematologia', 'vcm', 82, 99),
    ('hematologia', 'pqts', 150, 400),
    ('hematologia', 'ferremia', 50, 175),
    ('hematologia', 'ferritina', 20, 250),
    ('hematologia', 'saturacion', 20, 50),
    ('hematologia', 'tibc', 250, 370),
    ('hematologia', 'epo', 4, 24),
    ('hematologia', 'vit_b12', 200, 900),
    ('hematologia', 'af', 3, 17),
    ('hematologia', 'ldh', 140, 280),
    ('hematologia', 'tp', 85, 100),
    ('hematologia', 'kptt', 25, 35),
    ('hematologia', 'rino', 0.8, 1.2),

    -- Nutrición
    ('nutricion', 'glucemia', 70, 99),
    ('nutricion', 'colesterol_total', NULL, 200),
    ('nutricion', 'hdl', 40, NULL),
    ('nutricion', 'ldl', NULL, 100),
    ('nutricion', 'trigliceridos', NULL, 150),
    ('nutricion', 'hba1c', NULL, 5.7),
    ('nutricion', 'albumina', 3.5, 5.0),
    ('nutricion', 'vitamina_d', 30, 100),

    -- Cardiología
    ('cardiologia', 'colesterol_total', NULL, 200),
    ('cardiologia', 'hdl', 40, NULL),
    ('cardiologia', 'ldl', NULL, 100),
    ('cardiologia', 'trigliceridos', NULL, 150),
    ('cardiologia', 'presion_sistolica', 90, 120),
    ('cardiologia', 'presion_diastolica', 60, 80),
    ('cardiologia', 'frecuencia_cardiaca', 60, 100),

    -- Neurología
    ('neurologia', 'vitamina_b12', 200, 900),
    ('neurologia', 'acido_folico', 3, 17),
    ('neurologia', 'tsh', 0.4, 4.5)
ON CONFLICT (especialidad, analisis_key) DO UPDATE SET
    valor_min = EXCLUDED.valor_min,
    valor_max = EXCLUDED.valor_max;
