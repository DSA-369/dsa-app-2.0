# 🏁 Downhill Skate App — DSA 2.0 🛹

![DSA License](https://img.shields.io/badge/License-Proprietary-red.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Streamlit](https://img.shields.io/badge/Framework-Streamlit-FF4B4B.svg)
![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E.svg)

**DSA 2.0** es una plataforma digital de vanguardia diseñada para la gestión deportiva automatizada, procesamiento de cronometrajes en pista, cálculo analítico de brackets de carrera y clasificaciones de alto rendimiento en el Downhill Skateboarding nacional.

---

## 🚀 Características Principales

* **👥 Comunidad de Riders:** Perfiles autónomos con inicio de sesión seguro para que cada atleta gestione de forma independiente sus datos técnicos y material multimedia.
* **🗂️ Historial de Válidas:** Repositorio centralizado con el registro histórico de eventos, pistas y campeonatos ejecutados.
* **🌍 Ranking Nacional:** Motor de cálculo en tiempo real apegado estrictamente al sistema de puntaje oficial de la **WDSC**, asegurando clasificaciones transparentes y automáticas.
* **⏱️ Módulos de Operación Técnica:** Secciones restringidas mediante cripto-llaves de administración para Jueces de Pista, Directores de Carrera y personal de Cronometraje.

---

## 🛠️ Arquitectura Tecnológica

* **Frontend & UI:** [Streamlit](https://streamlit.io/) optimizado con inyecciones dinámicas de CSS e interfaces fluidas PWA para dispositivos móviles y de escritorio.
* **Backend & Base de Datos:** [Supabase](https://supabase.com/) (PostgreSQL) con consultas blindadas e inyección de tokens dinámicos (`Timestamp`) para destrucción de caché de CDN en almacenamiento de archivos (Storage).
* **Versionamiento:** Git & GitHub bajo flujos de despliegue continuo (CD) hacia servidores de producción.

---

## 💻 Instalación y Configuración Local

Para ejecutar el panel de control de la DSA 2.0 en un entorno de desarrollo local, siga estos pasos:

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/dsa-app-2.0.git](https://github.com/tu-usuario/dsa-app-2.0.git)
   cd dsa-app-2.0