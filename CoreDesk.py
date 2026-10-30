import base64
import json
import logging
import math
import os
import shutil
import sys
import time
import traceback
from datetime import datetime
from html import escape

from PyQt6.QtCore import (Qt, QByteArray, QUrl, QSize, QRectF, QPointF, QSettings, QStandardPaths, QTimer, QUrlQuery,
                          QStringListModel, pyqtSignal)
from PyQt6.QtGui import (QAction, QBrush, QColor, QDesktopServices, QFont, QFontDatabase, QIcon, QKeySequence,
                         QLinearGradient, QPainter, QPainterPath, QPalette, QPen, QPixmap, QShortcut)
from PyQt6.QtNetwork import QAuthenticator
from PyQt6.QtWidgets import (QApplication, QCompleter, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QFrame,
                             QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox,
                             QProgressBar, QPushButton, QSizePolicy, QStackedWidget, QSystemTrayIcon, QTabBar, QToolButton,
                             QVBoxLayout, QWidget, QWidgetAction)
from PyQt6 import sip
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView


APP_NAME = "CoreDesk"
APP_VERSION = "2.0"
HOME_URL = "https://www.python.org"
NEW_TAB_TITLE = "Nueva pestaña"
HISTORY_LIMIT = 500
CLOSED_TABS_LIMIT = 25
SESSION_LIMIT = 30
APP_USER_MODEL_ID = "CoreDesk.App"
DATA_FOLDER = "CoreDesk"
LOG_FILE = "coredesk.log"
SETTINGS_ORGANIZATION = "CoreDesk"
SETTINGS_APPLICATION = "CoreDesk"
LEGACY_NAME = "Autorizador"
MIGRATED_SETTINGS = ("geometry", "history", "session")
MIGRATION_MARKER = "migracion.json"
PERMISSION_NAMES = {
    "MediaAudioCapture": "usar tu micrófono",
    "MediaVideoCapture": "usar tu cámara",
    "MediaAudioVideoCapture": "usar tu cámara y tu micrófono",
    "DesktopVideoCapture": "compartir tu pantalla",
    "DesktopAudioVideoCapture": "compartir tu pantalla y el audio",
    "MouseLock": "bloquear el puntero del ratón",
    "Notifications": "mostrarte notificaciones",
    "Geolocation": "conocer tu ubicación",
    "ClipboardReadWrite": "leer y escribir el portapapeles",
    "LocalFontsAccess": "acceder a las fuentes instaladas",
}
ZOOM_LEVELS = (0.25, 0.33, 0.5, 0.67, 0.75, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0)

# Paleta
BG = "#060A13"
SURFACE = "#0C1324"
SURFACE_2 = "#16213A"
BORDER = "#1E2A44"
TEXT = "#E6EDF7"
MUTED = "#7A8BA8"
ICON = "#9FB0CC"
CYAN = "#22D3EE"
VIOLET = "#8B5CF6"
AMBER = "#FBBF24"
RED = "#F43F5E"


class G:
    # Glifos de Segoe Fluent Icons / Segoe MDL2 Assets (mismos códigos en ambas fuentes)
    BACK = ""
    FORWARD = ""
    REFRESH = ""
    STOP = ""
    HOME = ""
    ADD = ""
    CLOSE = ""
    LOCK = ""
    WARNING = ""
    SEARCH = ""
    DOWNLOAD = ""
    MORE = ""
    GLOBE = ""
    BOLT = ""
    UP = ""
    DOWN = ""
    CODE = ""
    FULLSCREEN = ""
    HISTORY = ""
    INFO = ""
    PRINT = ""
    DELETE = ""
    EXTERNAL = ""
    FOLDER = ""
    CHECK = ""
    ZOOM_IN = ""
    ZOOM_OUT = ""


ICON_FONT = "Segoe MDL2 Assets"


def resource_path(name):
    # PyInstaller extrae los datos a sys._MEIPASS
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def new_pixmap(size):
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2)
    pixmap.fill(Qt.GlobalColor.transparent)
    return pixmap


def glyph_pixmap(glyph, color, size):
    pixmap = new_pixmap(size)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    font = QFont(ICON_FONT)
    font.setPixelSize(size)
    painter.setFont(font)
    painter.setPen(QColor(color))
    painter.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, glyph)
    painter.end()
    return pixmap


def glyph_icon(glyph, color=ICON, size=16, active=TEXT, disabled="#2E3A55"):
    icon = QIcon(glyph_pixmap(glyph, color, size))
    if active:
        icon.addPixmap(glyph_pixmap(glyph, active, size), QIcon.Mode.Active)
    if disabled:
        icon.addPixmap(glyph_pixmap(glyph, disabled, size), QIcon.Mode.Disabled)
    return icon


def spinner_icon(angle, size=16):
    pixmap = new_pixmap(size)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    rect = QRectF(2, 2, size - 4, size - 4)
    painter.setPen(QPen(QColor(BORDER), 2))
    painter.drawEllipse(rect)
    painter.setPen(QPen(QColor(CYAN), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawArc(rect, int(-angle * 16), 100 * 16)
    painter.end()
    return QIcon(pixmap)


def logo_pixmap(size):
    pixmap = new_pixmap(size)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    center = QPointF(size / 2, size / 2)
    radius = size / 2 - 1
    hexagon = QPainterPath()
    for i in range(6):
        angle = math.radians(60 * i - 90)
        point = QPointF(center.x() + radius * math.cos(angle), center.y() + radius * math.sin(angle))
        if i == 0:
            hexagon.moveTo(point)
        else:
            hexagon.lineTo(point)
    hexagon.closeSubpath()
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0, QColor(CYAN))
    gradient.setColorAt(1, QColor(VIOLET))
    painter.fillPath(hexagon, gradient)
    font = QFont("Segoe UI")
    font.setPixelSize(int(size * 0.5))
    font.setWeight(QFont.Weight.Black)
    painter.setFont(font)
    painter.setPen(QColor(BG))
    painter.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "C")
    painter.end()
    return pixmap


def make_button(glyph, tooltip, slot=None, name="navBtn", size=16, box=34, parent=None):
    button = QToolButton(parent)
    button.setObjectName(name)
    button.setAutoRaise(True)
    button.setIcon(glyph_icon(glyph, size=size))
    button.setIconSize(QSize(size, size))
    button.setFixedSize(box, box)
    button.setToolTip(tooltip)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    if slot is not None:
        button.clicked.connect(lambda: slot())
    return button


def add_menu_action(menu, text, slot, icon=None):
    action = menu.addAction(icon, text) if icon is not None else menu.addAction(text)
    action.triggered.connect(lambda: slot())
    return action


def make_menu(parent):
    # Menú sin marco y con fondo translúcido para que se vean las esquinas redondeadas
    menu = QMenu(parent)
    menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
    menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    return menu


def google_signin_state(url):
    """"rechazado" si Google rechazó el inicio de sesión, "inicio" en sus páginas de inicio de sesión, None si no."""
    if url.host().lower() != "accounts.google.com":
        return None
    path = url.path().lower()
    if "rejected" in path or "disallowed" in path:
        return "rechazado"
    if "signin" in path or "servicelogin" in path or path.startswith("/v3/"):
        return "inicio"
    return None


def to_url(text):
    text = text.strip()
    if "://" in text or text.startswith(("about:", "data:")):
        return QUrl(text)
    if " " not in text and ("." in text or text.startswith("localhost")):
        return QUrl.fromUserInput(text)
    return QUrl("https://www.google.com/search?q=" + QUrl.toPercentEncoding(text).data().decode())


def apply_dark_titlebar(widget):
    # Barra de título oscura y con los colores de la aplicación (Windows 10 20H1+ / Windows 11)
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = int(widget.winId())
        dwm = ctypes.windll.dwmapi

        def set_attribute(attribute, value):
            value = ctypes.c_int(value)
            return dwm.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value))

        if set_attribute(20, 1) != 0:
            set_attribute(19, 1)
        set_attribute(35, 0x00130A06)  # color del título: BG en formato 0x00BBGGRR
        set_attribute(36, 0x00F7EDE6)  # color del texto: TEXT
        set_attribute(34, 0x0044312A)  # color del borde
    except Exception:
        pass


STYLESHEET = f"""
QMainWindow, QWidget#root {{ background: {BG}; }}
QFrame#topBar {{ background: {BG}; }}
QLabel#brand {{ color: {TEXT}; }}

QTabBar {{ background: transparent; border: none; }}
QTabBar::tab {{
    background: transparent; color: {MUTED};
    height: 32px; margin-top: 8px; padding: 0 4px 0 12px;
    border-top-left-radius: 10px; border-top-right-radius: 10px;
}}
QTabBar::tab:hover:!selected {{ background: #0A1120; color: #C3CEE0; }}
QTabBar::tab:selected {{ background: {SURFACE}; color: {TEXT}; }}
QTabBar::scroller {{ width: 26px; }}
QTabBar QToolButton {{ background: {BG}; border: none; }}
QTabBar QToolButton#tabClose {{ background: transparent; border: none; border-radius: 9px; }}
QTabBar QToolButton#tabClose:hover {{ background: {SURFACE_2}; }}

QToolButton#navBtn, QToolButton#addTabBtn {{ background: transparent; border: none; border-radius: 9px; }}
QToolButton#navBtn:hover, QToolButton#addTabBtn:hover {{ background: {SURFACE_2}; }}
QToolButton#navBtn:pressed, QToolButton#addTabBtn:pressed {{ background: #1C2B4A; }}
QToolButton#navBtn[active="true"] {{ background: rgba(34, 211, 238, 0.14); }}
QToolButton::menu-indicator {{ image: none; width: 0; }}
QToolButton#zoomBtn {{
    background: rgba(34, 211, 238, 0.10); color: {CYAN};
    border: 1px solid rgba(34, 211, 238, 0.35); border-radius: 11px;
    padding: 2px 10px; font-weight: 600;
}}
QToolButton#zoomBtn:hover {{ background: rgba(34, 211, 238, 0.18); }}

QFrame#navBar {{ background: {SURFACE}; }}
QLineEdit#urlBar {{
    background: #070C18; color: {TEXT};
    border: 1px solid #1A2540; border-radius: 17px;
    padding: 0 14px 0 8px; min-height: 34px; font-size: 10pt;
    selection-background-color: #0E7490;
}}
QLineEdit#urlBar:hover {{ border-color: #26365A; }}
QLineEdit#urlBar:focus {{ border: 1px solid {CYAN}; background: #050913; }}

QProgressBar#loadBar {{ background: {SURFACE}; border: none; border-bottom: 1px solid #141E33; }}
QProgressBar#loadBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {CYAN}, stop:1 {VIOLET});
}}

QFrame#infoBar {{ background: #0B1A2A; border-bottom: 1px solid #12324A; }}
QFrame#infoBar[state="rechazado"] {{ background: #221A08; border-bottom: 1px solid #5A4512; }}
QFrame#infoBar QLabel {{ color: {TEXT}; }}
QPushButton#infoButton {{ padding: 5px 14px; background: #0E7490; border-color: {CYAN}; }}
QPushButton#infoButton:hover {{ background: #0891B2; }}
QFrame#findBar {{ background: {SURFACE}; border-top: 1px solid {BORDER}; }}
QLineEdit#findInput {{
    background: #070C18; color: {TEXT};
    border: 1px solid #1A2540; border-radius: 8px;
    padding: 5px 10px; min-width: 280px; selection-background-color: #0E7490;
}}
QLineEdit#findInput:focus {{ border-color: {CYAN}; }}
QLineEdit#findInput[notFound="true"] {{ border-color: {RED}; }}
QLabel#findCount {{ color: {MUTED}; min-width: 96px; }}

QStatusBar {{ background: {BG}; color: {MUTED}; border-top: 1px solid #0F1729; }}
QStatusBar::item {{ border: none; }}
QStatusBar QLabel {{ color: {MUTED}; padding: 0 8px; }}

QMenu {{
    background: {SURFACE}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 12px; padding: 6px;
}}
QMenu::item {{ padding: 8px 40px 8px 12px; border-radius: 7px; background: transparent; }}
QMenu::item:selected {{ background: {SURFACE_2}; }}
QMenu::item:disabled {{ color: #4A5874; }}
QMenu::icon {{ padding-left: 10px; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 6px 8px; }}
QWidget#menuRow {{ background: transparent; }}
QLabel#menuRowLabel {{ color: {TEXT}; }}
QLabel#menuRowValue {{ color: {CYAN}; font-weight: 600; }}

QToolTip {{ background: {SURFACE}; color: {TEXT}; border: 1px solid #2A3B60; padding: 5px 8px; }}

QListView#completerPopup {{
    background: {SURFACE}; color: {TEXT};
    border: 1px solid {BORDER}; padding: 4px; outline: 0;
}}
QListView#completerPopup::item {{ padding: 7px 10px; border-radius: 6px; }}
QListView#completerPopup::item:selected {{ background: {SURFACE_2}; color: {TEXT}; }}

QMessageBox {{ background: {SURFACE}; }}
QMessageBox QLabel {{ color: {TEXT}; }}
QPushButton {{
    background: {SURFACE_2}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 8px; padding: 6px 18px;
}}
QPushButton:hover {{ border-color: {CYAN}; }}
QPushButton:default {{ background: #0E7490; border-color: {CYAN}; }}
"""


START_PAGE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Nueva pestaña</title>
<style>
:root{--c:#22d3ee;--v:#8b5cf6;--bg:#060a13;--s:#0c1324;--b:#1e2a44;--t:#e6edf7;--m:#7a8ba8}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{background:radial-gradient(1100px 560px at 50% -12%,rgba(34,211,238,.16),transparent 62%),
radial-gradient(900px 520px at 100% 115%,rgba(139,92,246,.18),transparent 60%),var(--bg);
color:var(--t);font-family:"Segoe UI Variable Display","Segoe UI",system-ui,sans-serif;
overflow:hidden;display:flex;align-items:center;justify-content:center;user-select:none}
.grid{position:fixed;left:-50%;right:-50%;bottom:-8%;height:52%;pointer-events:none;
background-image:linear-gradient(rgba(34,211,238,.16) 1px,transparent 1px),linear-gradient(90deg,rgba(34,211,238,.16) 1px,transparent 1px);
background-size:52px 52px;transform:perspective(420px) rotateX(64deg);transform-origin:top;
-webkit-mask-image:linear-gradient(to bottom,transparent,#000 35%,#000 70%,transparent);animation:grid 5s linear infinite}
@keyframes grid{to{background-position:0 52px}}
.orb{position:fixed;width:420px;height:420px;border-radius:50%;filter:blur(90px);opacity:.28;pointer-events:none;animation:float 14s ease-in-out infinite}
.orb.a{background:var(--c);top:-160px;left:-120px}.orb.b{background:var(--v);bottom:-180px;right:-120px;animation-delay:-7s}
@keyframes float{50%{transform:translate(40px,30px) scale(1.08)}}
main{position:relative;width:min(720px,88vw);text-align:center;animation:in .7s cubic-bezier(.2,.8,.2,1)}
@keyframes in{from{opacity:0;transform:translateY(14px)}}
.badge{display:inline-flex;align-items:center;padding:7px 15px;border:1px solid rgba(34,211,238,.32);
border-radius:999px;font-size:11px;font-weight:600;letter-spacing:.28em;color:var(--c);background:rgba(34,211,238,.06)}
.dot{width:7px;height:7px;margin-right:10px;border-radius:50%;background:var(--c);box-shadow:0 0 12px var(--c);animation:pulse 2s ease-in-out infinite}
@keyframes pulse{50%{opacity:.35}}
h1{margin-top:22px;font-size:clamp(38px,7vw,64px);font-weight:700;letter-spacing:.14em;line-height:1.05;
background:linear-gradient(92deg,#f1f5fb 10%,var(--c) 55%,var(--v));-webkit-background-clip:text;color:transparent}
.clock{margin-top:12px;color:var(--m);font-size:14px;letter-spacing:.1em;font-variant-numeric:tabular-nums}
.clock b{color:var(--t);font-weight:600}
form{margin-top:36px;position:relative}
form svg{position:absolute;left:20px;top:50%;transform:translateY(-50%);width:19px;height:19px;stroke:var(--m);fill:none;stroke-width:2;transition:.2s}
input{width:100%;height:58px;border-radius:18px;border:1px solid var(--b);background:rgba(12,19,36,.72);
backdrop-filter:blur(14px);color:var(--t);font:inherit;font-size:16px;padding:0 22px 0 54px;outline:none;transition:.25s}
input::placeholder{color:#5b6b88}
input:focus{border-color:var(--c);box-shadow:0 0 0 4px rgba(34,211,238,.12),0 0 50px rgba(34,211,238,.16)}
input:focus+svg,form:focus-within svg{stroke:var(--c)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,210px));justify-content:center;gap:12px;margin-top:22px}
.tile{display:flex;align-items:center;padding:14px;border-radius:14px;text-decoration:none;color:var(--t);text-align:left;
background:rgba(12,19,36,.6);border:1px solid var(--b);transition:.22s;overflow:hidden}
.tile:hover{border-color:rgba(34,211,238,.55);transform:translateY(-2px);box-shadow:0 10px 30px rgba(34,211,238,.10)}
.av{flex:none;margin-right:12px;width:34px;height:34px;border-radius:10px;display:grid;place-items:center;font-weight:700;color:var(--bg);
background:linear-gradient(135deg,var(--c),var(--v))}
.tile div{min-width:0}.host{display:block;font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tag{display:block;font-size:11px;color:var(--m);margin-top:2px}
.keys{margin-top:34px;display:flex;flex-wrap:wrap;justify-content:center;color:var(--m);font-size:12px}
.keys span{margin:0 10px}
kbd{font:inherit;font-size:11px;color:var(--t);padding:2px 7px;border-radius:6px;border:1px solid var(--b);background:var(--s);margin-right:6px}
</style></head>
<body>
<div class="orb a"></div><div class="orb b"></div><div class="grid"></div>
<main>
  <span class="badge"><span class="dot"></span>CONSOLA SEGURA</span>
  <h1>COREDESK</h1>
  <p class="clock" id="clock">&nbsp;</p>
  <form id="f" autocomplete="off">
    <input id="q" placeholder="Buscar en Google o escribir una dirección" autofocus>
    <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
  </form>
  <div class="tiles">{{TILES}}</div>
  <div class="keys">
    <span><kbd>Ctrl+T</kbd>Nueva pestaña</span><span><kbd>Ctrl+L</kbd>Barra de direcciones</span>
    <span><kbd>Ctrl+F</kbd>Buscar</span><span><kbd>Ctrl+Mayús+T</kbd>Reabrir pestaña</span>
  </div>
</main>
<script>
const c=document.getElementById('clock');
function tick(){const d=new Date();
c.innerHTML='<b>'+d.toLocaleTimeString('es-ES')+'</b> · '+d.toLocaleDateString('es-ES',{weekday:'long',day:'numeric',month:'long',year:'numeric'});}
tick();setInterval(tick,1000);
document.getElementById('f').onsubmit=e=>{e.preventDefault();const q=document.getElementById('q').value.trim();if(!q)return;
let u;if(/^[a-z][a-z0-9+.-]*:\\/\\//i.test(q))u=q;else if(!/\\s/.test(q)&&(q.includes('.')||q.startsWith('localhost')))u='http://'+q;
else u='https://www.google.com/search?q='+encodeURIComponent(q);location.href=u;};
</script>
</body></html>"""


CRASH_PAGE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>La página dejó de responder</title>
<style>
body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;background:radial-gradient(900px 500px at 50% -10%,
rgba(244,63,94,.14),transparent 60%),#060a13;color:#e6edf7;font-family:"Segoe UI",system-ui,sans-serif;text-align:center}
.icon{width:64px;height:64px;margin:0 auto 22px;border-radius:18px;display:grid;place-items:center;font-size:30px;font-weight:700;
color:#060a13;background:linear-gradient(135deg,#f43f5e,#8b5cf6)}
h1{font-size:24px;margin:0 0 10px}p{color:#7a8ba8;margin:0 0 28px;max-width:460px;line-height:1.5}
a{display:inline-block;padding:11px 26px;border-radius:12px;background:#0e7490;border:1px solid #22d3ee;color:#e6edf7;
text-decoration:none;font-weight:600}a:hover{background:#0891b2}
</style></head><body><div><div class="icon">!</div><h1>La página dejó de responder</h1>
<p>El proceso que mostraba <b>{{HOST}}</b> se cerró inesperadamente ({{REASON}}).</p>
<a href="{{URL}}">Volver a cargar</a></div></body></html>"""


def local_data_root():
    return QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericDataLocation)


def data_dir():
    path = os.path.join(local_data_root(), DATA_FOLDER)
    os.makedirs(path, exist_ok=True)
    return path


def log_path():
    return os.path.join(data_dir(), LOG_FILE)


def app_settings():
    return QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)


# ------------------------------------------------------------------ migración desde el nombre anterior (Autorizador)

def find_legacy_data_dir(root):
    """Carpeta de datos de una instalación anterior: <root>\\<organización>\\Autorizador con un perfil dentro."""
    try:
        entries = list(os.scandir(root))
    except OSError:
        return None
    for entry in entries:
        candidate = os.path.join(entry.path, LEGACY_NAME)
        if entry.is_dir() and os.path.isdir(os.path.join(candidate, "perfil")):
            return candidate
    return None


def find_legacy_settings():
    """Preferencias de una instalación anterior en el registro (HKCU\\Software\\<organización>\\Autorizador)."""
    if sys.platform != "win32":
        return None
    software = QSettings("HKEY_CURRENT_USER\\Software", QSettings.Format.NativeFormat)
    for organization in software.childGroups():
        if organization == SETTINGS_ORGANIZATION:
            continue
        legacy = QSettings(organization, LEGACY_NAME)
        if any(legacy.contains(key) for key in MIGRATED_SETTINGS):
            return legacy
    return None


def migrate_legacy_data(new_dir, settings, legacy_dir, legacy_settings):
    """Copia, sin mover ni borrar los originales, el perfil web y las preferencias del nombre anterior.

    Se ejecuta una sola vez (queda registrado en migracion.json). Devuelve un mensaje para el usuario si la
    copia falla; en ese caso no deja copias parciales y se reintentará en el siguiente arranque.
    """
    marker = os.path.join(new_dir, MIGRATION_MARKER)
    if os.path.exists(marker):
        return None
    result = {"fecha": datetime.now().isoformat(timespec="seconds"), "perfil": "sin datos anteriores",
              "preferencias": []}

    if legacy_dir is not None:
        target = os.path.join(new_dir, "perfil")
        if os.path.exists(target):
            result["perfil"] = "ya existía un perfil nuevo: no se copió"
        else:
            temporary = target + ".migrando"
            shutil.rmtree(temporary, ignore_errors=True)
            try:
                shutil.copytree(os.path.join(legacy_dir, "perfil"), temporary)
                os.replace(temporary, target)
            except (OSError, shutil.Error) as exc:
                shutil.rmtree(temporary, ignore_errors=True)
                # No se registran rutas: solo el tipo de error
                logging.error("No se pudo copiar el perfil anterior: %s", type(exc).__name__)
                return (f"No se pudieron copiar las sesiones de la versión anterior porque algunos archivos están en "
                        f"uso.\n\nCierra todas las ventanas de Autorizador y de {APP_NAME} y vuelve a abrir {APP_NAME}.")
            result["perfil"] = "copiado"

    if legacy_settings is not None and not any(settings.contains(key) for key in MIGRATED_SETTINGS):
        backup = {}
        for key in MIGRATED_SETTINGS:
            if legacy_settings.contains(key):
                value = legacy_settings.value(key)
                settings.setValue(key, value)
                backup[key] = base64.b64encode(bytes(value)).decode() if isinstance(value, QByteArray) else value
        settings.sync()
        # Copia de seguridad de las preferencias anteriores (el registro original no se modifica)
        backup_dir = os.path.join(new_dir, "respaldo_migracion")
        os.makedirs(backup_dir, exist_ok=True)
        with open(os.path.join(backup_dir, "preferencias_anteriores.json"), "w", encoding="utf-8") as file:
            json.dump(backup, file, ensure_ascii=False, indent=2)
        result["preferencias"] = sorted(backup)

    with open(marker, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
    logging.info("Migración desde la versión anterior: perfil %s, preferencias %s", result["perfil"],
                 result["preferencias"] or "ninguna")
    return None


def setup_logging():
    logging.basicConfig(filename=log_path(), level=logging.INFO, encoding="utf-8",
                        format="%(asctime)s %(levelname)s %(message)s")

    # PyQt6 cierra la aplicación ante una excepción no controlada en un slot: se registra y se avisa sin cerrar
    def excepthook(exc_type, exc_value, exc_traceback):
        details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logging.error("Excepción no controlada:\n%s", details)
        if QApplication.instance() is not None:
            QMessageBox.critical(None, APP_NAME, f"Se produjo un error inesperado:\n{exc_value}\n\n"
                                                 f"Los detalles se guardaron en {log_path()}")

    sys.excepthook = excepthook


def set_app_user_model_id():
    # Agrupa la ventana en la barra de tareas con su propio icono (y no con el de python.exe)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
        except Exception:
            pass


def create_profile():
    # En Qt6 el perfil por defecto es de incógnito: se usa uno persistente para conservar las sesiones iniciadas
    profile = QWebEngineProfile(APP_NAME)
    base = data_dir()
    profile.setPersistentStoragePath(os.path.join(base, "perfil"))
    profile.setCachePath(os.path.join(base, "cache"))
    profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
    # Algunos sitios (p. ej. el inicio de sesión de Google) rechazan los navegadores que se anuncian como QtWebEngine
    user_agent = " ".join(part for part in profile.httpUserAgent().split() if not part.startswith("QtWebEngine/"))
    profile.setHttpUserAgent(user_agent)
    settings = profile.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.FocusOnNavigationEnabled, False)
    return profile


class WebPage(QWebEnginePage):
    def __init__(self, main_window, parent):
        super(WebPage, self).__init__(main_window.profile, parent)
        self.main_window = main_window

    # QWebEngine ignora por defecto los enlaces con target="_blank" y window.open();
    # se abren en una pestaña nueva junto a la actual
    def createWindow(self, window_type):
        background = window_type == QWebEnginePage.WebWindowType.WebBrowserBackgroundTab
        # En Qt6 la página ya no conoce su vista (QWebEnginePage.view() no existe)
        view = self.main_window.add_tab(QUrl(), background=background, after=QWebEngineView.forPage(self))
        return view.page()


class BrowserView(QWebEngineView):
    def __init__(self, main_window):
        super(BrowserView, self).__init__()
        self.setPage(WebPage(main_window, self))
        self.loading = False
        self.progress = 0
        # False mientras la pestaña no haya mostrado ninguna página (p. ej. un enlace de descarga con target="_blank")
        self.has_loaded = False
        self.info_dismissed = False  # el usuario ocultó el aviso de inicio de sesión en esta pestaña
        self.rejection_handled = False  # ya se abrió el navegador por un rechazo de Google en este inicio de sesión

    def is_start_page(self):
        return self.url().scheme() in ("", "data", "about")


class TabLabel(QWidget):
    """Icono y título de una pestaña alineados a la izquierda (QTabBar solo sabe centrarlos)."""

    def __init__(self, tab_bar):
        super(TabLabel, self).__init__(tab_bar)
        self.tab_bar = tab_bar
        self.icon = QIcon()
        self.text = ""
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.resize(120, 20)

    def set_icon(self, icon):
        self.icon = icon
        self.update()

    def set_text(self, text):
        self.text = text
        self.update()

    def sizeHint(self):
        return self.size()

    def paintEvent(self, event):
        index = self.tab_bar.index_of_label(self)
        if index == self.tab_bar.currentIndex():
            color = TEXT
        elif index == self.tab_bar.hover_index:
            color = "#C3CEE0"
        else:
            color = MUTED
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        top = (self.height() - 16) // 2
        self.icon.paint(painter, 0, top, 16, 16)
        painter.setPen(QColor(color))
        text_rect = self.rect().adjusted(26, 0, 0, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         self.fontMetrics().elidedText(self.text, Qt.TextElideMode.ElideRight, text_rect.width()))
        painter.end()


class TabBar(QTabBar):
    MIN_WIDTH = 72
    MAX_WIDTH = 240

    def __init__(self, parent=None):
        super(TabBar, self).__init__(parent)
        self.available_width = 800
        self.hover_index = -1
        self.setMouseTracking(True)
        self.currentChanged.connect(self.update_labels)
        self.setDocumentMode(True)
        self.setDrawBase(False)
        self.setExpanding(False)
        self.setMovable(True)
        self.setUsesScrollButtons(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setIconSize(QSize(16, 16))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def set_available_width(self, width):
        if width != self.available_width:
            self.available_width = width
            self.setElideMode(self.elideMode())  # obliga a recalcular el ancho de las pestañas

    def tabSizeHint(self, index):
        height = super(TabBar, self).tabSizeHint(index).height()
        width = self.available_width // max(1, self.count())
        return QSize(max(self.MIN_WIDTH, min(self.MAX_WIDTH, width)), height)

    def minimumTabSizeHint(self, index):
        return self.tabSizeHint(index)

    def label(self, index):
        return self.tabButton(index, QTabBar.ButtonPosition.LeftSide)

    def index_of_label(self, label):
        for i in range(self.count()):
            if self.label(i) is label:
                return i
        return -1

    def update_labels(self):
        for i in range(self.count()):
            if self.label(i) is not None:
                self.label(i).update()

    def tabLayoutChange(self):
        super(TabBar, self).tabLayoutChange()
        # La etiqueta ocupa el ancho de la pestaña menos el relleno y el botón de cerrar
        for i in range(self.count()):
            label = self.label(i)
            if label is not None:
                label.resize(max(16, self.tabRect(i).width() - 46), label.height())

    def mouseMoveEvent(self, event):
        super(TabBar, self).mouseMoveEvent(event)
        index = self.tabAt(event.position().toPoint())
        if index != self.hover_index:
            self.hover_index = index
            self.update_labels()

    def leaveEvent(self, event):
        super(TabBar, self).leaveEvent(event)
        self.hover_index = -1
        self.update_labels()

    def mouseReleaseEvent(self, event):
        index = self.tabAt(event.position().toPoint())
        if event.button() == Qt.MouseButton.MiddleButton and index >= 0:
            self.tabCloseRequested.emit(index)
            return
        super(TabBar, self).mouseReleaseEvent(event)

    def paintEvent(self, event):
        super(TabBar, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        current = self.currentIndex()
        top = 8  # margin-top de las pestañas en la hoja de estilos

        # Separadores entre pestañas no seleccionadas
        painter.setPen(QPen(QColor(BORDER), 1))
        for i in range(self.count() - 1):
            if current not in (i, i + 1):
                rect = self.tabRect(i)
                painter.drawLine(rect.right(), rect.top() + top + 9, rect.right(), rect.bottom() - 9)

        # Línea de neón sobre la pestaña activa (no se dibuja mientras se arrastra)
        if current >= 0 and not QApplication.mouseButtons() & Qt.MouseButton.LeftButton:
            rect = self.tabRect(current)
            gradient = QLinearGradient(rect.left(), 0, rect.right(), 0)
            gradient.setColorAt(0, QColor(CYAN))
            gradient.setColorAt(1, QColor(VIOLET))
            glow = QColor(CYAN)
            glow.setAlpha(45)
            painter.setPen(QPen(glow, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(rect.left() + 18, rect.top() + top + 1, rect.right() - 18, rect.top() + top + 1)
            painter.setPen(QPen(QBrush(gradient), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(rect.left() + 14, rect.top() + top + 1, rect.right() - 14, rect.top() + top + 1)
        painter.end()


class TopBar(QFrame):
    new_tab_requested = pyqtSignal()

    def __init__(self, parent=None):
        super(TopBar, self).__init__(parent)
        self.setObjectName("topBar")
        self.setFixedHeight(44)

        logo = QLabel()
        logo.setPixmap(logo_pixmap(22))

        brand_font = QFont("Segoe UI", 8)
        brand_font.setWeight(QFont.Weight.DemiBold)
        brand_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.4)
        brand = QLabel(f"CORE<span style='color:{CYAN}'>DESK</span>")
        brand.setObjectName("brand")
        brand.setFont(brand_font)

        self.tab_bar = TabBar()
        self.add_button = make_button(G.ADD, "Nueva pestaña (Ctrl+T)", self.new_tab_requested.emit, "addTabBtn",
                                      size=14, box=30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(6)
        layout.addWidget(logo)
        layout.addSpacing(2)
        layout.addWidget(brand)
        layout.addSpacing(14)
        layout.addWidget(self.tab_bar, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.add_button, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch(1)

    def resizeEvent(self, event):
        super(TopBar, self).resizeEvent(event)
        # Deja sitio para el botón "+" y una zona libre a la derecha
        self.tab_bar.set_available_width(self.width() - self.tab_bar.x() - self.add_button.width() - 80)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.new_tab_requested.emit()


class UrlBar(QLineEdit):
    def __init__(self, parent=None):
        super(UrlBar, self).__init__(parent)
        self.setObjectName("urlBar")
        self.setPlaceholderText("Buscar en Google o escribir una dirección")
        self.display_text = ""
        self.icons = {
            "https": (glyph_icon(G.LOCK, CYAN, 14), "Conexión segura (HTTPS)"),
            "http": (glyph_icon(G.WARNING, AMBER, 14), "Conexión no segura"),
            "": (glyph_icon(G.SEARCH, MUTED, 14), ""),
        }
        self.security_action = self.addAction(self.icons[""][0], QLineEdit.ActionPosition.LeadingPosition)

    def set_url(self, url, force=False):
        self.display_text = url.toDisplayString() if not url.isEmpty() else ""
        if force or not self.hasFocus():
            self.setText(self.display_text)
            self.setCursorPosition(0)
        icon, tooltip = self.icons.get(url.scheme(), self.icons[""])
        self.security_action.setIcon(icon)
        self.security_action.setToolTip(tooltip)

    def focusInEvent(self, event):
        super(UrlBar, self).focusInEvent(event)
        # Seleccionar todo solo cuando el usuario entra a la barra: la lista de sugerencias
        # también provoca eventos de foco y la siguiente tecla borraría lo escrito
        if event.reason() in (Qt.FocusReason.MouseFocusReason, Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason, Qt.FocusReason.ShortcutFocusReason):
            QTimer.singleShot(0, self.selectAll)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.setText(self.display_text)
            self.selectAll()
            return
        super(UrlBar, self).keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, profile):
        super(MainWindow, self).__init__()
        self.profile = profile

        self.setWindowTitle(APP_NAME)
        icon_path = resource_path("icon.ico")
        self.setWindowIcon(QIcon(icon_path) if os.path.exists(icon_path) else QIcon(logo_pixmap(64)))

        self.settings = app_settings()
        self.history = self.settings.value("history", [], type=list)
        self.closed_tabs = []
        self.downloads = []
        self.devtools = None
        self.tray = None
        self.notification = None
        self.last_navigation = ("", 0.0)

        # Animación de carga de las pestañas
        self.spinner_angle = 0
        self.spinner = QTimer(self)
        self.spinner.setInterval(50)
        self.spinner.timeout.connect(self.animate_spinners)

        self.build_ui()
        self.build_actions()
        self.restore_window()
        apply_dark_titlebar(self)

        # Gestionar las descargas (si no se aceptan, QWebEngine las cancela)
        self.profile.downloadRequested.connect(self.download_requested)
        self.profile.setNotificationPresenter(self.show_notification)

        self.restore_session()

    # ---------------------------------------------------------------- interfaz

    def build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barra de pestañas
        self.top_bar = TopBar()
        self.tab_bar = self.top_bar.tab_bar
        self.top_bar.new_tab_requested.connect(lambda: self.add_tab())
        self.tab_bar.currentChanged.connect(self.current_tab_changed)
        self.tab_bar.tabCloseRequested.connect(self.close_tab)
        self.tab_bar.customContextMenuRequested.connect(self.show_tab_menu)

        # Barra de navegación
        self.nav_bar = QFrame()
        self.nav_bar.setObjectName("navBar")
        nav = QHBoxLayout(self.nav_bar)
        nav.setContentsMargins(10, 6, 10, 6)
        nav.setSpacing(2)

        self.back_button = make_button(G.BACK, "Atrás (Alt+←)", self.go_back)
        self.forward_button = make_button(G.FORWARD, "Adelante (Alt+→)", self.go_forward)
        self.reload_button = make_button(G.REFRESH, "Recargar (F5)", self.reload_or_stop)
        self.home_button = make_button(G.HOME, "Página de inicio (Alt+Inicio)", self.go_home)

        # Barra de texto para la URL, con autocompletado del historial
        self.url_bar = UrlBar()
        self.url_bar.returnPressed.connect(self.load_url)
        self.history_model = QStringListModel(self.history, self)
        completer = QCompleter(self.history_model, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setMaxVisibleItems(8)
        completer.popup().setObjectName("completerPopup")
        completer.activated[str].connect(self.load_url)
        self.url_bar.setCompleter(completer)

        self.zoom_button = QToolButton()
        self.zoom_button.setObjectName("zoomBtn")
        self.zoom_button.setToolTip("Restablecer zoom (Ctrl+0)")
        self.zoom_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.zoom_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.zoom_button.clicked.connect(lambda: self.change_zoom(0))
        self.zoom_button.hide()

        self.downloads_button = make_button(G.DOWNLOAD, "Descargas")
        self.downloads_menu = make_menu(self)
        self.downloads_menu.aboutToShow.connect(self.build_downloads_menu)
        self.downloads_button.setMenu(self.downloads_menu)
        self.downloads_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        self.menu_button = make_button(G.MORE, "Menú")
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        for button in (self.back_button, self.forward_button, self.reload_button, self.home_button):
            nav.addWidget(button)
        nav.addSpacing(8)
        nav.addWidget(self.url_bar, 1)
        nav.addSpacing(6)
        nav.addWidget(self.zoom_button)
        nav.addWidget(self.downloads_button)
        nav.addWidget(self.menu_button)

        # Indicador de progreso de carga
        self.load_bar = QProgressBar()
        self.load_bar.setObjectName("loadBar")
        self.load_bar.setFixedHeight(3)
        self.load_bar.setTextVisible(False)
        self.load_bar.setRange(0, 100)
        self.load_bar.setValue(0)

        # Contenido de las pestañas
        self.stack = QStackedWidget()

        # Barra de búsqueda en la página
        self.find_bar = QFrame()
        self.find_bar.setObjectName("findBar")
        find = QHBoxLayout(self.find_bar)
        find.setContentsMargins(14, 6, 10, 6)
        find.setSpacing(4)
        find_icon = QLabel()
        find_icon.setPixmap(glyph_pixmap(G.SEARCH, CYAN, 14))
        self.find_input = QLineEdit()
        self.find_input.setObjectName("findInput")
        self.find_input.setPlaceholderText("Buscar en la página")
        self.find_input.textChanged.connect(lambda: self.find())
        self.find_input.returnPressed.connect(lambda: self.find())
        QShortcut(QKeySequence("Shift+Return"), self.find_input, lambda: self.find(backward=True), context=Qt.ShortcutContext.WidgetShortcut)
        QShortcut(QKeySequence("Esc"), self.find_input, self.hide_find_bar, context=Qt.ShortcutContext.WidgetShortcut)
        self.find_count = QLabel()
        self.find_count.setObjectName("findCount")
        find.addWidget(find_icon)
        find.addSpacing(6)
        find.addWidget(self.find_input)
        find.addSpacing(6)
        find.addWidget(self.find_count)
        find.addWidget(make_button(G.UP, "Anterior (Mayús+F3)", lambda: self.find(backward=True), size=12, box=28))
        find.addWidget(make_button(G.DOWN, "Siguiente (F3)", lambda: self.find(), size=12, box=28))
        find.addStretch(1)
        find.addWidget(make_button(G.CLOSE, "Cerrar (Esc)", self.hide_find_bar, size=11, box=28))
        self.find_bar.hide()

        # Aviso para continuar en el navegador predeterminado cuando el inicio de sesión de Google falla aquí
        self.info_bar = QFrame()
        self.info_bar.setObjectName("infoBar")
        info = QHBoxLayout(self.info_bar)
        info.setContentsMargins(14, 6, 10, 6)
        info.setSpacing(10)
        self.info_icon = QLabel()
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        info_button = QPushButton("Abrir en el navegador predeterminado")
        info_button.setObjectName("infoButton")
        info_button.setCursor(Qt.CursorShape.PointingHandCursor)
        info_button.clicked.connect(lambda: self.open_in_browser())
        info.addWidget(self.info_icon)
        info.addWidget(self.info_label, 1)
        info.addWidget(info_button)
        info.addWidget(make_button(G.CLOSE, "Ocultar", self.dismiss_info_bar, size=11, box=28))
        self.info_bar.hide()

        layout.addWidget(self.top_bar)
        layout.addWidget(self.nav_bar)
        layout.addWidget(self.load_bar)
        layout.addWidget(self.info_bar)
        layout.addWidget(self.stack, 1)
        layout.addWidget(self.find_bar)

        self.status_label = QLabel(f"{APP_NAME} · v{APP_VERSION}")
        self.statusBar().addPermanentWidget(self.status_label)

    def build_actions(self):
        def action(text, shortcuts, slot, glyph=None):
            act = QAction(text, self)
            if glyph:
                act.setIcon(glyph_icon(glyph, ICON, 14, active=None, disabled=None))
            act.setShortcuts([QKeySequence(shortcut) for shortcut in shortcuts])
            act.triggered.connect(lambda: slot())
            self.addAction(act)
            return act

        self.new_tab_action = action("Nueva pestaña", ["Ctrl+T"], self.add_tab, G.ADD)
        self.reopen_action = action("Reabrir pestaña cerrada", ["Ctrl+Shift+T"], self.reopen_closed_tab, G.HISTORY)
        action("Cerrar pestaña", ["Ctrl+W", "Ctrl+F4"], lambda: self.close_tab(self.tab_bar.currentIndex()))
        action("Pestaña siguiente", ["Ctrl+Tab", "Ctrl+PgDown"], lambda: self.cycle_tab(1))
        action("Pestaña anterior", ["Ctrl+Shift+Tab", "Ctrl+PgUp"], lambda: self.cycle_tab(-1))
        for number in range(1, 10):
            action(f"Pestaña {number}", [f"Ctrl+{number}"], lambda n=number: self.select_tab(n))
        action("Ir a la barra de direcciones", ["Ctrl+L", "F6", "Alt+D"], self.focus_url_bar)
        action("Recargar", ["F5", "Ctrl+R"], lambda: self.current_view().reload())
        action("Recargar sin caché", ["Ctrl+F5", "Ctrl+Shift+R"],
               lambda: self.current_view().triggerPageAction(QWebEnginePage.WebAction.ReloadAndBypassCache))
        action("Atrás", ["Alt+Left"], self.go_back)
        action("Adelante", ["Alt+Right"], self.go_forward)
        action("Página de inicio", ["Alt+Home"], self.go_home)
        self.find_action = action("Buscar en la página", ["Ctrl+F"], self.show_find_bar, G.SEARCH)
        action("Buscar siguiente", ["F3"], lambda: self.find())
        action("Buscar anterior", ["Shift+F3"], lambda: self.find(backward=True))
        action("Acercar", ["Ctrl++", "Ctrl+="], lambda: self.change_zoom(1))
        action("Alejar", ["Ctrl+-"], lambda: self.change_zoom(-1))
        action("Restablecer zoom", ["Ctrl+0"], lambda: self.change_zoom(0))
        self.devtools_action = action("Herramientas de desarrollador", ["F12", "Ctrl+Shift+I"], self.open_devtools, G.CODE)
        self.fullscreen_action = action("Pantalla completa", ["F11"], self.toggle_fullscreen, G.FULLSCREEN)
        self.pdf_action = action("Guardar como PDF…", ["Ctrl+P"], self.save_pdf, G.PRINT)
        self.external_action = action("Abrir en el navegador predeterminado", ["Ctrl+Shift+B"],
                                      self.open_in_browser, G.EXTERNAL)
        self.clear_data_action = action("Borrar datos de navegación…", ["Ctrl+Shift+Del"], self.clear_browsing_data,
                                        G.DELETE)
        self.about_action = action(f"Acerca de {APP_NAME}", [], self.show_about, G.INFO)

        # Menú principal
        menu = make_menu(self)
        menu.addAction(self.new_tab_action)
        menu.addAction(self.reopen_action)
        menu.addSeparator()
        menu.addAction(self.build_zoom_row(menu))
        menu.addSeparator()
        menu.addAction(self.find_action)
        menu.addAction(self.devtools_action)
        menu.addAction(self.fullscreen_action)
        menu.addAction(self.pdf_action)
        menu.addAction(self.external_action)
        menu.addSeparator()
        menu.addAction(self.clear_data_action)
        menu.addAction(self.about_action)
        menu.aboutToShow.connect(lambda: self.reopen_action.setEnabled(bool(self.closed_tabs)))
        self.menu_button.setMenu(menu)

    def build_zoom_row(self, menu):
        row = QWidget(menu)
        row.setObjectName("menuRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 2, 6, 2)
        layout.setSpacing(2)
        label = QLabel("Zoom")
        label.setObjectName("menuRowLabel")
        self.menu_zoom_label = QLabel("100%")
        self.menu_zoom_label.setObjectName("menuRowValue")
        self.menu_zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.menu_zoom_label.setFixedWidth(52)
        layout.addWidget(label)
        layout.addStretch(1)
        layout.addSpacing(40)
        layout.addWidget(make_button(G.ZOOM_OUT, "Alejar (Ctrl+-)", lambda: self.change_zoom(-1), size=14, box=30))
        layout.addWidget(self.menu_zoom_label)
        layout.addWidget(make_button(G.ZOOM_IN, "Acercar (Ctrl++)", lambda: self.change_zoom(1), size=14, box=30))
        widget_action = QWidgetAction(menu)
        widget_action.setDefaultWidget(row)
        return widget_action

    def restore_window(self):
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1280, 800)
            frame = self.frameGeometry()
            frame.moveCenter(QApplication.primaryScreen().availableGeometry().center())
            self.move(frame.topLeft())

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("history", self.history)
        self.save_session()
        if self.devtools is not None:
            self.devtools.close()
        super(MainWindow, self).closeEvent(event)

    # ---------------------------------------------------------------- pestañas

    def add_tab(self, url=None, background=False, after=None):
        """Abre una pestaña; sin url muestra la página de inicio y con una QUrl vacía no carga nada (popups)."""
        view = BrowserView(self)
        page = view.page()
        view.titleChanged.connect(lambda: self.update_tab_title(view))
        view.iconChanged.connect(lambda: self.update_tab_icon(view))
        view.urlChanged.connect(lambda: self.url_changed(view))
        view.loadStarted.connect(lambda: self.load_started(view))
        view.loadProgress.connect(lambda progress: self.load_progress(view, progress))
        view.loadFinished.connect(lambda ok: self.load_finished(view, ok))
        page.linkHovered.connect(lambda link: self.link_hovered(view, link))
        page.windowCloseRequested.connect(lambda: self.close_view(view))
        page.findTextFinished.connect(lambda result: self.find_finished(view, result))
        page.fullScreenRequested.connect(self.fullscreen_requested)
        page.permissionRequested.connect(lambda permission: self.permission_requested(permission))
        page.certificateError.connect(self.certificate_error)
        page.authenticationRequired.connect(lambda url, authenticator: self.authentication_required(url, authenticator))
        page.proxyAuthenticationRequired.connect(
            lambda url, authenticator, host: self.authentication_required(url, authenticator, host))
        page.selectClientCertificate.connect(self.select_client_certificate)
        page.renderProcessTerminated.connect(lambda status, code: self.render_process_terminated(view, status, code))
        page.pdfPrintingFinished.connect(self.pdf_finished)
        self.stack.addWidget(view)

        opener = self.index_of(after)
        index = self.tab_bar.insertTab(opener + 1 if opener >= 0 else self.tab_bar.count(), "")
        self.tab_bar.setTabData(index, view)
        label = TabLabel(self.tab_bar)
        label.set_icon(glyph_icon(G.BOLT, CYAN, 14))
        label.set_text(NEW_TAB_TITLE)
        self.tab_bar.setTabButton(index, QTabBar.ButtonPosition.LeftSide, label)
        close_button = make_button(G.CLOSE, "Cerrar pestaña (Ctrl+W)", lambda: self.close_view(view), "tabClose",
                                   size=9, box=20)
        self.tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, close_button)

        if url is None:
            view.setHtml(self.start_page_html())
        elif not url.isEmpty():
            view.setUrl(url)

        if not background:
            if self.tab_bar.currentIndex() == index:
                self.current_tab_changed(index)  # la primera pestaña ya es la actual al insertarla
            else:
                self.tab_bar.setCurrentIndex(index)
            if url is None:
                self.url_bar.setFocus()
        return view

    def start_page_html(self):
        shortcuts = [(HOME_URL, "Página de inicio")]
        hosts = {QUrl(HOME_URL).host()}
        for entry in self.history:
            host = QUrl(entry).host()
            if host and host not in hosts:
                hosts.add(host)
                shortcuts.append((entry, "Visitado recientemente"))
            if len(shortcuts) == 4:
                break
        tiles = "".join(
            f'<a class="tile" href="{escape(url)}"><span class="av">{escape(self.host_label(url)[:1].upper())}</span>'
            f'<div><span class="host">{escape(self.host_label(url))}</span><span class="tag">{escape(tag)}</span></div></a>'
            for url, tag in shortcuts)
        return START_PAGE.replace("{{TILES}}", tiles)

    @staticmethod
    def host_label(url):
        host = QUrl(url).host() or url
        return host[4:] if host.startswith("www.") else host

    def index_of(self, view):
        for i in range(self.tab_bar.count()):
            if self.tab_bar.tabData(i) is view:
                return i
        return -1

    def current_view(self):
        return self.tab_bar.tabData(self.tab_bar.currentIndex())

    def view_for_page(self, page):
        for i in range(self.tab_bar.count()):
            view = self.tab_bar.tabData(i)
            if view.page() is page:
                return view
        return None

    def close_view(self, view):
        index = self.index_of(view)
        if index >= 0:
            self.close_tab(index)

    def close_tab(self, index):
        view = self.tab_bar.tabData(index)
        if view is None:
            return
        # La ventana siempre conserva al menos una pestaña
        if self.tab_bar.count() == 1:
            self.add_tab()
        if not view.is_start_page():
            self.closed_tabs.append(view.url())
            del self.closed_tabs[:-CLOSED_TABS_LIMIT]
        self.tab_bar.removeTab(self.index_of(view))
        self.stack.removeWidget(view)
        view.deleteLater()

    def close_other_tabs(self, keep):
        for i in reversed(range(self.tab_bar.count())):
            if self.tab_bar.tabData(i) is not keep:
                self.close_tab(i)

    def close_tabs_to_right(self, view):
        for i in reversed(range(self.index_of(view) + 1, self.tab_bar.count())):
            self.close_tab(i)

    def reopen_closed_tab(self):
        if self.closed_tabs:
            self.add_tab(self.closed_tabs.pop(), after=self.current_view())

    def duplicate_tab(self, view):
        self.add_tab(None if view.is_start_page() else view.url(), after=view)

    def cycle_tab(self, step):
        self.tab_bar.setCurrentIndex((self.tab_bar.currentIndex() + step) % self.tab_bar.count())

    def select_tab(self, number):
        index = self.tab_bar.count() - 1 if number == 9 else number - 1
        if index < self.tab_bar.count():
            self.tab_bar.setCurrentIndex(index)

    def show_tab_menu(self, pos):
        index = self.tab_bar.tabAt(pos)
        menu = make_menu(self)
        if index >= 0:
            view = self.tab_bar.tabData(index)
            add_menu_action(menu, "Recargar", view.reload, glyph_icon(G.REFRESH, ICON, 14))
            add_menu_action(menu, "Duplicar", lambda: self.duplicate_tab(view))
            add_menu_action(menu, "Abrir en el navegador predeterminado", lambda: self.open_in_browser(view),
                            glyph_icon(G.EXTERNAL, ICON, 14))
            menu.addSeparator()
            add_menu_action(menu, "Cerrar pestaña", lambda: self.close_view(view), glyph_icon(G.CLOSE, ICON, 12))
            add_menu_action(menu, "Cerrar otras pestañas", lambda: self.close_other_tabs(view)).setEnabled(
                self.tab_bar.count() > 1)
            add_menu_action(menu, "Cerrar pestañas a la derecha", lambda: self.close_tabs_to_right(view)).setEnabled(
                index < self.tab_bar.count() - 1)
            menu.addSeparator()
        menu.addAction(self.new_tab_action)
        menu.addAction(self.reopen_action)
        self.reopen_action.setEnabled(bool(self.closed_tabs))
        menu.exec(self.tab_bar.mapToGlobal(pos))

    def current_tab_changed(self, index):
        view = self.tab_bar.tabData(index) if index >= 0 else None
        if view is None:
            return
        self.stack.setCurrentWidget(view)
        self.url_bar.set_url(QUrl() if view.is_start_page() else view.url(), force=True)
        self.update_navigation(view)
        self.update_info_bar(view)
        self.update_window_title(view)
        self.update_zoom(view)
        self.load_bar.setValue(view.progress if view.loading else 0)
        self.statusBar().clearMessage()
        if self.find_bar.isVisible():
            self.find()
        if self.devtools is not None and self.devtools.isVisible():
            view.page().setDevToolsPage(self.devtools.page())

    # ---------------------------------------------------------------- eventos de las páginas

    def update_tab_title(self, view):
        index = self.index_of(view)
        if index < 0:
            return
        title = view.title() or self.host_label(view.url().toString()) or NEW_TAB_TITLE
        if view.is_start_page() and not view.title():
            title = NEW_TAB_TITLE
        self.tab_bar.label(index).set_text(title)
        self.tab_bar.setTabToolTip(index, title)
        if view is self.current_view():
            self.update_window_title(view)

    def update_tab_icon(self, view):
        index = self.index_of(view)
        if index < 0 or view.loading:
            return
        if view.is_start_page():
            icon = glyph_icon(G.BOLT, CYAN, 14)
        elif view.icon().isNull():
            icon = glyph_icon(G.GLOBE, MUTED, 14)
        else:
            icon = view.icon()
        self.tab_bar.label(index).set_icon(icon)

    def update_window_title(self, view):
        title = view.title() if not view.is_start_page() else NEW_TAB_TITLE
        self.setWindowTitle(f"{title} — {APP_NAME}" if title else APP_NAME)

    def url_changed(self, view):
        state = google_signin_state(view.url())
        if state is None:
            view.info_dismissed = False
            view.rejection_handled = False
        elif state == "rechazado" and not view.rejection_handled:
            view.rejection_handled = True
            QTimer.singleShot(0, lambda: self.signin_rejected(view))
        if view is self.current_view():
            self.url_bar.set_url(QUrl() if view.is_start_page() else view.url())
            self.update_navigation(view)
            self.update_info_bar(view)

    def signin_rejected(self, view):
        # Google no admite la vista integrada para esta cuenta: se continúa en el navegador del sistema
        # (que empieza el inicio de sesión desde cero) y la pestaña vuelve a donde estaba
        if self.index_of(view) < 0:
            return
        logging.warning("Google rechazó el inicio de sesión en la vista integrada; se abre el navegador")
        self.open_in_browser(view)
        if view.history().canGoBack():
            view.back()
        else:
            view.setHtml(self.start_page_html())
        self.statusBar().showMessage("Google no permite esta cuenta en CoreDesk: el inicio de sesión continúa en "
                                     "tu navegador predeterminado", 10000)

    def update_info_bar(self, view):
        state = google_signin_state(view.url())
        if state is None or view.info_dismissed:
            self.info_bar.hide()
            return
        if state == "rechazado":
            self.info_icon.setPixmap(glyph_pixmap(G.WARNING, AMBER, 16))
            self.info_label.setText("Google no permite iniciar sesión en esta cuenta desde CoreDesk. "
                                    "Puedes continuar en tu navegador predeterminado.")
        else:
            self.info_icon.setPixmap(glyph_pixmap(G.INFO, CYAN, 16))
            self.info_label.setText("¿No puedes iniciar sesión aquí (llave de acceso, verificación o "
                                    "«navegador no seguro»)? Continúa en tu navegador predeterminado.")
        self.info_bar.setProperty("state", state)
        self.repolish(self.info_bar)
        self.info_bar.show()

    def dismiss_info_bar(self):
        self.current_view().info_dismissed = True
        self.info_bar.hide()

    def open_in_browser(self, view=None):
        # Abre la misma dirección en el navegador del sistema; CoreDesk no lee ni transfiere credenciales
        view = view or self.current_view()
        url = view.url()
        if google_signin_state(url) is not None:
            # La dirección intermedia del inicio de sesión de Google depende de esta vista: en el otro navegador
            # se abre el destino final (p. ej. Gmail) para que el inicio de sesión empiece desde cero
            target = QUrl(QUrlQuery(url).queryItemValue("continue", QUrl.ComponentFormattingOption.FullyDecoded))
            url = target if target.scheme() == "https" else QUrl("https://accounts.google.com/")
        if url.scheme() not in ("http", "https"):
            self.statusBar().showMessage("Esta página no se puede abrir en otro navegador", 5000)
            return
        if QDesktopServices.openUrl(url):
            logging.info("Página abierta en el navegador predeterminado: %s", url.host())
            self.statusBar().showMessage(f"Abierto en el navegador predeterminado: {url.host()}", 6000)
        else:
            QMessageBox.warning(self, APP_NAME, "No se pudo abrir el navegador predeterminado.")

    def load_started(self, view):
        view.loading = True
        view.progress = 0
        if not self.spinner.isActive():
            self.spinner.start()
        if view is self.current_view():
            self.load_bar.setValue(2)
            self.update_navigation(view)

    def load_progress(self, view, progress):
        view.progress = progress
        if view is self.current_view():
            self.load_bar.setValue(max(progress, 2))

    def load_finished(self, view, ok):
        view.loading = False
        view.has_loaded = view.has_loaded or ok
        self.update_tab_icon(view)
        if ok and not view.is_start_page():
            self.add_to_history(view.url().toString())
        if view is self.current_view():
            self.load_bar.setValue(100)
            QTimer.singleShot(300, lambda: self.load_bar.setValue(0) if not self.current_view().loading else None)
            self.update_navigation(view)
            self.update_zoom(view)

    def link_hovered(self, view, link):
        if view is self.current_view():
            if link:
                self.statusBar().showMessage(link)
            else:
                self.statusBar().clearMessage()

    def animate_spinners(self):
        self.spinner_angle = (self.spinner_angle + 24) % 360
        icon = spinner_icon(self.spinner_angle)
        loading = False
        for i in range(self.tab_bar.count()):
            if self.tab_bar.tabData(i).loading:
                self.tab_bar.label(i).set_icon(icon)
                loading = True
        if not loading:
            self.spinner.stop()

    def update_navigation(self, view):
        history = view.history()
        self.back_button.setEnabled(history.canGoBack())
        self.forward_button.setEnabled(history.canGoForward())
        if view.loading:
            self.reload_button.setIcon(glyph_icon(G.STOP, size=16))
            self.reload_button.setToolTip("Detener")
        else:
            self.reload_button.setIcon(glyph_icon(G.REFRESH, size=16))
            self.reload_button.setToolTip("Recargar (F5)")

    def add_to_history(self, url):
        if url in self.history:
            self.history.remove(url)
        self.history.insert(0, url)
        del self.history[HISTORY_LIMIT:]
        self.history_model.setStringList(self.history)

    # ---------------------------------------------------------------- navegación

    def load_url(self, text=None):
        text = (text if isinstance(text, str) else self.url_bar.text()).strip()
        # Al elegir una sugerencia con Intro llegan tanto activated como returnPressed
        now = time.monotonic()
        last_text, last_time = self.last_navigation
        if not text or (text == last_text and now - last_time < 0.5):
            return
        self.last_navigation = (text, now)
        view = self.current_view()
        view.setUrl(to_url(text))
        view.setFocus()

    def go_back(self):
        history = self.current_view().history()
        if history.canGoBack():
            history.back()

    def go_forward(self):
        history = self.current_view().history()
        if history.canGoForward():
            history.forward()

    def go_home(self):
        self.current_view().setUrl(QUrl(HOME_URL))

    def reload_or_stop(self):
        view = self.current_view()
        if view.loading:
            view.stop()
        else:
            view.reload()

    def focus_url_bar(self):
        self.url_bar.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.url_bar.selectAll()

    # ---------------------------------------------------------------- búsqueda en la página

    def show_find_bar(self):
        self.find_bar.show()
        self.find_input.setFocus()
        self.find_input.selectAll()
        if self.find_input.text():
            self.find()

    def hide_find_bar(self):
        self.find_bar.hide()
        self.find_input.setProperty("notFound", False)
        self.repolish(self.find_input)
        view = self.current_view()
        view.page().findText("")
        view.setFocus()

    def find(self, backward=False):
        if not self.find_bar.isVisible():
            self.show_find_bar()
            return
        flags = QWebEnginePage.FindFlag(0)
        if backward:
            flags |= QWebEnginePage.FindFlag.FindBackward
        self.current_view().page().findText(self.find_input.text(), flags)
        if not self.find_input.text():
            self.find_count.clear()
            self.find_input.setProperty("notFound", False)
            self.repolish(self.find_input)

    def find_finished(self, view, result):
        if view is not self.current_view() or not self.find_bar.isVisible() or not self.find_input.text():
            return
        matches = result.numberOfMatches()
        self.find_count.setText(f"{result.activeMatch()} de {matches}" if matches else "Sin resultados")
        self.find_input.setProperty("notFound", matches == 0)
        self.repolish(self.find_input)

    @staticmethod
    def repolish(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    # ---------------------------------------------------------------- zoom, pantalla completa y herramientas

    def change_zoom(self, step):
        view = self.current_view()
        factor = view.zoomFactor()
        if step == 0:
            factor = 1.0
        elif step > 0:
            factor = next((zoom for zoom in ZOOM_LEVELS if zoom > factor + 0.001), ZOOM_LEVELS[-1])
        else:
            factor = next((zoom for zoom in reversed(ZOOM_LEVELS) if zoom < factor - 0.001), ZOOM_LEVELS[0])
        view.setZoomFactor(factor)
        self.update_zoom(view)

    def update_zoom(self, view):
        percent = round(view.zoomFactor() * 100)
        self.zoom_button.setText(f"{percent}%")
        self.zoom_button.setVisible(percent != 100)
        self.menu_zoom_label.setText(f"{percent}%")

    def toggle_fullscreen(self):
        self.set_fullscreen(not self.isFullScreen())

    def set_fullscreen(self, fullscreen):
        for widget in (self.top_bar, self.nav_bar, self.load_bar, self.statusBar()):
            widget.setVisible(not fullscreen)
        if fullscreen:
            self.showFullScreen()
        else:
            self.showNormal()

    def fullscreen_requested(self, request):
        # Pantalla completa solicitada por la página (p. ej. vídeos)
        request.accept()
        self.set_fullscreen(request.toggleOn())

    def open_devtools(self):
        if self.devtools is None:
            self.devtools = QWebEngineView()
            self.devtools.setWindowTitle(f"Herramientas de desarrollador — {APP_NAME}")
            self.devtools.setWindowIcon(self.windowIcon())
            self.devtools.resize(1100, 720)
            apply_dark_titlebar(self.devtools)
        self.current_view().page().setDevToolsPage(self.devtools.page())
        self.devtools.show()
        self.devtools.raise_()
        self.devtools.activateWindow()

    def save_session(self):
        urls = []
        for i in range(self.tab_bar.count()):
            view = self.tab_bar.tabData(i)
            if not view.is_start_page():
                urls.append(view.url().toString())
        self.settings.setValue("session", urls[:SESSION_LIMIT])

    def restore_session(self):
        # Reabre las pestañas de la última sesión (o la página de inicio la primera vez)
        urls = self.settings.value("session", [], type=list)
        for url in urls:
            self.add_tab(QUrl(url), background=True)
        if urls:
            self.tab_bar.setCurrentIndex(0)
            self.current_tab_changed(0)
        else:
            self.add_tab(QUrl(HOME_URL))

    # ---------------------------------------------------------------- seguridad y permisos

    def ask(self, title, text, accept_text, reject_text="Cancelar", icon=QMessageBox.Icon.Question):
        box = QMessageBox(icon, title, text, parent=self)
        box.setTextFormat(Qt.TextFormat.RichText)
        accept = box.addButton(accept_text, QMessageBox.ButtonRole.AcceptRole)
        reject = box.addButton(reject_text, QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(reject)
        box.exec()
        return box.clickedButton() is accept

    def permission_requested(self, permission):
        # La decisión queda guardada en el perfil y no se vuelve a preguntar para ese sitio
        what = PERMISSION_NAMES.get(permission.permissionType().name, "usar una función de tu equipo")
        host = escape(permission.origin().host() or permission.origin().toString())
        if self.ask("Permiso solicitado", f"<b>{host}</b> quiere {what}.", "Permitir", "Bloquear"):
            permission.grant()
        else:
            permission.deny()

    def certificate_error(self, error):
        logging.warning("Certificado no válido en %s: %s", error.url().toString(), error.description())
        if not error.isOverridable():
            error.rejectCertificate()
            return
        host = escape(error.url().host())
        if self.ask("Conexión no segura",
                    f"El certificado de seguridad de <b>{host}</b> no es válido:<br><i>{escape(error.description())}</i>"
                    f"<br><br>Si continúas, la información que envíes podría ser interceptada.",
                    "Continuar de todos modos", "Volver a un sitio seguro", QMessageBox.Icon.Warning):
            error.acceptCertificate()
        else:
            error.rejectCertificate()

    def authentication_required(self, url, authenticator, proxy_host=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Autenticación del proxy" if proxy_host else "Iniciar sesión")
        form = QFormLayout(dialog)
        form.setContentsMargins(20, 18, 20, 16)
        form.setVerticalSpacing(10)
        server = escape(proxy_host or url.host())
        realm = escape(authenticator.realm())
        info = QLabel(f"<b>{server}</b> solicita usuario y contraseña" + (f"<br><span style='color:{MUTED}'>{realm}</span>"
                                                                         if realm else ""))
        form.addRow(info)
        user = QLineEdit()
        password = QLineEdit()
        password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Usuario", user)
        form.addRow("Contraseña", password)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Iniciar sesión")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        apply_dark_titlebar(dialog)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            authenticator.setUser(user.text())
            authenticator.setPassword(password.text())
        else:
            # Un autenticador vacío cancela la petición
            sip.assign(authenticator, QAuthenticator())

    def select_client_certificate(self, selection):
        certificates = selection.certificates()
        if not certificates:
            selection.selectNone()
            return
        names = [f"{cert.subjectDisplayName()} — emitido por {cert.issuerDisplayName()} "
                 f"(vence {cert.expiryDate().toString('dd/MM/yyyy')})" for cert in certificates]
        name, ok = QInputDialog.getItem(self, "Certificado de cliente",
                                        f"{selection.host().host()} solicita un certificado para identificarte:",
                                        names, 0, False)
        if ok:
            selection.select(certificates[names.index(name)])
        else:
            selection.selectNone()

    def render_process_terminated(self, view, status, exit_code):
        if status == QWebEnginePage.RenderProcessTerminationStatus.NormalTerminationStatus:
            return
        url = view.url()
        logging.error("El proceso de la página %s terminó: %s (código %s)", url.toString(), status.name, exit_code)
        reasons = {
            "AbnormalTerminationStatus": "error interno",
            "CrashedTerminationStatus": "fallo del proceso",
            "KilledTerminationStatus": "proceso finalizado",
        }
        html = (CRASH_PAGE.replace("{{HOST}}", escape(url.host() or url.toString()))
                .replace("{{REASON}}", reasons.get(status.name, status.name))
                .replace("{{URL}}", escape(url.toString())))
        QTimer.singleShot(0, lambda: view.setHtml(html, url))

    def show_notification(self, notification):
        if self.tray is None:
            self.tray = QSystemTrayIcon(self.windowIcon(), self)
            self.tray.setToolTip(APP_NAME)
            self.tray.messageClicked.connect(self.bring_to_front)
            self.tray.show()
        self.notification = notification  # mantener viva la notificación mientras se muestra
        self.tray.showMessage(notification.title(), notification.message(), self.windowIcon(), 8000)
        notification.show()

    def bring_to_front(self):
        self.showNormal() if self.isMinimized() else self.show()
        self.raise_()
        self.activateWindow()

    # ---------------------------------------------------------------- PDF y datos de navegación

    def save_pdf(self):
        view = self.current_view()
        name = (view.title() or "pagina").strip()
        name = "".join(c for c in name if c not in '\\/:*?"<>|')[:80] or "pagina"
        default = os.path.join(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
                               f"{name}.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Guardar como PDF", default, "Documento PDF (*.pdf)")
        if path:
            self.statusBar().showMessage("Generando PDF…")
            view.page().printToPdf(path)

    def pdf_finished(self, path, ok):
        if ok:
            self.statusBar().showMessage(f"PDF guardado: {os.path.normpath(path)}", 8000)
        else:
            self.statusBar().clearMessage()
            QMessageBox.warning(self, "Guardar como PDF", f"No se pudo guardar {os.path.normpath(path)}")

    def clear_browsing_data(self):
        if not self.ask("Borrar datos de navegación",
                        "Se borrarán el historial, las cookies, la caché y los permisos concedidos.<br>"
                        "Tendrás que volver a iniciar sesión en los sitios.", "Borrar datos",
                        icon=QMessageBox.Icon.Warning):
            return
        self.history.clear()
        self.history_model.setStringList(self.history)
        self.closed_tabs.clear()
        self.profile.clearHttpCache()
        self.profile.clearAllVisitedLinks()
        self.profile.cookieStore().deleteAllCookies()
        for permission in self.profile.listAllPermissions():
            permission.reset()
        self.settings.setValue("history", [])
        logging.info("Datos de navegación borrados")
        self.statusBar().showMessage("Datos de navegación borrados", 6000)

    def show_about(self):
        QMessageBox.about(self, f"Acerca de {APP_NAME}",
                          f"<h3 style='color:{CYAN}'>{APP_NAME}</h3>"
                          f"<p>Versión {APP_VERSION}</p>"
                          f"<p style='color:{MUTED}'>Navegador seguro con pestañas basado en Qt WebEngine 6.</p>")

    # ---------------------------------------------------------------- descargas

    def download_requested(self, download):
        # Preguntar dónde guardar; si se cierra el diálogo la descarga se cancela
        suggested_path = os.path.join(download.downloadDirectory(), download.downloadFileName())
        path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo", os.path.normpath(suggested_path))

        # Un enlace de descarga abierto en una pestaña nueva deja esa pestaña vacía: se cierra
        view = self.view_for_page(download.page())
        if view is not None and not view.has_loaded:
            QTimer.singleShot(0, lambda: self.close_view(view))

        if not path:
            return

        download.setDownloadDirectory(os.path.dirname(path))
        download.setDownloadFileName(os.path.basename(path))
        download.receivedBytesChanged.connect(lambda: self.download_progress(download))
        download.isFinishedChanged.connect(lambda: self.download_finished(download))
        download.accept()
        self.downloads.append(download)
        self.update_downloads_button()

    def download_progress(self, download):
        name = download.downloadFileName()
        received, total = download.receivedBytes(), download.totalBytes()
        if total > 0:
            self.statusBar().showMessage(f"Descargando {name}: {received * 100 // total}%")
        else:
            self.statusBar().showMessage(f"Descargando {name}: {received // 1024} KB")

    def download_finished(self, download):
        if not download.isFinished():
            return
        self.update_downloads_button()
        path = self.download_path(download)
        if download.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            self.statusBar().showMessage(f"Descarga completada: {path}", 8000)
        else:
            self.statusBar().clearMessage()
            QMessageBox.warning(self, "Descarga fallida", f"No se pudo descargar {path}\n{download.interruptReasonString()}")

    @staticmethod
    def download_path(download):
        return os.path.normpath(os.path.join(download.downloadDirectory(), download.downloadFileName()))

    def update_downloads_button(self):
        active = any(d.state() == QWebEngineDownloadRequest.DownloadState.DownloadInProgress for d in self.downloads)
        self.downloads_button.setProperty("active", active)
        self.downloads_button.setIcon(glyph_icon(G.DOWNLOAD, CYAN if active else ICON, 16))
        self.repolish(self.downloads_button)

    def build_downloads_menu(self):
        menu = self.downloads_menu
        menu.clear()
        if not self.downloads:
            menu.addAction("No hay descargas").setEnabled(False)
        for download in reversed(self.downloads[-10:]):
            name = download.downloadFileName()
            path = self.download_path(download)
            state = download.state()
            if state == QWebEngineDownloadRequest.DownloadState.DownloadInProgress:
                total = download.totalBytes()
                percent = f"{download.receivedBytes() * 100 // total}%" if total > 0 else "…"
                menu.addAction(glyph_icon(G.DOWNLOAD, CYAN, 14), f"{name}    {percent}").setEnabled(False)
            elif state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
                add_menu_action(menu, name, lambda p=path: QDesktopServices.openUrl(QUrl.fromLocalFile(p)),
                                glyph_icon(G.CHECK, CYAN, 14))
            else:
                menu.addAction(glyph_icon(G.WARNING, RED, 14), f"{name}    (fallida)").setEnabled(False)
        menu.addSeparator()
        folder = self.downloads[-1].downloadDirectory() if self.downloads else \
            self.profile.downloadPath()
        add_menu_action(menu, "Abrir carpeta de descargas", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(folder)),
                        glyph_icon(G.FOLDER, ICON, 14))
        clear = add_menu_action(menu, "Limpiar lista", self.clear_downloads)
        clear.setEnabled(bool(self.downloads))

    def clear_downloads(self):
        self.downloads = [d for d in self.downloads if d.state() == QWebEngineDownloadRequest.DownloadState.DownloadInProgress]
        self.update_downloads_button()


def dark_palette():
    palette = QPalette()
    for role, color in ((QPalette.ColorRole.Window, SURFACE), (QPalette.ColorRole.WindowText, TEXT), (QPalette.ColorRole.Base, BG),
                        (QPalette.ColorRole.AlternateBase, SURFACE), (QPalette.ColorRole.Text, TEXT), (QPalette.ColorRole.Button, SURFACE_2),
                        (QPalette.ColorRole.ButtonText, TEXT), (QPalette.ColorRole.Highlight, "#0E7490"), (QPalette.ColorRole.HighlightedText, TEXT),
                        (QPalette.ColorRole.ToolTipBase, SURFACE), (QPalette.ColorRole.ToolTipText, TEXT), (QPalette.ColorRole.Link, CYAN),
                        (QPalette.ColorRole.PlaceholderText, "#5B6B88")):
        palette.setColor(role, QColor(color))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#4A5874"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#4A5874"))
    return palette


if __name__ == "__main__":
    setup_logging()
    set_app_user_model_id()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    app.setPalette(dark_palette())
    app.setFont(QFont("Segoe UI", 9))
    if "Segoe Fluent Icons" in QFontDatabase.families():
        ICON_FONT = "Segoe Fluent Icons"
    app.setStyleSheet(STYLESHEET)
    # Debe ejecutarse antes de crear el perfil web, que bloquea su carpeta
    migration_error = migrate_legacy_data(data_dir(), app_settings(), find_legacy_data_dir(local_data_root()),
                                          find_legacy_settings())
    if migration_error:
        QMessageBox.warning(None, APP_NAME, migration_error)
        sys.exit(1)
    profile = create_profile()
    main_window = MainWindow(profile)
    main_window.show()
    logging.info("%s %s iniciado", APP_NAME, APP_VERSION)
    exit_code = app.exec()
    del main_window  # las páginas deben destruirse antes que su perfil
    sys.exit(exit_code)
