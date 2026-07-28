// Renderiza y lee los campos clínicos dinámicos de la especialidad del
// médico logueado (ver GET /especialidades/campos y
// app/especialidades/config.py). Usado por nuevo_paciente.html y
// paciente.html para no duplicar esta lógica en los dos.

function escapeAttr(valor) {
    return String(valor ?? "").replace(/"/g, "&quot;");
}

function renderCampoInput(campo, valor) {
    const value = escapeAttr(valor);
    const attrs = `id="campo_${campo.key}" data-campo-key="${campo.key}" class="form-control mb-2"`;
    const requiredAttr = campo.requerido ? "required" : "";

    if (campo.tipo === "textarea") {
        return `<textarea ${attrs} ${requiredAttr} placeholder="${campo.label}">${value}</textarea>`;
    }

    if (campo.tipo === "select") {
        const opciones = (campo.opciones || [])
            .map(op => `<option value="${escapeAttr(op)}" ${op === valor ? "selected" : ""}>${op}</option>`)
            .join("");
        return `<select ${attrs} ${requiredAttr}><option value="">-- ${campo.label} --</option>${opciones}</select>`;
    }

    const tipoInput = campo.tipo === "numero" ? "number" : campo.tipo === "fecha" ? "date" : "text";
    return `<input type="${tipoInput}" ${attrs} ${requiredAttr} placeholder="${campo.label}" value="${value}">`;
}

function renderCamposEspecialidad(containerId, campos, valores = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!campos.length) {
        container.innerHTML = "";
        return;
    }

    container.innerHTML = campos.map(campo => `
        <label class="form-label small text-muted mb-1">${campo.label}${campo.requerido ? " *" : ""}</label>
        ${renderCampoInput(campo, valores[campo.key])}
    `).join("");
}

function leerCamposEspecialidad(containerId) {
    const container = document.getElementById(containerId);
    const datos = {};
    if (!container) return datos;

    container.querySelectorAll("[data-campo-key]").forEach(el => {
        datos[el.dataset.campoKey] = el.value;
    });

    return datos;
}

async function cargarCamposEspecialidad(containerId, valores = {}) {
    const res = await fetch("/especialidades/campos", {
        headers: { "Authorization": "Bearer " + localStorage.getItem("token") }
    });

    if (!res.ok) return [];

    const campos = await res.json();
    renderCamposEspecialidad(containerId, campos, valores);
    return campos;
}
