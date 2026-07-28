-- Usuarios de prueba para probar el panel owner y los 4 catálogos de
-- especialidad en la web deployada. Contraseña para los 5: Test1234!
-- (hash bcrypt via passlib, mismo esquema que app/core/security.py).
--
-- Cambiá esta contraseña (o borrá estos usuarios) después de probar si
-- la base tiene datos reales cerca.
--
-- Uso: psql "$DATABASE_URL" -f migrations/2026_07_28_seed_usuarios_de_prueba.sql

INSERT INTO usuarios (username, password, rol, especialidad, activo) VALUES
    ('owner1',   '$2b$12$2F5S0Az8vwSc6vklpYjQs.sj3xBlk5RGb.Q8a23DGwBhlL9ik100u', 'owner',  'sistema',     true),
    ('drhemato', '$2b$12$TcVGs.llACdo2eo3Ar.ynu712.kMGzFkqO06eOxxeYKbimt8qB9nS', 'medico', 'hematologia', true),
    ('drnutri',  '$2b$12$k.bvF9a1X3riLmP5gxm7L.3a7/sNT8JOEAMz7NvAm8Su84UAbdybW', 'medico', 'nutricion',   true),
    ('drcardio', '$2b$12$rq4S6Z.AYlBuKZaw5Ovr9eM.WRvjwQvxToJb5odcOwSodQFSC66m.', 'medico', 'cardiologia', true),
    ('drneuro',  '$2b$12$WAojgZgQAN0rM.yEJdRY9Ou1lQ2Yx/UwIZIr6HGPXdgSYYqqDOZ/W', 'medico', 'neurologia',  true)
ON CONFLICT (username) DO NOTHING;
