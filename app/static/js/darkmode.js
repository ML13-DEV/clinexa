function aplicarModo() {
    const darkMode = localStorage.getItem("darkMode");

    if (darkMode === "true") {
        document.body.classList.add("dark-mode");
    } else {
        document.body.classList.remove("dark-mode");
    }
}

function toggleDarkMode() {
    const isDark = document.body.classList.contains("dark-mode");
    localStorage.setItem("darkMode", !isDark);
    aplicarModo();
}

// 🔥 IMPORTANTE: se ejecuta SIEMPRE
document.addEventListener("DOMContentLoaded", () => {
    aplicarModo();
});