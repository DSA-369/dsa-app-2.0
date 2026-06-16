import os
import streamlit as st
import pandas as pd
import time
import re
import streamlit.components.v1 as components
from dotenv import load_dotenv
from supabase import create_client, Client

# Intentamos importar de forma segura el motor de brackets por si ya está creado
try:
    from bracket_engine import BracketEngine
except ImportError:
    BracketEngine = None

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA E IDENTIDAD VISUAL
# ==========================================
st.set_page_config(
    page_title="DSA 2.0 - Panel de Control",
    page_icon="🏁",
    layout="wide"
)

# Paleta de colores DSA (Fondo Negro, Acentos en Azul de Carrera, Naranja Enérgico y Menú Animado)
st.markdown("""
    <style>
        /* Fondo Principal Oscuro / Negro */
        .stApp {
            background-color: #0c0f17;
            color: #f1f5f9;
        }
        
        /* Modificar el menú lateral (Sidebar) */
        section[data-testid="stSidebar"] {
            background-color: #080a10 !important;
            border-right: 2px solid #ff7a00; /* Borde naranja */
        }
        
        /* Estilo para los títulos y subtítulos */
        h1, h2, h3, h4, h5, h6, .stMarkdown {
            color: #ffffff !important;
            font-family: 'Segoe UI', sans-serif;
        }
        
        /* Personalizar botones de acción (Naranja DSA) */
        div.stButton > button {
            background-color: #ff7a00 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: bold !important;
            padding: 0.6rem 2rem !important;
            transition: all 0.3s ease;
            width: 100%;
        }
        
        div.stButton > button:hover {
            background-color: #0052ff !important; /* Cambia a Azul en Hover */
            box-shadow: 0 0 10px #0052ff;
            transform: scale(1.02);
        }

        /* Estilo para cajas informativas */
        .stAlert {
            background-color: #111827 !important;
            border-left: 5px solid #0052ff !important; /* Borde azul de proceso */
            color: #f1f5f9 !important;
        }
        
        /* Decoraciones de inputs */
        input, select, textarea {
            background-color: #1e293b !important;
            color: white !important;
            border: 1px solid #475569 !important;
        }

        /* Tarjeta de Corredor en Heat */
        .rider-card {
            background-color: #111827;
            border: 2px solid #1e293b;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            transition: border-color 0.3s ease;
        }
        .rider-card:hover {
            border-color: #ff7a00;
        }
        .podium-box {
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 8px 16px rgba(0,0,0,0.4);
            margin-bottom: 20px;
        }

        /* 🚀 MULTI-SELECTOR BLINDADO: Captura el botón abierto, cerrado, en PC o Móvil 🚀 */
        button[data-testid="stSidebarCollapseButton"],
        div[data-testid="collapsedControl"] button,
        .stSidebarCollapseButton {
            background-color: #ff7a00 !important; /* Naranja DSA */
            color: #ffffff !important;
            border-radius: 50% !important;
            box-shadow: 0 0 0 0 rgba(255, 122, 0, 0.7) !important;
            animation: pulso_menu 1.8s infinite cubic-bezier(0.66, 0, 0, 1) !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        /* Forzamos a que las flechas internas (los vectores SVG) se vuelvan blancas */
        button[data-testid="stSidebarCollapseButton"] svg,
        div[data-testid="collapsedControl"] button svg {
            fill: #ffffff !important;
            color: #ffffff !important;
        }

        @keyframes pulso_menu {
            to {
                box-shadow: 0 0 0 15px rgba(255, 122, 0, 0) !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN REAL A LA BASE DE DATOS
# ==========================================
load_dotenv()

# 1. Buscamos primero en el entorno local (.env)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# 2. Si estamos en la nube, usamos la bóveda de Streamlit (st.secrets)
if "SUPABASE_URL" in st.secrets:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
if "SUPABASE_KEY" in st.secrets:
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# Variable global del cliente Supabase
supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.sidebar.error(f"Error de conexión: {e}")
else:
    st.sidebar.error("❌ No se encontraron credenciales en el sistema")

# ==========================================
# 3. CARGA DE LOGO REAL DE LA DSA
# ==========================================
# Traer el logo directamente desde Supabase
# Traer el logo directamente desde Supabase
LOGO_URL = "https://gaxnteisqvvkjavhtmgm.supabase.co/storage/v1/object/public/directorio-partners/SPOND36.PNG"

# 1. Mostrar la imagen del logo
st.sidebar.image(LOGO_URL, use_container_width=True)

# 2. Mostrar el subtítulo centrado debajo de la imagen
st.sidebar.markdown("<h3 style='color:#ff7a00; text-align:center; margin-top: -10px;'>🏁 DSA 2.0</h3>", unsafe_allow_html=True)

# 3. La línea divisoria
st.sidebar.markdown("<hr style='border: 1px solid #1e293b; margin-top: 5px;'/>", unsafe_allow_html=True)
# ==========================================
# 4. NAVEGACIÓN MODULAR (RANKING EN SEGUNDO LUGAR)
# ==========================================
st.sidebar.title("🏁 Menú de Carrera")
opcion_menu = st.sidebar.radio(
    "Navegación:",
    [
        "🗂️ Historial de Válidas",
        "🌍 Ranking Nacional",
        "👥 Maestro de Corredores",
        "📝 Inscripción de Válida",
        "⏱️ Cronometraje en Pista",
        "📊 Resultados y Brackets",
        "🏁 Vista del Juez",
        "🏆 Cuadro de Honor y Rankings"
    ]
)

# Estilo visual de cabecera principal con colores DSA
st.markdown("""
    <div style='background: linear-gradient(90deg, #0c0f17 0%, #0052ff 100%); padding: 20px; border-radius: 8px; margin-bottom: 25px; border-left: 8px solid #ff7a00;'>
        <h1 style='margin:0; font-size:32px; color: white;'>DOWNHILL SYSTEM APP</h1>
        <p style='margin:5px 0 0 0; color:#cbd5e1; font-weight:bold;'>Plataforma Avanzada de Gestión Deportiva, Brackets y Clasificación de Alto Rendimiento 🏆</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 🔒 SISTEMA DE SEGURIDAD Y ACCESO PÚBLICO
# ==========================================
if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False

# Palabras clave para identificar módulos que el público SÍ puede ver sin contraseña
modulos_publicos = ["Historial", "Ranking", "Maestro"]

# EVALUACIÓN INTELIGENTE: Verifica si la opción elegida contiene alguna de las palabras clave de arriba
es_modulo_publico = any(palabra in opcion_menu for palabra in modulos_publicos)

# Si NO es un módulo público y el usuario NO se ha autenticado como admin, lo bloqueamos
if not es_modulo_publico and not st.session_state.admin_auth:
    st.markdown("<br>", unsafe_allow_html=True)
    st.warning("🔒 **Área Restringida: Acceso exclusivo para Jueces y Staff de la DSA**")
    st.info("💡 El público puede navegar libremente por el 'Ranking Nacional', 'Historial de Válidas' y 'Maestro de Corredores' en el menú izquierdo.")
    
    col_pwd, _ = st.columns([4, 6])
    with col_pwd:
        pwd = st.text_input("🔑 Ingresa la clave de administración:", type="password")
        if st.button("Desbloquear Sistema"):
            if pwd == "dsa2026":  # <--- AQUÍ PUEDES CAMBIAR TU CONTRASEÑA
                st.session_state.admin_auth = True
                st.success("✅ Acceso concedido.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta.")
    
    st.stop()  # 🛑 MAGIA: Esto detiene el código aquí y oculta todo lo de abajo al público.

# Botón para cerrar sesión si ya eres admin (aparece en el menú lateral)
if st.session_state.admin_auth:
    st.sidebar.markdown("---")
    if st.sidebar.button("🔒 Cerrar Sesión (Juez)"):
        st.session_state.admin_auth = False
        st.rerun()

# ==========================================
# ESTADOS DE CONTROL Y VERSIONES DE CRONÓMETRO
# ==========================================
if "crono_version" not in st.session_state:
    st.session_state.crono_version = 0
if "mostrar_celebracion" not in st.session_state:
    st.session_state.mostrar_celebracion = False

# ==========================================
# CELEBRACIÓN DE BANDERA A CUADROS
# ==========================================
def lanzar_lluvia_banderas():
    divs_banderas = ""
    for i in range(40):
        posicion_horizontal = i * 2.5
        retraso_animacion = (i % 6) * 0.4
        duracion_caida = 2.0 + (i % 4) * 0.4
        tamano_bandera = 22 + (i % 4) * 8
        divs_banderas += f'<div class="flag-confetti" style="left:{posicion_horizontal}%; animation-delay:{retraso_animacion}s; animation-duration:{duracion_caida}s; font-size:{tamano_bandera}px;">🏁</div>'
    
    css_js_celebration = f"""
    <style>
        @keyframes fallAndRotate {{
            0% {{ transform: translateY(-100px) rotate(0deg); opacity: 0; }}
            10% {{ opacity: 1; }}
            90% {{ opacity: 1; }}
            100% {{ transform: translateY(105vh) rotate(360deg); opacity: 0; }}
        }}
        .flag-confetti {{
            position: fixed;
            top: -100px;
            z-index: 999999;
            pointer-events: none;
            animation-name: fallAndRotate;
            animation-timing-function: linear;
            animation-iteration-count: 1;
            animation-fill-mode: forwards;
        }}
    </style>
    <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 999998; overflow: hidden;">
        {divs_banderas}
    </div>
    """
    st.markdown(css_js_celebration, unsafe_allow_html=True)

if st.session_state.mostrar_celebracion:
    lanzar_lluvia_banderas()
    st.session_state.mostrar_celebracion = False

# ==========================================
# COMPONENTE BIDIRECCIONAL: CRONÓMETRO CLIENTE
# ==========================================
cronometro_html_content = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { background-color: #0c0f17; color: #f1f5f9; font-family: 'Segoe UI', -apple-system, sans-serif; margin: 0; padding: 5px; overflow: hidden; }
        .crono-box { background-color: #000000; border: 3px solid #0052ff; border-radius: 10px; padding: 15px; text-align: center; font-family: 'Courier New', Courier, monospace; font-size: 46px; color: #ff7a00; font-weight: bold; box-shadow: 0 0 15px #0052ff; margin-bottom: 12px; }
        .btn-container { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 12px; }
        button { color: white; border: none; padding: 12px; font-weight: bold; border-radius: 6px; cursor: pointer; font-size: 14px; transition: all 0.2s ease; }
        #btn-salida { background-color: #ff7a00; }
        #btn-salida:hover { background-color: #e06c00; }
        #btn-meta { background-color: #0052ff; }
        #btn-meta:hover { background-color: #0041cc; }
        #btn-reset { background-color: #dc2626; }
        #btn-reset:hover { background-color: #b91c1c; }
        #guardar-container { text-align: center; }
        .btn-enviar { background: linear-gradient(90deg, #10b981 0%, #059669 100%); color: white; border: none; padding: 12px; font-weight: bold; border-radius: 6px; cursor: pointer; width: 100%; font-size: 14px; }
        .btn-enviar:hover { background: linear-gradient(90deg, #059669 0%, #047857 100%); }
    </style>
</head>
<body>
    <div class="crono-box" id="reloj-visual">0:00.000</div>
    <div class="btn-container">
        <button id="btn-salida" onclick="iniciarCrono()">🚀 SALIDA</button>
        <button id="btn-meta" onclick="detenerCrono()" style="display: none;">🏁 META</button>
        <button id="btn-reset" onclick="resetCrono()" style="display: none;">🔄 RESET</button>
    </div>
    <div id="guardar-container" style="display: none;">
        <p style="color: #cbd5e1; font-size: 14px; margin: 0 0 8px 0;">Tiempo Capturado: <span id="tiempo-cap-txt" style="color:#10b981; font-weight:bold;">0:00.000</span></p>
        <button class="btn-enviar" onclick="enviarAlBackend()">💾 Registrar Tiempo en Supabase</button>
    </div>
    <script>
        let startTime = 0;
        let elapsedTime = 0;
        let timerInterval = null;
        let totalSegundosGuardar = 0;
        const display = document.getElementById("reloj-visual");
        const btnSalida = document.getElementById("btn-salida");
        const btnMeta = document.getElementById("btn-meta");
        const btnReset = document.getElementById("btn-reset");
        const guardarContainer = document.getElementById("guardar-container");
        const txtTiempoCap = document.getElementById("tiempo-cap-txt");

        function sendStreamlitMessage(type, payload = {}) {
            window.parent.postMessage({ isStreamlitMessage: true, type: type, ...payload }, "*");
        }
        function formatTime(timeInMs) {
            let diffInMin = timeInMs / (60 * 1000);
            let mm = Math.floor(diffInMin);
            let diffInSec = (diffInMin - mm) * 60;
            let ss = Math.floor(diffInSec);
            let diffInMs = (diffInSec - ss) * 1000;
            let ms = Math.floor(diffInMs);
            return `${mm}:${ss.toString().padStart(2, "0")}.${ms.toString().padStart(3, "0")}`;
        }
        function iniciarCrono() {
            startTime = Date.now() - elapsedTime;
            timerInterval = setInterval(function() {
                elapsedTime = Date.now() - startTime;
                display.textContent = formatTime(elapsedTime);
            }, 10);
            btnSalida.style.display = "none";
            btnMeta.style.display = "block";
            btnReset.style.display = "block";
            guardarContainer.style.display = "none";
            ajustarAltura();
        }
        function detenerCrono() {
            clearInterval(timerInterval);
            totalSegundosGuardar = elapsedTime / 1000;
            btnMeta.style.display = "none";
            txtTiempoCap.textContent = formatTime(elapsedTime);
            guardarContainer.style.display = "block";
            ajustarAltura();
        }
        function resetCrono() {
            clearInterval(timerInterval);
            elapsedTime = 0;
            totalSegundosGuardar = 0;
            display.textContent = "0:00.000";
            btnSalida.style.display = "block";
            btnMeta.style.display = "none";
            btnReset.style.display = "none";
            guardarContainer.style.display = "none";
            ajustarAltura();
        }
        function ajustarAltura() {
            sendStreamlitMessage("streamlit:setFrameHeight", { height: document.documentElement.scrollHeight });
        }
        function enviarAlBackend() {
            sendStreamlitMessage("streamlit:setComponentValue", { value: totalSegundosGuardar });
        }
        window.onload = function() {
            sendStreamlitMessage("streamlit:componentReady", { apiVersion: 1 });
            ajustarAltura();
        };
        window.addEventListener("message", function(event) {
            if (event.data.type === "streamlit:render") { ajustarAltura(); }
        });
    </script>
</body>
</html>
"""

@st.cache_resource
def registrar_componente_crono():
    dir_principal = os.path.dirname(os.path.abspath(__file__))
    ruta_temp_crono = os.path.join(dir_principal, "temp_crono")
    os.makedirs(ruta_temp_crono, exist_ok=True)
    with open(os.path.join(ruta_temp_crono, "index.html"), "w", encoding="utf-8") as f:
        f.write(cronometro_html_content)
    return components.declare_component("crono_componente_dsa", path=ruta_temp_crono)

crono_componente_dsa = registrar_componente_crono()

# ==========================================
# METODOS DE BASE DE DATOS Y RENDERIZADO
# ==========================================
def obtener_riders_desde_db():
    if not supabase: return []
    try:
        # El "*" le ordena a Supabase traer absolutamente todas las columnas existentes
        response = supabase.table("riders_master").select("*").order("nombre").execute()
        return response.data
    except Exception as e:
        st.error(f"Error al consultar la base de datos: {e}")
        return []

def obtener_inscritos_desde_db():
    if not supabase: return []
    try:
        response = supabase.table("inscritos_valida").select("dorsal, id_rider, categoria_evento, firma_disclaimer, estado_registro, riders_master(nombre, foto_url)").execute()
        return response.data
    except Exception as e:
        st.error(f"Error: {e}")
        return []

def obtener_tiempos_tt_desde_db():
    if not supabase: return []
    try:
        response = supabase.table("clasificacion_tt").select("dorsal, tiempo_run1, tiempo_run2, penalizacion_segundos, top_speed").execute()
        return response.data
    except Exception as e:
        st.error(f"Error: {e}")
        return []

def desglosar_tiempo_a_segundos(texto_crudo):
    if not texto_crudo.isdigit(): return None
    if len(texto_crudo) <= 3: return float(texto_crudo)
    milesimas_str = texto_crudo[-3:]
    resto_str = texto_crudo[:-3]
    if len(resto_str) > 2:
        segundos_str = resto_str[-2:]
        minutos_str = resto_str[:-2]
        minutos = int(minutos_str) if minutos_str else 0
        segundos = int(segundos_str) if segundos_str else 0
    else:
        minutos = 0
        segundos = int(resto_str) if resto_str else 0
    milisegundos = int(milesimas_str)
    return round((minutos * 60) + segundos + (milisegundos / 1000.0), 3)

def formatear_segundos_a_cronometro(segundos_totales):
    if segundos_totales is None or pd.isna(segundos_totales) or segundos_totales == float('inf'):
        return "---"
    
    minutos = int(segundos_totales // 60)
    segundos_restantes = segundos_totales % 60
    segundos = int(segundos_restantes)
    milisegundos = int(round((segundos_restantes - segundos) * 1000))
    
    if milisegundos == 1000:
        segundos += 1
        milisegundos = 0
    if segundos == 60:
        minutos += 1
        segundos = 0
        
    return f"{minutos}:{segundos:02d}.{milisegundos:03d}"

# ==========================================
# PARSER INTELIGENTE DE IMÁGENES
# ==========================================
def resolver_ruta_imagen(ruta_raw):
    # Si está vacío, devolvemos None inmediatamente
    if not ruta_raw or pd.isna(ruta_raw) or str(ruta_raw).strip() == "" or str(ruta_raw).lower() == 'nan':
        return None
    
    ruta_str = str(ruta_raw).strip()
    
    # Si parece una URL (contiene supabase o http), devuélvela tal cual
    if "http" in ruta_str or "supabase" in ruta_str:
        return ruta_str
        
    # Si no es URL, busca en rutas locales
    if os.path.exists(ruta_str): return ruta_str
    
    # Si no encontró nada, devolvemos None
    return None
# ==========================================
# MODULO: MAESTRO DE CORREDORES (VERSIÓN DEFINITIVA DE FOTOS)
# ==========================================
if "👥 Maestro de Corredores" in opcion_menu:
    import datetime
    import time

    # 1. Inicialización de interruptores de pantalla en la memoria de la App
    if "mostrar_registro_rider" not in st.session_state:
        st.session_state.mostrar_registro_rider = False
    if "mostrar_perfil_rider" not in st.session_state:
        st.session_state.mostrar_perfil_rider = False
    if "rider_autenticado" not in st.session_state:
        st.session_state.rider_autenticado = None
    if "version_fotos" not in st.session_state:
        st.session_state.version_fotos = 1

    # =======================================================
    # PANTALLA A: FORMULARIO DE REGISTRO
    # =======================================================
    if st.session_state.mostrar_registro_rider:
        st.markdown("### 📝 Inscripción Oficial de Corredor")
        if st.button("⬅️ Cancelar y volver al Maestro", key="btn_cancel_reg"):
            st.session_state.mostrar_registro_rider = False
            st.rerun()
            
        def obtener_proximo_id():
            try:
                res = supabase.table("riders_master").select("id_rider").execute()
                ids_actuales = []
                for r in res.data:
                    val = str(r.get('id_rider', ''))
                    digitos = ''.join(c for c in val if c.isdigit())
                    if digitos: ids_actuales.append(int(digitos))
                return max(ids_actuales) + 1 if ids_actuales else 1
            except:
                return 1
                
        proximo_id = obtener_proximo_id()
        id_formateado = f"RID{proximo_id:03d}"
        url_foto_generada = f"https://gaxnteisqvvkjavhtmgm.supabase.co/storage/v1/object/public/riders-photos/{id_formateado}.jpeg"

        with st.form("form_nuevo_rider"):
            st.markdown(f"### 🆔 Código DSA Asignado: `{id_formateado}`")
            
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre Completo *").strip().upper()
                categoria_base = st.selectbox("Categoría Principal *", ["Open Skate", "Femenino Skate", "Junior Skate", "Master Skate", "Open Inline", "Femenino Inline", "Junior Inline", "Streetluge"])
                pais_input = st.text_input("Código de tu País (2 letras - Ej: VE, CO, PA) *", max_chars=2).strip().upper()
                ciudad_input = st.text_input("Ciudad o Estado que representas *").strip().upper()
                fecha_nacimiento = st.date_input("Fecha de Nacimiento", value=datetime.date(2000, 1, 1), min_value=datetime.date(1926, 1, 1))
                
            with col2:
                correo = st.text_input("Correo Electrónico *").strip()
                password_input = st.text_input("Crea una Contraseña para tu Perfil *", type="password").strip()
                telefono = st.text_input("Teléfono de Contacto").strip()
                telefono_emergencia = st.text_input("Teléfono de Emergencia").strip()
                instagram = st.text_input("Usuario de Instagram (sin @)").strip()
                
            st.markdown("---")
            foto_archivo = st.file_uploader("Sube tu foto de perfil (JPG / PNG)", type=['jpg', 'jpeg', 'png'])

            if st.form_submit_button("🚀 Registrar mi perfil en la DSA"):
                if not nombre or not correo or not ciudad_input or len(pais_input) < 2 or not password_input:
                    st.error("⚠️ Por favor completa los campos obligatorios (*) incluyendo tu contraseña.")
                else:
                    estado_pais_combinado = f"{pais_input} | {ciudad_input}"
                    insta_limpio = instagram.replace("@", "")
                    if insta_limpio and not insta_limpio.startswith("http"):
                        insta_limpio = f"https://www.instagram.com/{insta_limpio}/"
                        
                    if foto_archivo:
                        try:
                            # Posicionamiento estándar de parámetros del SDK
                            supabase.storage.from_("riders-photos").upload(
                                path=f"{id_formateado}.jpeg", 
                                file=foto_archivo.getvalue(), 
                                file_options={"content-type": foto_archivo.type, "upsert": "true"}
                            )
                        except Exception as e:
                            st.warning(f"Aviso de almacenamiento de imagen: {e}")

                    nuevo_registro = {
                        "id_rider": id_formateado,  
                        "nombre": nombre,
                        "categoria_base": categoria_base,
                        "estado_pais": estado_pais_combinado,
                        "fecha_nacimiento": str(fecha_nacimiento),
                        "correo": correo,
                        "password": password_input,
                        "telefono": telefono,
                        "telefono_emergencia": telefono_emergencia,
                        "instagram": insta_limpio if insta_limpio else None,
                        "foto_url": url_foto_generada,
                        "total_eventos": 0
                    }
                    
                    try:
                        supabase.table("riders_master").insert(nuevo_registro).execute()
                        st.success(f"🎉 ¡Inscripción exitosa! Tu código es {id_formateado}.")
                        time.sleep(2)
                        st.session_state.mostrar_registro_rider = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar datos: {e}")

    # =======================================================
    # PANTALLA C: INTERFAZ AUTÓNOMA "MI PERFIL DSA" (LOGIN / EDICIÓN)
    # =======================================================
    elif st.session_state.mostrar_perfil_rider:
        st.markdown("### 👤 Panel Autónomo de Corredores")
        
        if st.button("⬅️ Volver a la Tabla Principal", key="btn_volver_tabla"):
            st.session_state.mostrar_perfil_rider = False
            st.rerun()

        if st.session_state.rider_autenticado is None:
            st.markdown("#### 🔑 Iniciar Sesión de Atleta")
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                login_codigo = st.text_input("Ingresa tu Código DSA:", placeholder="Ej: RID039").strip().upper()
                login_pass = st.text_input("Ingresa tu Contraseña:", type="password").strip()
                
                if st.button("🔓 Entrar a mi Perfil", use_container_width=True):
                    if not login_codigo or not login_pass:
                        st.error("⚠️ Por favor ingresa tu código y contraseña.")
                    else:
                        try:
                            res = supabase.table("riders_master").select("*").eq("id_rider", login_codigo).execute()
                            if res.data:
                                rider_db = res.data[0]
                                contrasena_guardada = str(rider_db.get('password', '')).strip()
                                es_clave_valida = False
                                
                                if contrasena_guardada == "" or contrasena_guardada.lower() == "none":
                                    if login_pass == "dsa2026" or login_pass == login_codigo:
                                        es_clave_valida = True
                                        st.toast("⚠️ Clave temporal detectada. Por favor, asigna una contraseña segura abajo.", icon="🔒")
                                else:
                                    if contrasena_guardada == login_pass:
                                        es_clave_valida = True
                                
                                if es_clave_valida:
                                    st.session_state.rider_autenticado = rider_db
                                    st.success(f"✅ ¡Acceso concedido! Bienvenido, {rider_db.get('nombre')}.")
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    st.error("❌ Contraseña incorrecta para este código.")
                            else:
                                st.error("❌ El código de corredor no existe en la base de datos.")
                        except Exception as e:
                            st.error(f"Error de conexión con el servidor: {e}")

        else:
            rider = st.session_state.rider_autenticado
            st.markdown(f"#### 🛠️ Editando el Perfil de: **{rider.get('id_rider')}**")
            
            if st.button("🚨 Cerrar Sesión de Corredor"):
                st.session_state.rider_autenticado = None
                st.rerun()

            ubicacion_actual = str(rider.get('estado_pais') or 'VE | CARACAS')
            p_inicial = ubicacion_actual.split("|")[0].strip() if "|" in ubicacion_actual else "VE"
            e_inicial = ubicacion_actual.split("|")[1].strip() if "|" in ubicacion_actual else ubicacion_actual

            try: f_inicial = datetime.datetime.strptime(str(rider.get('fecha_nacimiento') or '2000-01-01'), '%Y-%m-%d').date()
            except: f_inicial = datetime.date(2000, 1, 1)

            LISTA_CATEGORIAS_EDICION = ["Open Skate", "Femenino Skate", "Junior Skate", "Master Skate", "Open Inline", "Femenino Inline", "Junior Inline", "Streetluge"]

            cat_guardada = str(rider.get('categoria_base') or '').strip()
            if cat_guardada in LISTA_CATEGORIAS_EDICION:
                idx_cat = LISTA_CATEGORIAS_EDICION.index(cat_guardada)
            else:
                idx_cat = 0  

            with st.form("form_editar_rider"):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    edit_nombre = st.text_input("Nombre Completo *", value=str(rider.get('nombre') or '')).strip().upper()
                    edit_categoria = st.selectbox("Categoría de Competición *", LISTA_CATEGORIAS_EDICION, index=idx_cat)
                    edit_pais = st.text_input("Código de tu País (2 letras) *", value=str(p_inicial), max_chars=2).strip().upper()
                    edit_ciudad = st.text_input("Ciudad / Estado *", value=str(e_inicial)).strip().upper()
                    edit_fecha = st.date_input("Fecha de Nacimiento", value=f_inicial, min_value=datetime.date(1926, 1, 1))
                
                with col_e2: 
                    edit_correo = st.text_input("Correo Electrónico *", value=str(rider.get('correo') or '')).strip()
                    edit_pass = st.text_input("Cambiar Contraseña *", value=str(rider.get('password') or ''), type="password").strip()
                    edit_tel = st.text_input("Teléfono de Contacto", value=str(rider.get('telefono') or '')).strip()
                    edit_tel_em = st.text_input("Teléfono de Emergencia", value=str(rider.get('telefono_emergencia') or '')).strip()
                    
                    insta_url_vieja = str(rider.get('instagram') or '')
                    if "instagram.com/" in insta_url_vieja:
                        insta_user_viejo = insta_url_vieja.split("instagram.com/")[-1].replace("/", "").strip()
                    else:
                        insta_user_viejo = insta_url_vieja
                    edit_insta = st.text_input("Usuario de Instagram (sin @)", value=insta_user_viejo).strip()

                st.markdown("---")
                st.write("📸 **Actualizar Foto de Perfil** (Dejar vacío si deseas conservar tu foto actual)")
                nueva_foto = st.file_uploader("Subir nueva imagen cuadrada (JPG / PNG)", type=['jpg', 'jpeg', 'png'], key="update_photo_loader")

                submit_edicion = st.form_submit_button("💾 Guardar y Actualizar mis Datos")

                if submit_edicion:
                    if not edit_nombre or not edit_correo or not edit_ciudad or len(edit_pais) < 2 or not edit_pass:
                        st.error("⚠️ Los campos marcados con (*) son obligatorios.")
                    else:
                        edit_insta_limpio = edit_insta.replace("@", "")
                        if edit_insta_limpio and not edit_insta_limpio.startswith("http"):
                            edit_insta_limpio = f"https://www.instagram.com/{edit_insta_limpio}/"

                        id_rider_actual = rider.get('id_rider')
                        
                        # 🚀 BLINDAJE ABSOLUTO EN EL STORAGE DE SUPABASE 🚀
                        if nueva_foto:
                            try:
                                # Paso A: Forzamos el borrado físico de la foto vieja de forma explícita
                                try:
                                    supabase.storage.from_("riders-photos").remove([f"{id_rider_actual}.jpeg"])
                                except:
                                    pass
                                
                                # Paso B: Subimos la nueva foto ordenando la sintaxis estricta y corrigiendo 'upsert'
                                supabase.storage.from_("riders-photos").upload(
                                    path=f"{id_rider_actual}.jpeg", 
                                    file=nueva_foto.getvalue(), 
                                    file_options={"content-type": nueva_foto.type, "upsert": "true"}
                                )
                            except Exception as img_err:
                                st.error(f"⚠️ Alerta en Servidor de Imagen: {img_err}")

                        datos_actualizados = {
                            "nombre": edit_nombre,
                            "categoria_base": edit_categoria,
                            "estado_pais": f"{edit_pais} | {edit_ciudad}",
                            "fecha_nacimiento": str(edit_fecha),
                            "correo": edit_correo,
                            "password": edit_pass,
                            "telefono": edit_tel,
                            "telefono_emergencia": edit_tel_em,
                            "instagram": edit_insta_limpio if edit_insta_limpio else None
                        }

                        try:
                            supabase.table("riders_master").update(datos_actualizados).eq("id_rider", id_rider_actual).execute()
                            
                            # Incrementamos el token anti-caché del navegador
                            st.session_state.version_fotos += 1
                            
                            st.success("🎉 ¡Tu perfil ha sido actualizado con éxito!")
                            st.session_state.rider_autenticado.update(datos_actualizados)
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al sincronizar los cambios: {e}")

    # =======================================================
    # PANTALLA B: TABLA PRINCIPAL DE CONSULTA (VISTA POR DEFECTO)
    # =======================================================
    else:
        col_t, col_b1, col_b2 = st.columns([2, 1, 1])
        with col_t:
            st.subheader("👥 Registo Global de Corredores")
            st.write("Historial y base de datos de atletas registrados oficialmente en el sistema.")
        with col_b1:
            st.write("<br>", unsafe_allow_html=True)
            if st.button("➕ REGÍSTRATE AQUÍ", use_container_width=True):
                st.session_state.mostrar_registro_rider = True
                st.rerun()
        with col_b2:
            st.write("<br>", unsafe_allow_html=True)
            if st.button("👤 Mi Perfil DSA", use_container_width=True):
                st.session_state.mostrar_perfil_rider = True
                st.rerun()

        riders_lista = obtener_riders_desde_db()
        if riders_lista:
            df_riders = pd.DataFrame(riders_lista)
            
            cols_necesarias = ["foto_url", "id_rider", "nombre", "estado_pais", "categoria_base", "instagram", "total_eventos"]
            for col in cols_necesarias:
                if col not in df_riders.columns:
                    df_riders[col] = 0 if col == "total_eventos" else None

            df_riders["total_eventos"] = pd.to_numeric(df_riders["total_eventos"], errors='coerce').fillna(0)
            
            def obtener_url_bandera(texto):
                text_str = str(texto or '').strip()
                if not text_str: return "https://flagcdn.com/w80/un.png"
                pais_codigo = text_str.split("|")[0].strip().lower()
                return f"https://flagcdn.com/w80/{pais_codigo}.png"

            def obtener_estado_puro(texto):
                if not texto: return "N/A"
                return str(texto).split("|")[1].strip().upper() if "|" in str(texto) else str(texto).strip().upper()

            df_riders["Bandera_URL"] = df_riders["estado_pais"].apply(obtener_url_bandera)
            df_riders["Estado_Limpio"] = df_riders["estado_pais"].apply(obtener_estado_puro)

            def mapear_codigo_texto(val):
                val_str = str(val).strip()
                if val_str.startswith("RID"): return val_str  
                try: return f"RID{int(val_str):03d}"  
                except: return val_str

            df_riders["Codigo_Texto"] = df_riders["id_rider"].apply(mapear_codigo_texto)

            # 🚀 TRUCO MAESTRO: Forzamos un token de tiempo real único por cada recarga de página
            import time
            token_anticahe = int(time.time())
            df_riders["Foto_Con_Version"] = df_riders["foto_url"].apply(lambda url: f"{url}?t={token_anticahe}" if url else url)

            orden_categorias = ["Open Skate", "Femenino Skate", "Junior Skate", "Master Skate", "Open Inline", "Femenino Inline", "Junior Inline"]
            df_riders['categoria_base'] = df_riders['categoria_base'].fillna("Sin Categoría")
            df_riders['categoria_cat'] = pd.Categorical(df_riders['categoria_base'], categories=orden_categorias, ordered=True)
            df_riders = df_riders.sort_values(['categoria_cat', 'nombre'])
            
            df_vista = df_riders[["Foto_Con_Version", "Codigo_Texto", "nombre", "Bandera_URL", "Estado_Limpio", "categoria_base", "instagram", "total_eventos"]].copy()
            df_vista.columns = ["Foto", "Código", "Nombre", "País", "Estado", "Categoría", "Instagram", "Eventos"]
            
            st.dataframe(
                df_vista.set_index("Código"),
                column_config={
                    "Foto": st.column_config.ImageColumn("Avatar", width="small"),
                    "País": st.column_config.ImageColumn("País", width="small"),
                    "Instagram": st.column_config.LinkColumn("Instagram", display_text="📸 Ver Perfil"),
                    "Eventos": st.column_config.NumberColumn("Eventos", format="%d")
                },
                use_container_width=True
            )
        else:
            st.info("La base de datos de corredores del Maestro se encuentra vacía.")
                             
# MODULO: INSCRIPCIÓN DE VÁLIDA
# ==========================================
elif "📝 Inscripción de Válida" in opcion_menu:
    st.subheader("📝 Inscripción y Entrega de Dorsales")
    st.write("Registra los corredores activos para este evento y asígnales su número de dorsal de pista.")

    riders_lista = obtener_riders_desde_db()
    inscritos_lista = obtener_inscritos_desde_db()
    
    if not riders_lista:
        st.warning("⚠️ No se encontraron corredores en la tabla 'riders_master'. Primero debes registrar atletas en la base de datos.")
    else:
        opciones_select = [f"{r['id_rider']} | {r['nombre']}" for r in riders_lista]

        # Fila superior: Formulario y Planilla actual
        col1, col2 = st.columns([4, 6])

        with col1:
            st.markdown("### 🎫 Formulario de Registro")
            with st.form("registro_pista"):
                rider_elegido = st.selectbox("Seleccionar Atleta:", opciones_select)
                dorsal_input = st.text_input("🔢 Número de Dorsal asignado:", placeholder="Ej: 24").strip()
                
                categoria_carrera = st.selectbox(
                    "⚡ Categoría de Competición:",
                    ["Open Skate", "Junior Skate", "Femenino Skate", "Master Skate", "Open Inline", "Junior Inline", "Femenino Inline", "Master Inline", "Open Streetluge"]
                )
                
                disclaimer = st.checkbox("✍️ Disclaimer Físico Firmado", value=False)
                estado_reg = st.selectbox("🚦 Estatus Inicial:", ["Inscrito", "Verificado", "Retirado"])

                guardar = st.form_submit_button("💾 Guardar en Base de Datos")

                if guardar:
                    if not dorsal_input:
                        st.error("❌ El número de dorsal es estrictamente obligatorio para pista.")
                    else:
                        id_rider_clean = rider_elegido.split(" | ")[0].strip()
                        datos_inscripcion = {
                            "dorsal": dorsal_input,
                            "id_rider": id_rider_clean,
                            "categoria_evento": categoria_carrera,
                            "firma_disclaimer": disclaimer,
                            "estado_registro": estado_reg
                        }
                        
                        try:
                            supabase.table("inscritos_valida").insert(datos_inscripcion).execute()
                            st.success(f"🎉 ¡Dorsal {dorsal_input} asignado con éxito!")
                            st.rerun()
                        except Exception as ex:
                            err_msg = str(ex)
                            if "already exists" in err_msg or "violates unique constraint" in err_msg:
                                st.error(f"⚠️ Error: El Dorsal '{dorsal_input}' ya está asignado a otro corredor.")
                            else:
                                st.error(f"❌ Error al guardar: {err_msg}")

        with col2:
            st.markdown("### 📋 Planilla de Control de Pista")
            if not inscritos_lista:
                st.info("ℹ️ No hay corredores registrados en pista para esta carrera aún.")
            else:
                tabla_datos = []
                for ins in inscritos_lista:
                    nombre_rider = ins.get('riders_master', {}).get('nombre', 'Desconocido') if ins.get('riders_master') else 'Desconocido'
                    tabla_datos.append({
                        "Dorsal": ins['dorsal'],
                        "ID Rider": ins['id_rider'],
                        "Nombre": nombre_rider,
                        "Categoría": ins['categoria_evento'],
                        "Disclaimer": "✅ Firmado" if ins['firma_disclaimer'] else "⏳ Pendiente",
                        "Estatus": ins['estado_registro']
                    })
                
                df_inscritos = pd.DataFrame(tabla_datos)
                st.dataframe(df_inscritos.set_index("Dorsal"), use_container_width=True)

        # Fila inferior: Modificación y Baja Operativa (Solo si hay inscritos)
        if inscritos_lista:
            st.markdown("---")
            st.markdown("### ⚙️ Panel de Modificación y Baja Operativa")
            st.write("Selecciona un dorsal activo en la carrera para editar su información o darlo de baja.")
            
            dorsales_activos = [ins['dorsal'] for ins in inscritos_lista]
            
            col_sel, col_edit, col_del = st.columns([3, 5, 4])
            
            with col_sel:
                dorsal_a_gestionar = st.selectbox("🎯 Seleccionar Dorsal a Gestionar:", dorsales_activos)
                datos_actuales = next((ins for ins in inscritos_lista if ins['dorsal'] == dorsal_a_gestionar), None)
            
            if datos_actuales:
                nombre_actual = datos_actuales.get('riders_master', {}).get('nombre', 'Desconocido') if datos_actuales.get('riders_master') else 'Desconocido'
                
                with col_edit:
                    st.markdown(f"**✏️ Editar Datos de: {nombre_actual} (Dorsal {dorsal_a_gestionar})**")
                    nueva_categoria = st.selectbox(
                        "Cambiar Categoría de Evento:",
                        ["Open Skate", "Junior Skate", "Femenino Skate", "Master Skate", "Open Inline", "Junior Inline", "Femenino Inline", "Master Inline", "Open Streetluge"],
                        index=["Open Skate", "Junior Skate", "Femenino Skate", "Master Skate", "Open Inline", "Junior Inline", "Femenino Inline", "Master Inline", "Open Streetluge"].index(datos_actuales['categoria_evento'])
                    )
                    nuevo_estatus = st.selectbox(
                        "Cambiar Estatus de Registro:",
                        ["Inscrito", "Verificado", "Retirado"],
                        index=["Inscrito", "Verificado", "Retirado"].index(datos_actuales['estado_registro'])
                    )
                    nuevo_disclaimer = st.checkbox("Disclaimer Físico Actualizado", value=datos_actuales['firma_disclaimer'], key="edit_disc_valida")
                    
                    if st.button("🆙 Actualizar Datos del Rider"):
                        try:
                            supabase.table("inscritos_valida").update({
                                "categoria_evento": nueva_categoria,
                                "estado_registro": nuevo_estatus,
                                "firma_disclaimer": nuevo_disclaimer
                            }).eq("dorsal", dorsal_a_gestionar).execute()
                            
                            st.success(f"✅ Dorsal {dorsal_a_gestionar} updated successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar: {e}")
                
                with col_del:
                    st.markdown("**🚨 Zona de Peligro (Bajas)**")
                    st.write("Si un atleta decide no participar, puedes removerlo permanentemente.")
                    st.warning(f"Eliminará al Dorsal {dorsal_a_gestionar} de la carrera actual.")
                    
                    confirmar_borrado = st.checkbox(f"Confirmo la baja del Dorsal {dorsal_a_gestionar}", value=False)
                    if st.button("🗑️ Eliminar Corredor de la Válida"):
                        if confirmar_borrado:
                            try:
                                supabase.table("inscritos_valida").delete().eq("dorsal", dorsal_a_gestionar).execute()
                                st.success(f"💥 El Dorsal {dorsal_a_gestionar} fue eliminado.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al eliminar: {e}")
                        else:
                            st.error("⚠️ Debes confirmar la casilla de seguridad antes de eliminar.")

# ==========================================
# MODULO: ⏱️ CRONOMETRAJE EN PISTA
# ==========================================
elif "⏱️ Cronometraje en Pista" in opcion_menu:
    st.subheader("⏱️ Estación Central de Cronometraje - Time Trials")
    
    inscritos = obtener_inscritos_desde_db()
    tiempos_raw = obtener_tiempos_tt_desde_db()
    
    if not inscritos:
        st.warning("⚠️ No hay corredores inscritos en pista para cronometrar en este momento.")
    else:
        tiempos_dict = {t['dorsal']: t for t in tiempos_raw}
        
        opciones_dorsales = []
        for i in inscritos:
            dorsal = i['dorsal']
            t_data = tiempos_dict.get(dorsal, {})
            
            status_tag = " 🆕 [Pendiente]"
            if t_data.get('tiempo_run1') and t_data.get('tiempo_run2'): status_tag = " 🏆 [R1 y R2 Completados]"
            elif t_data.get('tiempo_run1'): status_tag = " ⏱️ [R1 Guardado]"
            elif t_data.get('tiempo_run2'): status_tag = " ⏱️ [R2 Guardado]"
                
            nombre_rider = i['riders_master']['nombre'] if i.get('riders_master') else 'Desconocido'
            opciones_dorsales.append(
                f"Dorsal {dorsal} | {nombre_rider} ({i['categoria_evento']}){status_tag}"
            )
        
        col_ctrl, col_leader = st.columns([5, 5])
        
        with col_ctrl:
            st.markdown("### 🎛️ Control de Captura de Tiempos")
            
            seleccion_rider = st.selectbox("Seleccionar Competidor en Línea de Salida:", opciones_dorsales)
            dorsal_actual = seleccion_rider.split(" | ")[0].replace("Dorsal ", "").strip()
            
            run_seleccionado = st.radio("Manga a registrar:", ["Run 1", "Run 2"], horizontal=True)
            penalizacion = st.number_input("⚠️ Penalización en Segundos (A sumar al final):", min_value=0.0, max_value=10.0, value=0.0, step=0.1)
            velocidad_capturada = st.number_input("⚡ Velocidad Registrada (km/h):", min_value=0.0, max_value=120.0, value=0.0, step=0.1)
            
            tab1, tab2, tab3 = st.tabs(["🔢 1. Ingreso Manual Crudo", "📱 2. Botones Nativos APP (Navegador)", "⚡ 3. Conexión Láser"])
            
            with tab1:
                st.write("Escribe el tiempo de tu cronómetro digital **sin usar puntos ni dos puntos**.")
                tiempo_crudo = st.text_input("Ingresa los números corridos:", placeholder="Ejemplo: para 1:33.369 escribe 133369", key="crono_manual_crudo")
                
                if st.button("💾 Guardar Tiempo Manual", key="guardar_manual_btn"):
                    tiempo_convertido = desglosar_tiempo_a_segundos(tiempo_crudo)
                    if tiempo_convertido is None:
                        st.error("❌ Por favor ingresa un número válido sin letras ni símbolos.")
                    else:
                        campo_db = "tiempo_run1" if run_seleccionado == "Run 1" else "tiempo_run2"
                        
                        try:
                            existe = supabase.table("clasificacion_tt").select("dorsal").eq("dorsal", dorsal_actual).execute()
                            
                            if existe.data:
                                supabase.table("clasificacion_tt").update({campo_db: tiempo_convertido, "penalizacion_segundos": penalizacion, "top_speed": velocidad_capturada}).eq("dorsal", dorsal_actual).execute()
                            else:
                                supabase.table("clasificacion_tt").insert({"dorsal": dorsal_actual, campo_db: tiempo_convertido, "penalizacion_segundos": penalizacion, "top_speed": velocidad_capturada}).execute()
                            
                            tiempo_pantalla = formatear_segundos_a_cronometro(tiempo_convertido)
                            st.session_state.mostrar_celebracion = True
                            st.success(f"✅ Guardado correctamente: {tiempo_pantalla} (Run guardado como {tiempo_convertido:.3f} s).")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error en base de datos: {e}")
            
            with tab2:
                st.write("Cronómetro ultra fluido e interactivo de 60 FPS. Procesado localmente para optimizar datos de internet.")
                tiempo_capturado_js = crono_componente_dsa(key=f"stopwatch_dsa_20_{st.session_state.crono_version}")
                
                if tiempo_capturado_js is not None and float(tiempo_capturado_js) > 0:
                    campo_db = "tiempo_run1" if run_seleccionado == "Run 1" else "tiempo_run2"
                    try:
                        existe = supabase.table("clasificacion_tt").select("dorsal").eq("dorsal", dorsal_actual).execute()
                        if existe.data:
                            supabase.table("clasificacion_tt").update({campo_db: float(tiempo_capturado_js), "penalizacion_segundos": penalizacion, "top_speed": velocidad_capturada}).eq("dorsal", dorsal_actual).execute()
                        else:
                            supabase.table("clasificacion_tt").insert({"dorsal": dorsal_actual, campo_db: float(tiempo_capturado_js), "penalizacion_segundos": penalizacion, "top_speed": velocidad_capturada}).execute()
                        
                        tiempo_formateado_exito = formatear_segundos_a_cronometro(float(tiempo_capturado_js))
                        st.session_state.mostrar_celebracion = True
                        st.success(f"🎉 ¡Dorsal {dorsal_actual} registrado con {tiempo_formateado_exito} en Supabase!")
                        st.session_state.crono_version += 1
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar el tiempo: {e}")
            
            with tab3:
                st.markdown("#### ⚡ Hardware Telemetría Láser")
                st.info("Plan de integración automatizada vía IoT.")
                st.write("**Arquitectura recomendada:**")
                st.write("- **Hardware:** Microcontrolador **ESP32** con receptor infrarrojo de barrera láser.")
                st.write("- **Protocolo:** El microcontrolador envía un paquete de datos vía UDP/WebSockets en la red WiFi local al puerto de esta aplicación, registrando la largada y llegada con precisión milimétrica.")
        
        with col_leader:
            st.markdown("### 📊 Leaderboard - Clasificación General")
            st.write("Clasificación ordenada por el **Mejor Tiempo** final de ambas mangas + Penalizaciones.")
            
            if not tiempos_raw:
                st.info("Esperando por el ingreso de los primeros tiempos de pista...")
            else:
                leaderboard_datos = []
                for t in tiempos_raw:
                    inf_r = next((i for i in inscritos if i['dorsal'] == t['dorsal']), None)
                    nombre = inf_r['riders_master']['nombre'] if inf_r and inf_r.get('riders_master') else "Desconocido"
                    categoria = inf_r['categoria_evento'] if inf_r else "Desconocida"
                    
                    r1 = float(t['tiempo_run1']) if t['tiempo_run1'] else float('inf')
                    r2 = float(t['tiempo_run2']) if t['tiempo_run2'] else float('inf')
                    pen = float(t['penalizacion_segundos']) if t['penalizacion_segundos'] else 0.0
                    
                    mejor_run = min(r1, r2)
                    mejor_tiempo_final = mejor_run + pen if mejor_run != float('inf') else 0.0
                    
                    leaderboard_datos.append({
                        "Dorsal": t['dorsal'],
                        "Nombre": nombre,
                        "Categoría": categoria,
                        "Run 1": formatear_segundos_a_cronometro(t['tiempo_run1']),
                        "Run 2": formatear_segundos_a_cronometro(t['tiempo_run2']),
                        "Pen. (s)": f"+{pen:.2f}",
                        "Mejor Tiempo (Num)": mejor_tiempo_final if mejor_tiempo_final > 0 else float('inf'),
                        "Mejor Tiempo": formatear_segundos_a_cronometro(mejor_tiempo_final) if mejor_tiempo_final > 0 else "Sin Tiempo",
                        "Velocidad (km/h)": t.get('top_speed', 0.0)
                    })
                
                df_leader = pd.DataFrame(leaderboard_datos)
                df_leader = df_leader.sort_values(by="Mejor Tiempo (Num)").reset_index(drop=True)
                df_leader.index = df_leader.index + 1
                df_leader_vista = df_leader.drop(columns=["Mejor Tiempo (Num)"])
                st.session_state.df_leader = df_leader
                st.dataframe(df_leader_vista, use_container_width=True)

# ==========================================
# MODULO: 📊 RESULTADOS Y BRACKETS
# ==========================================
elif "📊 Resultados y Brackets" in opcion_menu:
    st.subheader("📊 Resultados y Armado de Brackets")
    
    # Verificación en tiempo real si ya existen brackets en la base de datos
    brackets_activos = False
    if supabase is not None:
        try:
            response_check = supabase.table("resultados_bracket").select("id", count="exact").limit(1).execute()
            if response_check.count is not None and response_check.count > 0:
                brackets_activos = True
        except Exception:
            brackets_activos = False

    # CASO A: Brackets no han sido armados todavía
    if not brackets_activos:
        if "df_leader" in st.session_state:
            df_leader = st.session_state.df_leader
            st.success(f"✅ Datos de clasificación listos ({len(df_leader)} corredores cargados en memoria).")
            st.info("💡 Presiona el botón de abajo para distribuir los corredores en sus respectivos heats iniciales.")
            
            # Botón único para armar brackets iniciales
            if st.button("Armar Brackets Iniciales"):
                if BracketEngine is not None and supabase is not None:
                    try:
                        engine = BracketEngine(supabase)
                        df_leader_compat = df_leader.rename(columns={"Dorsal": "dorsal"})
                        if engine.registrar_heat_inicial(df_leader_compat):
                            st.session_state.mostrar_celebracion = True
                            st.success("✅ Brackets generados con éxito. ¡Estación de Juez activada!")
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error al generar brackets en base de datos: {e}")
                else:
                    st.warning("⚠️ El motor de brackets (bracket_engine.py) o la conexión a Supabase no están listos.")
        else:
            st.warning("⚠️ No se detectan tiempos clasificados en la sesión. Debes ir primero a la pestaña '⏱️ Cronometraje en Pista' para cargar el Leaderboard.")

    # CASO B: Brackets activos en Supabase - Mostrar Estación de Juez de Meta
    else:
        st.success("🏁 ¡Brackets de Carrera Activos y guardados en Supabase!")
        st.markdown("---")
        st.subheader("⏱️ Estación de Control: Juez de Meta (Heats)")
        st.write("Asigna de forma visual y rápida las posiciones de llegada para cada competidor en su heat actual.")

        try:
            # 1. Obtener heats existentes de la base de datos
            res_heats = supabase.table("resultados_bracket").select("heat_id, ronda, estado").execute()
            df_heats_db = pd.DataFrame(res_heats.data)
            
            if not df_heats_db.empty:
                heats_pendientes = df_heats_db[df_heats_db['estado'] == 'PENDIENTE']['heat_id'].unique().tolist()
                heats_cerrados = df_heats_db[df_heats_db['estado'] == 'CERRADO']['heat_id'].unique().tolist()
                
                opciones_control_display = []
                
                # Primero mostramos los pendientes con indicador rojo
                for h in heats_pendientes:
                    ronda_val = df_heats_db[df_heats_db['heat_id'] == h]['ronda'].iloc[0]
                    opciones_control_display.append(f"🔴 {ronda_val} ({h})")
                    
                # Luego mostramos los cerrados con indicador verde
                for h in heats_cerrados:
                    ronda_val = df_heats_db[df_heats_db['heat_id'] == h]['ronda'].iloc[0]
                    opciones_control_display.append(f"🟢 {ronda_val} ({h})")
                
                if opciones_control_display:
                    col_sel, col_stat = st.columns([5, 5])
                    with col_sel:
                        opcion_elegida_raw = st.selectbox("🎯 Seleccionar Manga a Controlar:", opciones_control_display)
                        # Extraemos el ID del heat real que está entre paréntesis (ej: R1_HEAT_1)
                        heat_seleccionado = opcion_elegida_raw.split("(")[-1].replace(")", "").strip()
                        
                    # 2. Consultar corredores asignados a ese heat específico
                    res_corredores_heat = supabase.table("resultados_bracket").select("*").eq("heat_id", heat_seleccionado).execute()
                    corredores_heat = res_corredores_heat.data
                    
                    # LOGICA ORIGINAL ESTABLE PARA OBTENER NOMBRES
                    res_inscritos_info = supabase.table("inscritos_valida").select("dorsal, riders_master(nombre, foto_url)").execute()
                    info_inscritos_dict = {str(item['dorsal']): item['riders_master'] for item in res_inscritos_info.data if item.get('riders_master')}

                    # Título de la manga en pantalla
                    ronda_val_seleccionada = df_heats_db[df_heats_db['heat_id'] == heat_seleccionado]['ronda'].iloc[0]
                    st.markdown(f"### 🏁 {ronda_val_seleccionada} - {heat_seleccionado}")
                    
                    # Mostrar tarjetas dinámicas en fila
                    cols_tarjetas = st.columns(len(corredores_heat))
                    resultados_ingresados = {}
                    posiciones_elegidas = []

                    for idx, corr in enumerate(corredores_heat):
                        dorsal_str = str(corr['dorsal'])
                        
                        # Lectura estable
                        info_rider = info_inscritos_dict.get(dorsal_str, {"nombre": f"Dorsal {dorsal_str}", "foto_url": None})
                        nombre_competidor = info_rider.get('nombre', f"Dorsal {dorsal_str}")
                        
                        # Resolvemos la ruta de la imagen
                        url_foto_convertida = resolver_ruta_imagen(info_rider.get('foto_url'))
                        
                        # Definir posición inicial o cargada previamente
                        pos_actual = corr.get('posicion_heat') if corr.get('posicion_heat') is not None else 0
                        
                        with cols_tarjetas[idx]:
                            st.markdown(f"""
                                <div class="rider-card">
                                    <h4 style="margin:0 0 10px 0; color:#ff7a00;">Dorsal {dorsal_str}</h4>
                                    <p style="font-weight:bold; font-size:16px; margin:0 0 10px 0; color:white; min-height:40px;">{nombre_competidor}</p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            try:
                                st.image(url_foto_convertida, use_container_width=True)
                            except Exception:
                                st.image("https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=256&auto=format&fit=crop", caption="[Foto no disponible]", use_container_width=True)
                            
                            # Selector de posición del 1 al 4 para el Juez
                            opciones_pos = ["-- Seleccionar --", "1ra Posición", "2da Posición", "3ra Posición", "4ta Posición", "DNF (No finalizó)", "DSQ (Descalificado)"]
                            default_idx = 0
                            if pos_actual in [1, 2, 3, 4]:
                                default_idx = pos_actual
                            elif corr.get('estado') == 'DNF':
                                default_idx = 5
                            elif corr.get('estado') == 'DSQ':
                                default_idx = 6

                            seleccion_pos = st.selectbox(
                                f"Posición Llegada:",
                                opciones_pos,
                                index=default_idx,
                                key=f"pos_{heat_seleccionado}_{dorsal_str}"
                            )
                            
                            # Almacenamiento temporal para validación
                            if "1ra" in seleccion_pos:
                                resultados_ingresados[dorsal_str] = 1
                                posiciones_elegidas.append(1)
                            elif "2da" in seleccion_pos:
                                resultados_ingresados[dorsal_str] = 2
                                posiciones_elegidas.append(2)
                            elif "3ra" in seleccion_pos:
                                resultados_ingresados[dorsal_str] = 3
                                posiciones_elegidas.append(3)
                            elif "4ta" in seleccion_pos:
                                resultados_ingresados[dorsal_str] = 4
                                posiciones_elegidas.append(4)
                            elif "DNF" in seleccion_pos:
                                resultados_ingresados[dorsal_str] = "DNF"
                            elif "DSQ" in seleccion_pos:
                                resultados_ingresados[dorsal_str] = "DSQ"

                    # 3. Guardar seguro del Heat
                    st.markdown("<br>", unsafe_allow_html=True)
                    col_btn_save, _ = st.columns([4, 6])
                    with col_btn_save:
                        if st.button("💾 Cerrar Heat y Registrar Ganadores"):
                            hay_duplicados = len(posiciones_elegidas) != len(set(posiciones_elegidas))
                            num_competidores_completos = len(resultados_ingresados) == len(corredores_heat)
                            
                            if hay_duplicados:
                                st.error("❌ Conflicto: Se han asignado posiciones duplicadas en el heat (ej. dos corredores en 1ra posición). Corrige el error.")
                            elif not num_competidores_completos:
                                st.warning("⚠️ Asegúrate de asignarle un estatus de llegada o posición a todos los corredores antes de guardar.")
                            else:
                                try:
                                    if BracketEngine is not None:
                                        engine = BracketEngine(supabase)
                                        if engine.cerrar_heat(heat_seleccionado, resultados_ingresados):
                                            st.session_state.mostrar_celebracion = True
                                            st.success(f"✅ Resultados guardados correctamente.")
                                            time.sleep(1)
                                            st.rerun()
                                except Exception as ex_db:
                                    st.error(f"Error al actualizar el heat en Supabase: {ex_db}")
                else:
                    st.info("No se encontraron heats activos para controlar.")
        except Exception as e_load_heats:
            st.error(f"Error de carga de estación de control: {e_load_heats}")

    st.markdown("---")
    
    # Zona administrativa para mantenimiento, reajuste y eliminación controlada de brackets
    with st.expander("⚠️ Zona de Control Administrativo"):
        st.write("### 🔄 Control de Heats Individuales (Reclamos / Ajustes)")
        st.write("Si necesitas corregir un resultado, selecciona el Heat correspondiente para restablecerlo a PENDIENTE:")
        
        try:
            # Consultamos los Heats que están registrados actualmente
            res_todos_heats = supabase.table("resultados_bracket").select("heat_id, ronda").execute()
            if res_todos_heats.data:
                heats_existentes = list(set([r['heat_id'] for r in res_todos_heats.data]))
                heats_existentes.sort()
                
                col_heat_sel, col_btn_sel = st.columns([7, 3])
                with col_heat_sel:
                    heat_a_reabrir = st.selectbox("Seleccionar Heat a Restablecer:", heats_existentes)
                with col_btn_sel:
                    st.write("<br>", unsafe_allow_html=True)
                    if st.button("🔓 Reabrir Heat"):
                        try:
                            engine = BracketEngine(supabase)
                            if engine.restablecer_heat(heat_a_reabrir):
                                st.success(f"✅ {heat_a_reabrir} reabierto con éxito.")
                                time.sleep(1)
                                st.rerun()
                        except Exception as e_ind_reset:
                            st.error(f"Error al reabrir heat: {e_ind_reset}")
            else:
                st.info("No hay heats generados todavía para restablecer.")
        except Exception as e_load_admin:
            st.error(f"Error al cargar el panel administrativo de heats: {e_load_admin}")

        st.markdown("<hr style='border: 1px dashed #475569;'/>", unsafe_allow_html=True)
        st.write("### 🚨 Borrado Completo")
        st.write("Esta sección te permite restablecer la tabla completa si deseas reiniciar todo el cuadro.")
        
        # Caja de seguridad para evitar duplicaciones por doble pulsación
        confirmar_reset_bracket = st.checkbox("Confirmo que deseo ELIMINAR por completo los brackets actuales y sus posiciones en Supabase", value=False)
        
        if st.button("🗑️ REESTABLECER Y ELIMINAR BRACKETS"):
            if confirmar_reset_bracket:
                try:
                    # Limpiamos los registros de la tabla de brackets
                    supabase.table("resultados_bracket").delete().neq("dorsal", 0).execute()
                    st.success("🏁 Brackets eliminados correctamente en Supabase. El sistema ha quedado listo para armar un nuevo torneo.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e_del:
                    st.error(f"Error al limpiar la tabla resultados_bracket: {e_del}")
            else:
                st.error("⚠️ Por seguridad, debes marcar la casilla de confirmación antes de restablecer los brackets.")

# ==========================================
# MODULO: 🏆 CUADRO DE HONOR Y RANKINGS (PREMIACIÓN DE 4 ATLETAS)
# ==========================================
elif "🏆 Cuadro de Honor y Rankings" in opcion_menu:
    st.subheader("🏆 Resultados Finales: Cuadro de Honor & Rankings")
    
    try:
        res_b = supabase.table("resultados_bracket").select("*").execute()
        res_i = supabase.table("inscritos_valida").select("dorsal, categoria_evento, riders_master(nombre, foto_url)").execute()
        res_tt = supabase.table("clasificacion_tt").select("dorsal, top_speed").execute()
        
        df_b = pd.DataFrame(res_b.data) if res_b.data else pd.DataFrame()
        df_i = pd.DataFrame(res_i.data) if res_i.data else pd.DataFrame()
        df_tt = pd.DataFrame(res_tt.data) if res_tt.data else pd.DataFrame()
        
        tab_podio, tab_speed = st.tabs(["🥇 Cuadro de Honor (Podio 4 Finalistas)", "⚡ Speed Trap: Ranking de Velocidad"])
        
        # --- TAB: CUADRO DE HONOR (PODIOS DE 4) ---
        with tab_podio:
            if df_b.empty or df_i.empty:
                st.info("ℹ️ Esperando la finalización y cierre de las finales para calcular el Cuadro de Honor.")
            else:
                # SEGURO CONTRA ERRORES: Convertimos todo a string antes de cruzar los datos
                df_b['dorsal'] = df_b['dorsal'].astype(str)
                df_i['dorsal'] = df_i['dorsal'].astype(str)

                # Extraemos los datos relacionales de riders_master
                df_i['nombre'] = df_i['riders_master'].apply(lambda x: x.get('nombre', 'Desconocido') if isinstance(x, dict) else "Desconocido")
                df_i['foto_url'] = df_i['riders_master'].apply(lambda x: x.get('foto_url') if isinstance(x, dict) else None)
                
                # Unimos brackets e inscritos
                df_results = pd.merge(df_b, df_i, on="dorsal")
                categorias_activas = sorted(df_results['categoria_evento'].unique().tolist())
                
                for cat in categorias_activas:
                    st.markdown(f"## 🏁 Categoría: {cat} 🏁")
                    
                    # Filtramos los corredores de esta categoría en la Gran Final
                    df_cat_final = df_results[(df_results['categoria_evento'] == cat) & (df_results['ronda'] == 'Gran Final')]
                    
                    if df_cat_final.empty:
                        st.info(f"Las finales de la categoría {cat} aún no han finalizado.")
                    else:
                        df_cat_final = df_cat_final.sort_values(by="posicion_heat")
                        
                        # Extraemos las 4 posiciones del podio de la Gran Final
                        campeon = df_cat_final[df_cat_final['posicion_heat'] == 1].iloc[0] if len(df_cat_final[df_cat_final['posicion_heat'] == 1]) > 0 else None
                        segundo = df_cat_final[df_cat_final['posicion_heat'] == 2].iloc[0] if len(df_cat_final[df_cat_final['posicion_heat'] == 2]) > 0 else None
                        tercero = df_cat_final[df_cat_final['posicion_heat'] == 3].iloc[0] if len(df_cat_final[df_cat_final['posicion_heat'] == 3]) > 0 else None
                        cuarto = df_cat_final[df_cat_final['posicion_heat'] == 4].iloc[0] if len(df_cat_final[df_cat_final['posicion_heat'] == 4]) > 0 else None
                        
                        # PODIO AMPLIADO A 4 COLUMNAS (2do | 1ro | 3ro | 4to)
                        col_seg, col_camp, col_ter, col_cua = st.columns([1, 1.2, 1, 1])
                        
                        with col_seg:
                            st.write("") # Margen para simular escalón
                            if segundo is not None:
                                img_url = resolver_ruta_imagen(segundo['foto_url'])
                                st.markdown("""
                                    <div class="podium-box" style="background-color: #1e293b; border-top: 6px solid #94a3b8;">
                                        <h2 style='margin:0; color:#94a3b8; font-size:18px;'>🥈 2° Lugar</h2>
                                    </div>
                                """, unsafe_allow_html=True)
                                st.image(img_url, use_container_width=True)
                                st.markdown(f"<h3 style='text-align:center; font-size:16px;'>{segundo['nombre']}</h3>", unsafe_allow_html=True)
                                st.markdown(f"<p style='text-align:center; font-weight:bold; color:#ff7a00;'>Dorsal {segundo['dorsal']}</p>", unsafe_allow_html=True)
                        
                        with col_camp:
                            if campeon is not None:
                                img_url = resolver_ruta_imagen(campeon['foto_url'])
                                st.markdown("""
                                    <div class="podium-box" style="background-color: #1e1b4b; border: 3px solid #eab308; border-top: 8px solid #eab308;">
                                        <h1 style='margin:0; color:#eab308; font-size:22px;'>🥇 CAMPEÓN</h1>
                                    </div>
                                """, unsafe_allow_html=True)
                                st.image(img_url, use_container_width=True)
                                st.markdown(f"<h2 style='text-align:center; color:#eab308; font-size:20px;'>{campeon['nombre']}</h2>", unsafe_allow_html=True)
                                st.markdown(f"<p style='text-align:center; font-weight:bold; color:#ff7a00; font-size:18px;'>Dorsal {campeon['dorsal']}</p>", unsafe_allow_html=True)
                        
                        with col_ter:
                            st.write("") 
                            if tercero is not None:
                                img_url = resolver_ruta_imagen(tercero['foto_url'])
                                st.markdown("""
                                    <div class="podium-box" style="background-color: #1e293b; border-top: 6px solid #b45309;">
                                        <h2 style='margin:0; color:#b45309; font-size:18px;'>🥉 3° Lugar</h2>
                                    </div>
                                """, unsafe_allow_html=True)
                                st.image(img_url, use_container_width=True)
                                st.markdown(f"<h3 style='text-align:center; font-size:16px;'>{tercero['nombre']}</h3>", unsafe_allow_html=True)
                                st.markdown(f"<p style='text-align:center; font-weight:bold; color:#ff7a00;'>Dorsal {tercero['dorsal']}</p>", unsafe_allow_html=True)

                        with col_cua:
                            st.write("") 
                            if cuarto is not None:
                                img_url = resolver_ruta_imagen(cuarto['foto_url'])
                                st.markdown("""
                                    <div class="podium-box" style="background-color: #1e293b; border-top: 6px solid #0052ff;">
                                        <h2 style='margin:0; color:#0052ff; font-size:18px;'>🏅 4° Lugar</h2>
                                    </div>
                                """, unsafe_allow_html=True)
                                st.image(img_url, use_container_width=True)
                                st.markdown(f"<h3 style='text-align:center; font-size:16px;'>{cuarto['nombre']}</h3>", unsafe_allow_html=True)
                                st.markdown(f"<p style='text-align:center; font-weight:bold; color:#ff7a00;'>Dorsal {cuarto['dorsal']}</p>", unsafe_allow_html=True)
                    st.markdown("---")
                    
        # --- TAB: SPEED TRAP (TOP SPEED POR CATEGORIA) ---
        with tab_speed:
            st.markdown("## ⚡ Radar de Velocidad: Speed Trap de la Válida")
            
            if df_tt.empty or df_i.empty:
                st.info("ℹ️ No hay registros de velocidad en pista todavía.")
            else:
                # SEGURO CONTRA ERRORES: Convertimos todo a string antes de cruzar los datos
                df_tt['dorsal'] = df_tt['dorsal'].astype(str)
                df_i['dorsal'] = df_i['dorsal'].astype(str)

                df_i['nombre'] = df_i['riders_master'].apply(lambda x: x.get('nombre', 'Desconocido') if isinstance(x, dict) else "Desconocido")
                df_speed_master = pd.merge(df_tt, df_i, on="dorsal")
                df_speed_master['top_speed'] = pd.to_numeric(df_speed_master['top_speed'], errors='coerce').fillna(0.0)
                df_speed_master = df_speed_master[df_speed_master['top_speed'] > 0.0]
                
                if df_speed_master.empty:
                    st.info("Esperando registros de velocidad en la clasificación.")
                else:
                    speed_king = df_speed_master.sort_values(by="top_speed", ascending=False).iloc[0]
                    st.markdown(f"""
                        <div style='background: linear-gradient(135deg, #1e1b4b 0%, #311005 100%); padding: 25px; border-radius: 12px; margin-bottom: 30px; border: 2px solid #ff7a00; text-align: center;'>
                            <h3 style='margin:0; color:#ff7a00; font-size:24px;'>🔥 SPEED KING / QUEEN DE LA VÁLIDA 🔥</h3>
                            <h1 style='margin:10px 0; font-size:46px; color:#ffffff;'>{speed_king['nombre']}</h1>
                            <p style='margin:0; font-size:22px; font-weight:bold; color:#0052ff;'>⚡ {speed_king['top_speed']:.2f} km/h (Dorsal {speed_king['dorsal']} - {speed_king['categoria_evento']})</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    cats_con_velocidad = sorted(df_speed_master['categoria_evento'].unique().tolist())
                    categoria_seleccionada = st.selectbox("🎯 Filtrar Radar de Velocidad por Categoría:", cats_con_velocidad)
                    
                    df_speed_cat = df_speed_master[df_speed_master['categoria_evento'] == categoria_seleccionada]
                    df_speed_cat = df_speed_cat.sort_values(by="top_speed", ascending=False).reset_index(drop=True)
                    df_speed_cat.index = df_speed_cat.index + 1
                    
                    st.markdown(f"### 🏁 Radar de Velocidad: {categoria_seleccionada}")
                    
                    for idx, row in df_speed_cat.iterrows():
                        col_rank, col_nombre, col_bar = st.columns([1, 4, 5])
                        with col_rank:
                            st.write(f"### #{idx}")
                        with col_nombre:
                            st.write(f"**{row['nombre']}** (Dorsal {row['dorsal']})")
                        with col_bar:
                            porcentaje_velocidad = min(float(row['top_speed']) / 100.0, 1.0)
                            st.progress(porcentaje_velocidad)
                            st.write(f"⚡ {row['top_speed']:.2f} km/h")
                        st.markdown("<hr style='margin:5px 0; border: 1px solid #111827;'/>", unsafe_allow_html=True)
    except Exception as e_main_ranks:
        st.error(f"Error de carga de resultados: {e_main_ranks}")
        
# ==============================================================================
# MODULO: 🗂️ HISTORIAL DE VÁLIDAS (VISTA PROFESIONAL)
# ==============================================================================
elif "🗂️ Historial de Válidas" in opcion_menu:
    st.title("🗂️ Archivo de Competencias")
    st.markdown("Explora los resultados oficiales, tiempos y brackets de las válidas pasadas.")

    if "evento_seleccionado" not in st.session_state:
        st.session_state.evento_seleccionado = None

    if st.session_state.evento_seleccionado is None:
        try:
            # 1. Traer todos los eventos
            res_eventos = supabase.table("historial_eventos").select("*").order("orden_valida").execute()
            eventos_db = res_eventos.data
            
            # 2. OPTIMIZACIÓN: Traer todos los sponsors mapeados de golpe
            sponsors_by_event = {}
            try:
                # ¡NUEVO! Añadimos 'id_perfil' y 'categoria' a la consulta para poder ordenarlos
                res_sponsors = supabase.table("eventos_sponsors").select("evento_id, id_perfil, jerarquia, directorio_partners(nombre, foto, instagram, categoria)").execute()
                if res_sponsors.data:
                    for sp in res_sponsors.data:
                        e_id = sp.get('evento_id')
                        if e_id not in sponsors_by_event:
                            sponsors_by_event[e_id] = []
                        sponsors_by_event[e_id].append(sp)
            except Exception as e_sp:
                st.sidebar.warning("No se pudo conectar el paddock de partners.")

            if not eventos_db:
                st.info("No hay eventos registrados en el historial.")
            else:
                for evento in eventos_db:
                    ev_id = evento.get('evento_id')
                    url_img = evento.get('afiche_url', '')
                    nombre = evento.get('nombre_carrera', 'Evento')
                    titulo = evento.get('titulo_oficial', '')
                    ubicacion = evento.get('ubicacion', 'Ubicación')
                    ciudad = evento.get('ciudad', 'Ciudad')
                    pais_code = str(evento.get('pais', 've')).lower().replace("🇻🇪", "ve")
                    fecha = evento.get('fecha_exacta', '')
                    participantes = evento.get('participantes_inscritos', 0)
                    distancia = evento.get('distancia', 'N/A')
                    costo = evento.get('costo_inscripcion', '$0')
                    
                    cats = str(evento.get('categorias_activas', 'Open_Skate')).split(',')
                    badges_html = ""
                    for cat in cats:
                        texto_cat = cat.strip().replace("_", "<br>")
                        badges_html += f"""
                        <span style='background-color: #1e293b; border: 1px solid #475569; color: #cbd5e1; padding: 6px 10px; border-radius: 6px; font-size: 10px; font-weight: bold; text-align: center; display: inline-block; line-height: 1.1; min-width: 60px; margin-right: 5px; margin-bottom: 5px;'>
                            {texto_cat}
                        </span>"""

                    with st.container(border=True):
                        col_datos, col_img = st.columns([0.6, 0.4])
                        
                        with col_datos:
                            st.subheader(nombre)
                            st.caption(f"⭐ {titulo}")
                            flag_url = f"https://flagcdn.com/w40/{pais_code}.png"
                            st.markdown(f'<img src="{flag_url}" width="20"> &nbsp; **{ciudad}** &nbsp; | &nbsp; 📍 {ubicacion}', unsafe_allow_html=True)
                            st.write(f"📅 {fecha}")
                            st.markdown(f"📏 {distancia} | 👥 {participantes} Riders | 🎟️ {costo}")
                            st.markdown(badges_html, unsafe_allow_html=True)
                            st.write("") 
                            if st.button(f"Ver Resultados - {nombre}", key=f"btn_{evento.get('id')}"):
                                st.session_state.evento_seleccionado = evento
                                st.rerun()
                                
                        with col_img:
                            if url_img:
                                st.image(url_img, use_container_width=True)
                            else:
                                st.warning("Sin afiche")

                        # --- BLOQUE INFERIOR: Paddock al 100% del ancho ---
                        sponsors_evento = sponsors_by_event.get(ev_id, [])
                        if sponsors_evento:
                            # 1. Separar y clasificar los sponsors
                            priority_ids = ['SPOND17', 'SPOND13', 'SPOND22']
                            priorities, organizers, standard_sponsors, promoters = [], [], [], []
                            
                            for sp in sponsors_evento:
                                d_partner = sp.get('directorio_partners')
                                if not d_partner: continue
                                
                                id_perf = str(sp.get('id_perfil', '')).strip()
                                cat = str(d_partner.get('categoria', '')).strip().upper()
                                
                                if cat == 'PROMOTORES':
                                    promoters.append(sp)
                                else:
                                    if id_perf in priority_ids:
                                        priorities.append(sp)
                                    elif cat == 'ORGANIZADORES':
                                        organizers.append(sp)
                                    else:
                                        standard_sponsors.append(sp)
                                        
                            # 2. Ordenar explícitamente a los prioritarios (Federación y Comisiones)
                            priorities.sort(key=lambda x: priority_ids.index(str(x.get('id_perfil')).strip()))
                            
                            # 3. Unir la lista principal de Official Partners
                            official_partners = priorities + organizers + standard_sponsors
                            
                            st.markdown("<hr style='margin: 15px 0 10px 0; border: 1px solid #1e293b;'/>", unsafe_allow_html=True)
                            
                            # Estilos CSS generales para el Paddock
                            paddock_html = """
                            <style>
                                .paddock-wrap { display: flex; flex-wrap: wrap; gap: 15px; align-items: center; padding-bottom: 20px; }
                                .sponsor-badge {
                                    background-color: transparent;
                                    border: none;
                                    height: 65px;
                                    min-width: 100px;
                                    padding: 5px;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    transition: all 0.3s ease;
                                    cursor: pointer;
                                }
                                .sponsor-badge:hover {
                                    transform: scale(1.08);
                                    filter: drop-shadow(0 4px 8px rgba(255, 122, 0, 0.4));
                                }
                                .sp-logo { max-height: 55px; max-width: 140px; object-fit: contain; }
                                .sp-text { color: #f1f5f9; font-weight: bold; font-size: 0.9rem; text-transform: uppercase; }
                                .paddock-title { font-size: 0.7rem; color: #64748b; margin-bottom: 5px; text-transform: uppercase; font-weight: bold; letter-spacing: 1px; }
                            </style>
                            """
                            
                            # --- RENDERIZAR GRUPO 1: OFFICIAL PARTNERS ---
                            if official_partners:
                                paddock_html += "<p class='paddock-title'>Official Partners</p><div class='paddock-wrap'>"
                                for sp in official_partners:
                                    d_partner = sp.get('directorio_partners')
                                    nom_sp = d_partner.get('nombre', 'Sponsor')
                                    url_logo = resolver_ruta_imagen(d_partner.get('foto'))
                                    insta_sp = d_partner.get('instagram')
                                    
                                    si_logo = f'<img src="{url_logo}" class="sp-logo" title="{nom_sp}" onerror="this.style.display=\'none\'">' if url_logo else f'<span class="sp-text">{nom_sp}</span>'
                                        
                                    if insta_sp and str(insta_sp).lower() not in ['nan', 'none', '']:
                                        paddock_html += f'<a href="{insta_sp}" target="_blank" style="text-decoration:none;"><div class="sponsor-badge">{si_logo}</div></a>'
                                    else:
                                        paddock_html += f'<div class="sponsor-badge" title="{nom_sp}">{si_logo}</div>'
                                paddock_html += "</div>"
                                
                            # --- RENDERIZAR GRUPO 2: Event Promoters ---
                            if promoters:
                                paddock_html += "<p class='paddock-title'>Event Promoters</p><div class='paddock-wrap'>"
                                for sp in promoters:
                                    d_partner = sp.get('directorio_partners')
                                    nom_sp = d_partner.get('nombre', 'Promotor')
                                    url_logo = resolver_ruta_imagen(d_partner.get('foto'))
                                    insta_sp = d_partner.get('instagram')
                                    
                                    si_logo = f'<img src="{url_logo}" class="sp-logo" title="{nom_sp}" onerror="this.style.display=\'none\'">' if url_logo else f'<span class="sp-text">{nom_sp}</span>'
                                        
                                    if insta_sp and str(insta_sp).lower() not in ['nan', 'none', '']:
                                        paddock_html += f'<a href="{insta_sp}" target="_blank" style="text-decoration:none;"><div class="sponsor-badge">{si_logo}</div></a>'
                                    else:
                                        paddock_html += f'<div class="sponsor-badge" title="{nom_sp}">{si_logo}</div>'
                                paddock_html += "</div>"
                                
                            st.markdown(paddock_html, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error cargando historial: {e}")

    # VISTA B: DETALLE DEL EVENTO
    else:
        if st.button("⬅️ Volver al Historial"):
            st.session_state.evento_seleccionado = None
            st.rerun()
            
        evento = st.session_state.evento_seleccionado
        st.title(f"🏆 {evento.get('nombre_carrera')}")
        st.subheader(evento.get('titulo_oficial'))
        
        tab1, tab2, tab3 = st.tabs(["⏱️ Qualy", "📊 Brackets", "🥇 Podio"])
        
        with tab1:
            import pandas as pd
            ev_id = evento.get('evento_id') 
            
            if ev_id:
                try:
                    res_qualy = supabase.table("resultados_qualy").select("*").eq("evento_id", ev_id).execute()
                    datos_qualy = res_qualy.data
                    
                    if datos_qualy:
                        df = pd.DataFrame(datos_qualy)
                        
                        # --- Lógica de Ordenamiento Personalizado ---
                        lista_categorias = sorted(df['Categoria'].unique())
                        if 'Open_Skate' in lista_categorias:
                            lista_categorias.remove('Open_Skate')
                            lista_categorias.insert(0, 'Open_Skate')
                        
                        cat_seleccionada = st.selectbox("🎯 Filtrar por Categoría:", lista_categorias)
                        df_filtrado = df[df['Categoria'] == cat_seleccionada].sort_values(by='Ranking_General', ascending=True)
                        
                        columnas_visibles = ['Ranking_General', 'Dorsal', 'Nombre', 'Tiempo_Manga_1', 'Tiempo_Manga_2', 'Mejor_Tiempo', 'Bonus_Qualy']
                        st.dataframe(
                            df_filtrado[columnas_visibles], 
                            use_container_width=True, 
                            hide_index=True,
                            column_config={"Ranking_General": st.column_config.NumberColumn("Rank", format="%d")}
                        )
                    else:
                        st.info("No hay resultados cargados.")
                except Exception as e:
                    st.error(f"Error al cargar la tabla: {e}")

        with tab2:
            import re
            import streamlit.components.v1 as components
            
            ev_id = evento.get('evento_id')
            if ev_id:
                try:
                    res_brackets = supabase.table("brackets_eventos").select("*").eq("evento_id", ev_id).execute()
                    datos_brackets = res_brackets.data
                    
                    if datos_brackets:
                        df_b = pd.DataFrame(datos_brackets)
                        df_b['categoria'] = df_b['categoria'].astype(str).str.strip()
                        
                        lista_cats_b = sorted(df_b['categoria'].unique())
                        if 'Open_Skate' in lista_cats_b:
                            lista_cats_b.remove('Open_Skate')
                            lista_cats_b.insert(0, 'Open_Skate')
                        
                        cat_b = st.selectbox("🎯 Categoría:", lista_cats_b, key="cat_tree_pro")
                        df_f = df_b[df_b['categoria'] == cat_b].copy()

                        orden_rondas = {
                            "Dieciseisavos": 0, "Octavos": 1, "Cuartos": 2, "Semifinal": 3, 
                            "Final de Consolación": 4, "Final de Consolidación": 4, "Final": 5, "Gran Final": 5
                        }
                        df_f['orden'] = df_f['Ronda'].map(orden_rondas).fillna(99)
                        
                        def limpiar_numero(val):
                            if pd.isna(val) or val == "" or str(val).lower() == 'nan': return "-"
                            try: return str(int(float(val)))
                            except: return str(val)

                        def limpiar_heat(val):
                            val = str(val).strip()
                            match = re.search(r'(Heat\s*\d+)', val, re.IGNORECASE)
                            if match: return match.group(1).title()
                            return val

                        df_f['Dorsal'] = df_f['Dorsal'].apply(limpiar_numero)
                        df_f['Pos_llegada'] = df_f['Pos_llegada'].apply(limpiar_numero)
                        df_f['Heat_Clean'] = df_f['Heat'].apply(limpiar_heat)

                        css_brackets = """
                        <style>
                            .bracket-wrapper { 
                                display: flex; flex-direction: row; gap: 40px; overflow-x: auto; 
                                padding: 20px 0; align-items: center; justify-content: flex-start; 
                                background-color: #000000; border-radius: 8px; padding: 20px; 
                                cursor: grab; scroll-behavior: smooth;
                            }
                            .bracket-wrapper:active { cursor: grabbing; }
                            .bracket-wrapper::-webkit-scrollbar { height: 8px; }
                            .bracket-wrapper::-webkit-scrollbar-track { background: #111111; border-radius: 4px; }
                            .bracket-wrapper::-webkit-scrollbar-thumb { background: #ff6600; border-radius: 4px; }
                            .column-round { display: flex; flex-direction: column; justify-content: center; gap: 15px; }
                            .matchup-box { background: #111111; border: 1px solid #ff6600; border-radius: 6px; padding: 8px 12px; box-shadow: 0 0 10px rgba(255, 102, 0, 0.15); min-width: 360px; max-width: 420px; }
                            .heat-title { font-size: 0.75rem; color: #ff6600; margin-bottom: 6px; text-transform: uppercase; font-weight: 800; border-bottom: 1px solid #333333; padding-bottom: 4px; text-align: center; letter-spacing: 2px;}
                            .rider-item { display: flex; justify-content: space-between; align-items: center; padding: 4px 8px; border-radius: 4px; margin-bottom: 4px; border: 1px solid #222222; }
                            .rider-info { font-size: 0.85rem; font-weight: 600; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; pointer-events: none; }
                            .rider-info span { color: #888888; font-size: 0.75rem; margin-right: 6px; }
                            .rider-stats { text-align: right; font-size: 0.75rem; font-weight: bold; display: flex; flex-direction: column; align-items: flex-end; min-width: 100px; margin-left: 15px; pointer-events: none; }
                            .estado-text { font-size: 0.6rem; text-transform: uppercase; margin-top: 2px; padding: 1px 4px; border-radius: 2px;}
                            .winner-item { border-left: 4px solid #22c55e; background: linear-gradient(90deg, rgba(34,197,94,0.15) 0%, rgba(0,0,0,0) 60%); }
                            .winner-item .estado-text { color: #22c55e; }
                            .loser-item { border-left: 4px solid #ef4444; background: linear-gradient(90deg, rgba(239,68,68,0.1) 0%, rgba(0,0,0,0) 60%); opacity: 0.85; }
                            .loser-item .estado-text { color: #ef4444; }
                            .bye-item { border-left: 4px solid #444444; background: linear-gradient(90deg, rgba(68,68,68,0.15) 0%, rgba(0,0,0,0) 60%); opacity: 0.6; }
                            .bye-item .rider-info { color: #777777; font-style: italic; }
                            .consolacion-item { border-left: 4px solid #e2e8f0; background: linear-gradient(90deg, rgba(226,232,240,0.1) 0%, rgba(0,0,0,0) 60%); opacity: 0.9; }
                            .consolacion-item .estado-text { color: #e2e8f0; }
                            .podio-1 { border-left: 4px solid #ffd700; background: linear-gradient(90deg, rgba(255,215,0,0.18) 0%, rgba(0,0,0,0) 60%); }
                            .podio-1 .estado-text { color: #ffd700; }
                            .podio-2 { border-left: 4px solid #c0c0c0; background: linear-gradient(90deg, rgba(192,192,192,0.12) 0%, rgba(0,0,0,0) 60%); }
                            .podio-2 .estado-text { color: #c0c0c0; }
                            .podio-3 { border-left: 4px solid #cd7f32; background: linear-gradient(90deg, rgba(205,127,50,0.12) 0%, rgba(0,0,0,0) 60%); }
                            .podio-3 .estado-text { color: #cd7f32; }
                            .podio-4 { border-left: 4px solid #38bdf8; background: linear-gradient(90deg, rgba(56,189,248,0.1) 0%, rgba(0,0,0,0) 60%); }
                            .podio-4 .estado-text { color: #38bdf8; }
                        </style>
                        """

                        html_tree = '<div class="bracket-wrapper" id="bracket-container">'
                        rondas_presentes = sorted(df_f['orden'].unique())
                        for orden in rondas_presentes:
                            ronda_nombre = df_f[df_f['orden'] == orden]['Ronda'].iloc[0]
                            mostrar_ronda = "Gran Final" if ronda_nombre == "Final" else ronda_nombre
                            is_consolacion = "Consol" in ronda_nombre
                            is_gran_final = ronda_nombre == "Final"

                            html_tree += '<div class="column-round">'
                            ronda_data = df_f[df_f['orden'] == orden].copy()
                            ronda_data['heat_num'] = ronda_data['Heat_Clean'].apply(
                                lambda x: int(re.search(r'\d+', str(x)).group()) if re.search(r'\d+', str(x)) else 999
                            )
                            ronda_data = ronda_data.sort_values('heat_num')
                            
                            for heat in ronda_data['Heat_Clean'].unique():
                                heat_riders = ronda_data[ronda_data['Heat_Clean'] == heat].copy()
                                heat_riders['sort_pos'] = pd.to_numeric(heat_riders['Pos_llegada'].replace('-', '99'), errors='coerce').fillna(99)
                                heat_riders = heat_riders.sort_values('sort_pos')
                                
                                html_tree += '<div class="matchup-box">'
                                html_tree += f'<div class="heat-title">{heat} | {mostrar_ronda}</div>'
                                
                                for _, rider in heat_riders.iterrows():
                                    estado_txt = str(rider.get('Estado', ''))
                                    if estado_txt.lower() in ['nan', 'none']: estado_txt = ''
                                    
                                    nombre_rider = str(rider.get('Nombre', ''))
                                    dorsal_rider = rider.get('Dorsal', '-')
                                    pos_rider = str(rider.get('Pos_llegada', '-'))
                                    
                                    if nombre_rider.lower() in ['nan', 'none', '']:
                                        nombre_rider = "BYE"
                                        dorsal_rider = "-"
                                        pos_rider = "-"
                                        estado_txt = ""
                                        cls = "bye-item"
                                    elif is_gran_final:
                                        if pos_rider == "1": cls = "podio-1"
                                        elif pos_rider == "2": cls = "podio-2"
                                        elif pos_rider == "3": cls = "podio-3"
                                        elif pos_rider == "4": cls = "podio-4"
                                        else: cls = "loser-item" 
                                    elif is_consolacion:
                                        cls = "consolacion-item"
                                    else:
                                        is_winner = "Avanza" in estado_txt or "1er" in estado_txt or "2do" in estado_txt
                                        cls = "winner-item" if is_winner else "loser-item"
                                    
                                    html_tree += f'<div class="rider-item {cls}">'
                                    if dorsal_rider != "-":
                                        html_tree += f'<div class="rider-info"><span>#{dorsal_rider}</span> {nombre_rider}</div>'
                                    else:
                                        html_tree += f'<div class="rider-info">{nombre_rider}</div>'
                                        
                                    html_tree += '<div class="rider-stats">'
                                    if pos_rider != "-":
                                        html_tree += f'P{pos_rider}'
                                    if estado_txt:
                                        html_tree += f'<span class="estado-text">{estado_txt}</span>'
                                    html_tree += '</div></div>'
                                    
                                html_tree += '</div>' 
                            html_tree += '</div>' 
                        html_tree += '</div>' 

                        st.markdown(css_brackets + html_tree, unsafe_allow_html=True)

                        components.html("""
                            <script>
                                const doc = window.parent.document;
                                const sliders = doc.querySelectorAll('.bracket-wrapper');
                                sliders.forEach(slider => {
                                    let isDown = false; let startX; let scrollLeft;
                                    slider.addEventListener('mousedown', (e) => {
                                        isDown = true; startX = e.pageX - slider.offsetLeft; scrollLeft = slider.scrollLeft;
                                    });
                                    slider.addEventListener('mouseleave', () => { isDown = false; });
                                    slider.addEventListener('mouseup', () => { isDown = false; });
                                    slider.addEventListener('mousemove', (e) => {
                                        if(!isDown) return; e.preventDefault();
                                        const x = e.pageX - slider.offsetLeft; const walk = (x - startX) * 1.5;
                                        slider.scrollLeft = scrollLeft - walk;
                                    });
                                });
                            </script>
                        """, height=0, width=0)
                except Exception as e:
                    st.error(f"Error cargando brackets: {e}")

        with tab3:
            ev_id = evento.get('evento_id')
            if ev_id:
                try:
                    res_podio = supabase.table("podio_eventos") \
                        .select("*, riders_master(nombre, foto_url, instagram, estado_pais)") \
                        .eq("evento_id", ev_id).execute()
                    datos_podio = res_podio.data
                    
                    if datos_podio:
                        df_p = pd.DataFrame(datos_podio)
                        df_riders = pd.json_normalize(df_p['riders_master'])
                        df_final = pd.concat([df_p.drop(columns=['riders_master']), df_riders], axis=1)
                        
                        lista_cats_p = sorted(df_final['categoria'].unique())
                        if 'Open_Skate' in lista_cats_p:
                            lista_cats_p.remove('Open_Skate')
                            lista_cats_p.insert(0, 'Open_Skate')
                        
                        cat_p = st.selectbox("🎯 Categoría:", lista_cats_p, key="cat_podio")
                        df_cat = df_final[df_final['categoria'] == cat_p].sort_values('posicion_final')

                        html_podio = """
                        <style>
                            body { background-color: #000; color: #fff; font-family: sans-serif; }
                            .podio-container { display: flex; justify-content: center; gap: 15px; margin-bottom: 30px; }
                            .podio-item { text-align: center; width: 100px; }
                            .podio-img { width: 80px; height: 80px; object-fit: cover; border-radius: 50%; border: 3px solid #ff6600; }
                            .podio-rank { font-weight: bold; margin-bottom: 5px; font-size: 0.9rem; }
                            .list-item { display: flex; align-items: center; padding: 12px; border-bottom: 1px solid #222; background: #0a0a0a; }
                            .rider-photo-small { width: 45px; height: 45px; object-fit: cover; border-radius: 50%; margin-right: 15px; border: 1px solid #333; }
                            .insta-link { margin-left: auto; }
                            .insta-icon { width: 28px; height: 28px; }
                        </style>
                        <div class="podio-container">
                        """

                        for pos in [1, 2, 3, 4]:
                            rider = df_cat[df_cat['posicion_final'] == pos]
                            if not rider.empty:
                                r = rider.iloc[0]
                                placeholder = f"https://ui-avatars.com/api/?name={str(r['nombre']).replace(' ', '+')}&background=ff6600&color=fff"
                                
                                # --- PARSER DE IMAGEN SEGURO RESTABLECIDO ---
                                foto_raw = r['foto_url']
                                if pd.notnull(foto_raw) and str(foto_raw).strip() != "" and str(foto_raw).lower() != 'nan':
                                    foto_str = str(foto_raw).strip()
                                    drive_id_match = re.search(r'(?:id=|\/d\/|folders\/)([a-zA-Z0-9-_]{25,45})', foto_str)
                                    foto = f"https://drive.google.com/uc?export=download&id={drive_id_match.group(1)}" if drive_id_match else foto_str
                                else:
                                    foto = placeholder
                                    
                                color = "#ffd700" if pos==1 else "#c0c0c0" if pos==2 else "#cd7f32" if pos==3 else "#38bdf8"
                                html_podio += f"""
                                <div class="podio-item">
                                    <div class="podio-rank" style="color: {color}">{pos}º</div>
                                    <img src="{foto}" class="podio-img" onerror="this.src='{placeholder}';">
                                    <div style="font-size: 0.75rem; margin-top: 5px; font-weight: 600;">{r['nombre']}</div>
                                </div>
                                """
                        html_podio += '</div><hr style="border: 0; border-top: 1px solid #333;">'

                        for _, r in df_cat.iterrows():
                            placeholder = f"https://ui-avatars.com/api/?name={str(r['nombre']).replace(' ', '+')}&background=222&color=fff"
                            
                            # --- PARSER DE IMAGEN SEGURO RESTABLECIDO ---
                            foto_raw = r['foto_url']
                            if pd.notnull(foto_raw) and str(foto_raw).strip() != "" and str(foto_raw).lower() != 'nan':
                                foto_str = str(foto_raw).strip()
                                drive_id_match = re.search(r'(?:id=|\/d\/|folders\/)([a-zA-Z0-9-_]{25,45})', foto_str)
                                foto = f"https://drive.google.com/uc?export=download&id={drive_id_match.group(1)}" if drive_id_match else foto_str
                            else:
                                foto = placeholder
                            
                            flag_html = ""; location_text = ""; pais_crudo = ""
                            val = str(r['estado_pais']).strip() if pd.notnull(r['estado_pais']) else ""
                            
                            if val and val.lower() not in ['nan', 'none']:
                                if '|' in val:
                                    parts = [p.strip() for p in val.split('|')]
                                    pais_crudo = parts[0].lower()
                                    flag_html = f'<img src="https://flagcdn.com/24x18/{pais_crudo}.png" style="vertical-align:middle; margin-right:5px;">'
                                    location_text = parts[1].upper() if len(parts) > 1 else ""
                                elif len(val) <= 3:
                                    pais_crudo = val.lower()
                                    flag_html = f'<img src="https://flagcdn.com/24x18/{pais_crudo}.png" style="vertical-align:middle;">'
                                else:
                                    location_text = val.upper()
                            
                            puntos_carrera = int(r['puntos_totales']) if 'puntos_totales' in r and pd.notnull(r['puntos_totales']) else 0
                            if pais_crudo == "ve":
                                badge_puntos = f'<div style="margin-right: 15px; font-weight: bold; color: #ff6600; background: #222; padding: 4px 8px; border-radius: 4px; border: 1px solid #444; font-size: 0.85rem;">{puntos_carrera} pts</div>'
                            else:
                                badge_puntos = f'<div style="margin-right: 15px; font-weight: bold; color: #888; background: #111; padding: 4px 8px; border-radius: 4px; border: 1px solid #333; font-size: 0.75rem;">Invitado</div>'
                            
                            html_podio += f"""
                            <div class="list-item">
                                <span style="margin-right:15px; font-weight:bold; color:#ff6600;">#{r['posicion_final']}</span>
                                <img src="{foto}" class="rider-photo-small" onerror="this.src='{placeholder}';">
                                <div style="flex-grow: 1;">
                                    <strong>{r['nombre']}</strong><br>
                                    <span style="font-size: 0.75rem; color: #888;">{flag_html} {location_text}</span>
                                </div>
                                {badge_puntos}
                            """
                            if r['instagram']:
                                html_podio += f"""
                                <a href="{r['instagram']}" target="_blank" class="insta-link">
                                    <img src="https://upload.wikimedia.org/wikipedia/commons/e/e7/Instagram_logo_2016.svg" class="insta-icon">
                                </a>
                                """
                            html_podio += "</div>"
                        
                        components.html(html_podio, height=800, scrolling=True)
                    else:
                        st.info("Aún no hay resultados de podio cargados.")
                except Exception as e:
                    st.error(f"Error cargando podio: {e}")

# ==========================================
# MODULO: 🌍 RANKING NACIONAL (TRADING CARDS CON ESTADÍSTICAS)
# ==========================================
elif "🌍 Ranking Nacional" in opcion_menu:
    st.title("🌍 Ranking Nacional 2026")
    st.write("Clasificación oficial acumulada del año en curso basada en el sistema de puntaje WDSC.")

    ANIO_ACTUAL = 2026

    try:
        # 1. Obtener datos del ranking y ahora incluyendo las 5 nuevas columnas de estadísticas gamificadas
        res_ranking = supabase.table("ranking_anual") \
            .select("*, riders_master(nombre, foto_url, estado_pais, instagram, total_eventos, total_finales_top8, total_podios_top4, total_victorias_1er_lugar, total_speed_king)") \
            .eq("anio", ANIO_ACTUAL).execute()
        
        datos_ranking = res_ranking.data

        if not datos_ranking:
            st.info("Aún no se han generado datos para el ranking de este año.")
        else:
            df_r = pd.DataFrame(datos_ranking)
            df_riders = pd.json_normalize(df_r['riders_master'])
            df_final = pd.concat([df_r.drop(columns=['riders_master']), df_riders], axis=1)

            lista_categorias = sorted(df_final['categoria'].unique())
            if 'Open_Skate' in lista_categorias:
                lista_categorias.remove('Open_Skate')
                lista_categorias.insert(0, 'Open_Skate')
            
            cat_seleccionada = st.selectbox("🎯 Filtrar por Categoría:", lista_categorias, key="cat_ranking_gral")
            df_cat = df_final[df_final['categoria'] == cat_seleccionada].sort_values('posicion_ranking')

            # 2. BLINDAJE DE ORDENAMIENTO CRONOLÓGICO Y ALFABÉTICO (EID001 antes que EID002)
            res_historial = supabase.table("podio_eventos") \
                .select("id_rider, puntos_totales, bonus_qualy, evento_id") \
                .eq("categoria", cat_seleccionada) \
                .order("evento_id").execute()
            
            df_historial = pd.DataFrame(res_historial.data) if res_historial.data else pd.DataFrame()

            # --- CSS PARA LAS TARJETAS DE VIDEOJUEGOS ---
            html_content = """
            <style>
                body { background-color: #000; color: #fff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
                .cards-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
                    gap: 20px;
                    padding: 15px;
                }
                .game-card {
                    background: linear-gradient(135deg, #111 0%, #050505 100%);
                    border: 2px solid #333;
                    border-radius: 14px;
                    overflow: hidden;
                    position: relative;
                    transition: transform 0.3s ease, border-color 0.3s ease;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
                }
                .game-card:hover {
                    transform: translateY(-5px);
                    border-color: #ff6600;
                    box-shadow: 0 8px 25px rgba(255, 102, 0, 0.3);
                }
                .img-container {
                    width: 100%;
                    aspect-ratio: 1 / 1;
                    position: relative;
                    background-color: #222;
                    overflow: hidden;
                }
                .rider-img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }
                .rank-badge {
                    position: absolute;
                    top: 10px;
                    left: 10px;
                    background: rgba(0, 0, 0, 0.85);
                    padding: 6px 12px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 1.1rem;
                    border: 1px solid #444;
                    z-index: 10;
                }
                
                /* Efecto Hover Instagram */
                .has-instagram:hover .img-container::after {
                    content: "👉 Ver en Instagram";
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    background: rgba(255, 102, 0, 0.95);
                    color: white;
                    font-weight: bold;
                    text-align: center;
                    padding: 8px;
                    font-size: 0.85rem;
                    transform: translateY(0);
                    transition: transform 0.3s ease;
                    z-index: 20;
                }
                .img-container::after {
                    content: "";
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    transform: translateY(100%);
                    transition: transform 0.3s ease;
                    z-index: 20;
                }

                .card-content {
                    padding: 12px;
                    text-align: center;
                }
                .rider-name {
                    font-size: 1.1rem;
                    font-weight: bold;
                    margin-bottom: 4px;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                .rider-meta {
                    font-size: 0.75rem;
                    color: #888;
                    margin-bottom: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 5px;
                }
                .total-score {
                    background: #ff6600;
                    color: #fff;
                    font-weight: bold;
                    padding: 6px;
                    border-radius: 6px;
                    font-size: 0.9rem;
                    margin-bottom: 12px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                .stats-section {
                    background: rgba(255,255,255,0.03);
                    border-top: 1px solid #222;
                    padding-top: 8px;
                    text-align: left;
                    font-size: 0.7rem;
                    color: #aaa;
                    min-height: 65px;
                }
                .stat-line {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 3px;
                    padding: 0 4px;
                }
                .badge-fastest {
                    background: #00bcff;
                    color: #000;
                    font-weight: bold;
                    font-size: 0.65rem;
                    padding: 2px 5px;
                    border-radius: 3px;
                    display: inline-block;
                    margin-top: 6px;
                    text-align: center;
                    width: 100%;
                }

                /* ESTILOS DE LA NUEVA BARRA GAMIFICADA */
                .gamified-stats {
                    margin-top: 10px;
                    border-top: 1px dashed #444;
                    padding-top: 8px;
                    font-size: 0.7rem;
                    color: #bbb;
                    text-align: left;
                }
                .stat-row {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 4px;
                }
                .stat-row span:last-child {
                    font-weight: bold;
                    color: #fff;
                }
            </style>
            <div class="cards-grid">
            """

            for _, r in df_cat.iterrows():
                id_r = r['id_rider']
                pos = int(r['posicion_ranking'])
                puntos_totales = int(r['puntos_totales'])
                
                # --- NUEVAS ESTADISTICAS GAMIFICADAS MATEMATICAS ---
                t_eventos = int(r['total_eventos']) if 'total_eventos' in r and pd.notnull(r['total_eventos']) else 0
                t_top8 = int(r['total_finales_top8']) if 'total_finales_top8' in r and pd.notnull(r['total_finales_top8']) else 0
                t_top4 = int(r['total_podios_top4']) if 'total_podios_top4' in r and pd.notnull(r['total_podios_top4']) else 0
                t_1er = int(r['total_victorias_1er_lugar']) if 'total_victorias_1er_lugar' in r and pd.notnull(r['total_victorias_1er_lugar']) else 0
                t_speed = int(r['total_speed_king']) if 'total_speed_king' in r and pd.notnull(r['total_speed_king']) else 0
                
                win_rate = (t_1er / t_eventos * 100) if t_eventos > 0 else 0
                podium_rate = (t_top4 / t_eventos * 100) if t_eventos > 0 else 0
                
                # Link de instagram
                insta_url = str(r['instagram']).strip() if 'instagram' in r and pd.notnull(r['instagram']) and str(r['instagram']).strip() != "" and str(r['instagram']).lower() != "nan" else ""

                placeholder = f"https://ui-avatars.com/api/?name={str(r['nombre']).replace(' ', '+')}&background=ff6600&color=fff"
                
                # --- PARSER DE IMAGEN SEGURO EN TARJETA ---
                foto_raw = r['foto_url']
                if pd.notnull(foto_raw) and str(foto_raw).strip() != "" and str(foto_raw).lower() != 'nan':
                    foto_str = str(foto_raw).strip()
                    drive_id_match = re.search(r'(?:id=|\/d\/|folders\/)([a-zA-Z0-9-_]{25,45})', foto_str)
                    foto = f"https://drive.google.com/uc?export=download&id={drive_id_match.group(1)}" if drive_id_match else foto_str
                else:
                    foto = placeholder
                
                badge_color = "#ffd700" if pos==1 else "#c0c0c0" if pos==2 else "#cd7f32" if pos==3 else "#fff"
                
                flag_html = ""; location_text = ""
                val_loc = str(r['estado_pais']).strip() if 'estado_pais' in r and pd.notnull(r['estado_pais']) else ""
                
                if val_loc and val_loc.lower() not in ['nan', 'none']:
                    if '|' in val_loc:
                        parts = [p.strip() for p in val_loc.split('|')]
                        flag_html = f'<img src="https://flagcdn.com/16x12/{parts[0].lower()}.png" style="vertical-align:middle;">'
                        location_text = parts[1].upper() if len(parts) > 1 else ""
                    elif len(val_loc) == 2 and val_loc.isalpha():
                        flag_html = f'<img src="https://flagcdn.com/16x12/{val_loc.lower()}.png" style="vertical-align:middle;">'
                    else:
                        location_text = val_loc.upper()

                leyenda_html = ""
                badge_speed_html = '<div class="badge-fastest">⚡ TOP QUALY</div>' if t_speed > 0 else ""
                
                if not df_historial.empty:
                    # Al estar df_historial pre-ordenado por evento_id desde Supabase, el ciclo de abajo procesa de forma estable EID001 antes de EID002
                    historico_rider = df_historial[df_historial['id_rider'] == id_r]
                    count_valida = 1
                    for _, h in historico_rider.iterrows():
                        nombre_ev = f"Válida {count_valida}"
                        leyenda_html += f"""
                        <div class="stat-line">
                            <span>📊 {nombre_ev}:</span>
                            <span style="color:#fff; font-weight:bold;">{int(h['puntos_totales'])} pts</span>
                        </div>
                        """
                        count_valida += 1

                # Estructura del HTML Gamificado (Carreras y Porcentajes)
                gamified_html = f"""
                <div class="gamified-stats">
                    <div class="stat-row"><span>🏁 Eventos Corridos:</span> <span>{t_eventos}</span></div>
                    <div class="stat-row"><span>🥇 Victorias absolutas:</span> <span>{t_1er} ({win_rate:.0f}%)</span></div>
                    <div class="stat-row"><span>🏆 Podios (Top 4):</span> <span>{t_top4} ({podium_rate:.0f}%)</span></div>
                    <div class="stat-row"><span>🔥 Finales (Top 8):</span> <span>{t_top8}</span></div>
                    {f'<div class="stat-row" style="color:#00bcff;"><span>⚡ Pole Position:</span> <span>{t_speed}</span></div>' if t_speed > 0 else ''}
                </div>
                """

                # Comportamiento del clic e Instagram (Solo activo si el link existe en base de datos)
                card_classes = "game-card has-instagram" if insta_url else "game-card"
                link_wrapper_start = f'<a href="{insta_url}" target="_blank" style="text-decoration: none; color: inherit; display: block;">' if insta_url else '<div style="cursor: default;">'
                link_wrapper_end = '</a>' if insta_url else '</div>'

                html_content += f"""
                {link_wrapper_start}
                <div class="{card_classes}">
                    <div class="img-container">
                        <div class="rank-badge" style="color: {badge_color}; border-color: {badge_color};">#{pos}</div>
                        <img src="{foto}" class="rider-img" onerror="this.src='{placeholder}';">
                    </div>
                    <div class="card-content">
                        <div class="rider-name">{r['nombre']}</div>
                        <div class="rider-meta">{flag_html} <span>{location_text}</span></div>
                        <div class="total-score">{puntos_totales} PTS TOTALES</div>
                        
                        <div class="stats-section">
                            {leyenda_html}
                            {badge_speed_html}
                            {gamified_html}
                        </div>
                    </div>
                </div>
                {link_wrapper_end}
                """

            html_content += "</div>"
            
            # Incremento el multiplicador de altura al renderizar para dar espacio a la nueva data
            num_cards = len(df_cat)
            rows = (num_cards // 4) + 1
            calculated_height = max(550, rows * 550)

            components.html(html_content, height=calculated_height, scrolling=True)

    except Exception as e:
        st.error(f"Error generando la pantalla de ranking: {e}")