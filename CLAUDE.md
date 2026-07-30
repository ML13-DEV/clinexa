# Clinexa SaaS Multiespecialidad

## Qué es esto

Producto SaaS multi-tenant de gestión de consultorios médicos multiespecialidad,
en desarrollo sobre la rama `feature/saas-multiespecialidad`.

Es un **producto separado** del sistema `main`/`estable` (el que ya usa una
hematóloga, Euge, en producción). No hay merge-back planeado: van a ser dos
despliegues independientes, cada uno con su propia base Supabase y su propio
Web Service en Render. No propongas cambios "para mantener compatibilidad"
con el schema o código de `main` — son bases de código que van a divergir
a propósito.

## Stack

- **Backend**: FastAPI + SQLAlchemy (ORM) + Pydantic v2 (`pydantic-settings`
  para config tipada desde env vars).
- **DB**: PostgreSQL/Supabase en producción; SQLite como fallback de
  desarrollo local (`sqlite:///./med.db` si no hay `DATABASE_URL`).
- **Migraciones**: SQL escrito a mano en `migrations/`, **no Alembic**. Ver
  sección de migraciones más abajo.
- **Auth**: JWT (`python-jose`) + bcrypt (`passlib`). El payload lleva `sub`,
  `id`, `rol`, `especialidad`.
- **Frontend**: Jinja2 + Bootstrap 5 + JS vanilla (sin framework) + Chart.js
  para gráficos.
- **Tests**: pytest + `fastapi.testclient.TestClient`, SQLite en memoria.

## Arquitectura y decisiones clave

### Multi-tenant vía `usuario_id`

Todos los médicos comparten la misma base. `Paciente` y `Turno` tienen una
columna `usuario_id` (el médico dueño). `Nota` y `Analisis` no tienen dueño
directo: cuelgan de un `paciente_id`, así que la propiedad se resuelve
transitivamente vía `Paciente`.

Toda esa lógica está centralizada en `app/core/permissions.py`:
- `get_paciente_propio(db, paciente_id, usuario_id)` — 404 (no 403) si el
  paciente es de otro médico, para no confirmarle a un atacante que el ID
  existe.
- `get_registro_de_paciente_propio(db, modelo, id, usuario_id)` — mismo
  criterio para Nota/Analisis/Turno, vía JOIN a Paciente.

Cualquier ruta nueva que reciba un `paciente_id` o un id de un registro
colgado de un paciente **tiene** que pasar por una de estas dos funciones
antes de leer o modificar algo. Cubierto por `tests/test_multitenant.py`.

### Catálogo de especialidades: código, no tabla

`app/especialidades/config.py` (campos clínicos del paciente) y
`app/especialidades/analisis_config.py` (determinaciones de laboratorio)
son diccionarios Python (`CAMPOS_POR_ESPECIALIDAD`, `ANALISIS_POR_ESPECIALIDAD`),
no tablas en la base.

Por qué: las especialidades y sus campos los da de alta el equipo de
desarrollo en un deploy, no un usuario final en runtime. Una tabla +
CRUD + migración sería overhead injustificado para algo que cambia por
código. **Si en algún momento un médico necesita definir sus propios
campos custom sin depender de un deploy, ahí sí vale la pena migrar esto
a una tabla** (`especialidad_campos` o similar) — no antes.

Cada catálogo se expone vía `GET /especialidades/campos` y
`GET /especialidades/analisis` (+ `GET /especialidades/analisis/rangos`
para los valores de referencia). `paciente.html` pide estos endpoints una
vez y arma el formulario/tabla/gráfico dinámicamente — un médico de una
especialidad no puede ver ni cargar campos de otra.

La validación server-side (`validar_datos_clinicos` en `config.py`,
`validar_analisis` en `analisis_config.py`) rechaza con 422: keys que el
catálogo no define, valores no numéricos en campos `NUMERO`, y opciones
inválidas en campos `SELECT`. Ver `tests/test_validaciones.py`.

### `Analisis`: modelo híbrido, no JSONB

`Analisis` es un header (`id`, `paciente_id`, `fecha`); cada determinación
individual (gb, hb, glucemia, etc.) es una fila en `AnalisisValor`
(`analisis_id`, `analisis_key`, `valor` como string).

Se evaluó un JSONB en `Analisis` como alternativa más simple, pero se
descartó pensando en `rangos_normales`: con filas normalizadas, colorear
un valor contra su rango normal es un JOIN de SQL directo por
`(especialidad, analisis_key)`, no un cruce a mano en Python contra un
blob JSON. `AnalisisCreate`/`AnalisisUpdate` usan
`ConfigDict(extra="allow")` para aceptar las keys de cualquier
especialidad sin declararlas una por una en el schema.

### Roles: `owner` / `medico`

- `RolUsuario` (`app/models/usuario.py`) es un `Enum` de Python usado en
  `UsuarioCreate` (Pydantic) para validar con 422 cualquier rol que no sea
  `owner` o `medico`. **A propósito no es un Enum de SQLAlchemy** — eso
  mapearía a un tipo `ENUM` nativo en Postgres y exigiría migrar el tipo de
  columna; la columna sigue siendo `String`, y el único lugar donde se
  escribe (`POST /owner/usuarios`) ya pasa por la validación de Pydantic.
- `get_current_owner` y `get_current_medico` (`app/core/dependencies.py`)
  son los guards de rol. `owner` administra médicos pero **no gestiona
  pacientes** (bloqueado con 403 en pacientes/notas/analisis/turnos);
  `medico` no puede pegarle a `/owner/*`. Ver `tests/test_roles.py`.
- El login (`POST /login`) devuelve `rol` además del token;
  `login.html` redirige a `/owner` o `/` según corresponda (antes
  mandaba siempre a `/`, lo cual rompía la UX de `owner` porque esa home
  llama a endpoints que ahora le están bloqueados).

## Estado actual (fases completas)

1. **Aislamiento multi-tenant** en pacientes/notas/turnos/análisis.
2. **Catálogo de especialidades** (campos clínicos) para Hematología,
   Nutrición, Cardiología y Neurología; `paciente.html` generalizado para
   armar el formulario dinámicamente según la especialidad del médico
   logueado.
3. **Catálogo de análisis** por especialidad (`analisis_config.py`),
   migración de los 21 campos de Hematología a este modelo, panel de
   análisis/tabla/gráfico de `paciente.html` generalizado igual que el
   formulario de paciente.
4. **Panel owner** (`/owner`, antes `/admin`): rol renombrado de `admin` a
   `owner`, primera UI real para este rol (antes solo API). Alta/baja de
   médicos, reasignación de especialidad, cantidad de pacientes por
   médico (vía `COUNT`+`JOIN`, no contando en el frontend).
5. **Validación de catálogo** con 422: `datos_clinicos` y
   `analisis_valores` rechazan keys fuera del catálogo de la especialidad
   y tipos incorrectos, en vez de guardarlos silenciosamente.
6. **Rol como Enum validado** (`RolUsuario`) en vez de string libre.
7. **Guard `get_current_medico`**: `owner` ya no puede gestionar pacientes
   por API aunque tenga un JWT válido.
8. **Suite de tests con pytest** (19 tests, SQLite en memoria, sin
   Alembic ni Postgres de test): aislamiento multi-tenant, roles,
   validaciones de catálogo, recálculo de IMC.
9. **`rangos_normales`**: endpoint (`GET /especialidades/analisis/rangos`),
   coloreado en `paciente.html` (`colorearValor()`, soporta límites de un
   solo lado), y una migración de seed con valores de bibliografía
   clínica general — **ver deuda técnica, esto necesita revisión médica**.
10. **Estadísticas de plataforma** en el panel owner
    (`GET /owner/estadisticas`): médicos/pacientes/notas/análisis
    agregados y por especialidad, con tarjetas y un gráfico de barras.
    Todo vía `COUNT`/`GROUP BY`, sin exponer datos clínicos ni pacientes
    individuales.
11. **`created_at`** agregado a `Usuario` y `Paciente` (sin uso todavía,
    sembrado para no perder el dato de alta real de ahora en más).

## Deuda técnica y pendientes

- **`rangos_normales` necesita revisión médica antes de confiar en el
  coloreado**: los valores cargados (`migrations/2026_07_28_seed_rangos_normales.sql`)
  salen de bibliografía clínica general (MedlinePlus, Mayo Clinic Labs,
  StatPearls, etc.), no de un laboratorio específico. Puntos concretos:
  - `hb`, `hto`, `ferritina` son compromisos **unisex** porque `Paciente`
    no registra el sexo del paciente (el rango real varía por sexo).
  - `epo`, `vit_b12`, `af`, `ldh`, `vitamina_d`, `tsh` tienen alta
    variabilidad entre fuentes — valores intermedios, no de un lab puntual.
  - **Troponina y BNP quedaron sin cargar a propósito**: el corte depende
    demasiado del ensayo específico (convencional vs. ultrasensible) como
    para adivinar un número genérico sin riesgo clínico real.
  - `circunferencia_cintura` (nutrición) y `escala_dolor` (neurología)
    tampoco se cargaron (dependiente de sexo la primera, escala subjetiva
    la segunda).
- **Sexo del paciente no modelado**: además de los rangos normales, es un
  dato clínico razonable de tener y hoy no existe en `Paciente`. Si se
  agrega, hay que revisar `rangos_normales` para dejar de usar los
  compromisos unisex.
- **`datos_clinicos`/`analisis_valores`**: la validación no chequea el
  tipo `FECHA` del catálogo de campos clínicos (`TipoCampo.FECHA`) ni
  formatos dentro de `TEXTO`/`TEXTAREA` — solo requerido/tipo
  numérico/opciones de `SELECT`.
- **Sin tests de UI automatizados**: la verificación en browser se hizo
  con Playwright ad hoc en cada sesión, no quedó como suite de regresión.
  Los 19 tests de pytest son solo de backend.
- **Hardening de producción no abordado**: CORS, rate limiting, headers
  de seguridad. Probablemente baja prioridad mientras sea un puñado de
  médicos usando la app directamente, pero a tener en cuenta si crece.
- **Panel owner con alcance angosto a propósito**: no permite resetear
  contraseña ni cambiar username de un médico (solo
  especialidad/activo) — así se pidió, no es un olvido.
- **No hay endpoint para promover un turno con `nombre_temp` a un
  `Paciente` real** (folder `turnos.py` permite crear un turno sin
  paciente asociado, pero no convertirlo después).
- **Infra pendiente (no es código)**: crear/confirmar el proyecto
  Supabase y el Web Service de Render dedicados a este SaaS, setear
  `DATABASE_URL`/`SECRET_KEY` ahí. En local, cuidado con una
  `DATABASE_URL` de sistema apuntando a un MySQL de otro proyecto — un
  `.env` propio con `override=True` en `load_dotenv` la tapa (ver
  `app/core/config.py`).

## Migraciones

Los scripts en `migrations/` son SQL a mano, pensados para **evolucionar
una base que ya tiene tablas en una forma anterior**. En una Supabase
nueva y vacía **no hace falta correrlos**: `Base.metadata.create_all()`
(en `app/main.py`, al arrancar la app) crea todas las tablas ya en su
forma final. Corré los `.sql` a mano solo si estás actualizando una base
que ya tenía datos con el schema viejo.

`migrations/2026_07_28_seed_usuarios_de_prueba.sql` crea un owner + un
médico por especialidad con contraseña de prueba — pensado para probar
el deploy, no para quedar en una base con datos reales sin cambiar esa
contraseña.

## Cómo correr esto localmente

```bash
# Backend, con SQLite de fallback (sin pisar un DATABASE_URL de sistema)
unset DATABASE_URL
uvicorn app.main:app --reload

# Tests (no requieren Postgres ni Alembic)
pip install -r requirements-dev.txt
pytest
```
