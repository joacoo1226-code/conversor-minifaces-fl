# -*- coding: utf-8 -*-
"""
Bot de minifaces cmtracker -> Football Life 26 (PES 2021 + Sider)  -- con ventana

  1. Elegís la liga de tu mundo FL en la lista.
  2. Abre cmtracker en Chrome y junta los jugadores de esa liga (nombre, equipo, cara).
  3. Los cruza con fl26playerids.json de tu mundo (por equipo y nombre).
  4. Guarda cada cara en DDS 128x128 DXT5 con el ID del juego, en una carpeta lista para copiar:
       Minifaces por liga\\Minifaces <liga>\\common\\render\\symbol\\player\\<ID>.dds   (una carpeta por liga)
       Minifaces por liga\\fl26world.txt   (esos jugadores pasan a 'newfaces3d')
     El bot NO toca el juego: deja las carpetas en el disco para que las instales o compartas vos.
  5. Deja un informe con los que no pudo emparejar.
"""
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import unicodedata
from difflib import SequenceMatcher
from io import BytesIO
from urllib.parse import urlparse, parse_qs

CONGELADO = getattr(sys, "frozen", False)          # True cuando corre como .exe
# como .exe, los archivos (config, base, salida) van al lado del .exe y no a la carpeta temporal
AQUI = os.path.dirname(os.path.abspath(sys.executable if CONGELADO else __file__))
NUEVOS_EN_JUEGO = "(Jugadores nuevos en clubes que ya trae el juego)"
TODAS_LIGAS = "(Todas las ligas, una carpeta por liga)"
CONFIG_FILE = os.path.join(AQUI, "config_minifaces.json")
SALIDA = os.path.join(AQUI, "Minifaces por liga")
WORLD_TXT = os.path.join(SALIDA, "fl26world.txt")
MARCA_MUNDO = os.path.join(SALIDA, "mundo.txt")


def carpeta_liga(liga):
    """carpeta de contenido de una liga (se copia entera a SiderAddons\\livecpk\\)"""
    return os.path.join(SALIDA, "Minifaces " + nombre_archivo(liga).rstrip(". "))


def destino_liga(liga):
    return os.path.join(carpeta_liga(liga), "common", "render", "symbol", "player")


def escribir_leeme(liga, carpeta_mundo):
    """LEEME de la carpeta de la liga, con los IDs que tienen miniface (para compartirla)"""
    d = destino_liga(liga)
    ids = sorted(int(f[:-4]) for f in os.listdir(d) if f.lower().endswith(".dds") and f[:-4].isdigit()) \
        if os.path.isdir(d) else []
    nombre = os.path.basename(carpeta_liga(liga))
    mundo = os.path.basename(os.path.normpath(carpeta_mundo or ""))
    with open(os.path.join(carpeta_liga(liga), "LEEME.txt"), "w", encoding="utf-8") as f:
        f.write(f"Minifaces de {liga} ({len(ids)} jugadores) para el mundo {mundo} de FL Mod Studio.\n"
                "Los archivos tienen el ID de los jugadores en ESE mundo: en otro mundo no sirven.\n\n"
                "Instalación:\n"
                f"1) Copiá la carpeta '{nombre}' a ...\\SiderAddons\\livecpk\\\n"
                f"2) En SiderAddons\\sider.ini agregá arriba de todo los cpk.root:\n"
                f"      cpk.root = \".\\livecpk\\{nombre}\"\n"
                "   (o FL Mod Studio > Carpetas de contenido > Añadir carpeta... > arriba del todo > Aplicar)\n"
                "3) Para que el juego muestre estas minifaces, en SiderAddons\\modules\\fl26world.txt\n"
                "   estos IDs tienen que estar en 'newfaces3d' y no en 'newfaces' (el bot ya te deja un\n"
                "   fl26world.txt listo en la carpeta 'Minifaces por liga'):\n\n")
        f.write("newfaces3d " + " ".join(_rangos(ids)) + "\n")
    return len(ids)

CONFIG_DEFAULT = {
    "carpeta_mundo": "",          # carpeta que tiene fl26playerids.json
    "db": "26110300",             # base de datos de cmtracker (sale del link)
    "tamano": 128,                # las minifaces de FL Mod Studio son 128x128 DXT5
    "formato_dds": "DXT5",
    "pausa_descarga": 0.15,       # segundos entre descargas
    "ligas_cmtracker": {          # liga del FL -> número de liga en cmtracker (league__in=)
        "2. Bundesliga": 20
    },
    "fuente": "cmtracker",        # "cmtracker" (caras del FC) o "sortitoutsi" (fotos recortadas del FM)
    "carpeta_megapack": "",       # opcional: carpeta del megapack de sortitoutsi (face_<id>.png)
    "ligas_sortitoutsi": {        # liga del FL -> número de competición en sortitoutsi (.../competition/<n>)
        "2. Bundesliga": 23
    },
}


# ------------------------------------------------------------------ dependencias
def asegurar_dependencias():
    """instala playwright y pillow si faltan (o si pillow es viejo y no sabe guardar DDS DXT5)"""
    if CONGELADO:          # el .exe ya trae todo adentro
        return
    falta = []
    try:
        import playwright  # noqa: F401
    except ImportError:
        falta.append("playwright")
    try:
        import PIL
        v = tuple(int(x) for x in PIL.__version__.split(".")[:2])
        if v < (11, 2):
            falta.append("pillow")
    except Exception:
        falta.append("pillow")
    if falta:
        print("Instalando lo necesario (solo la primera vez): " + ", ".join(falta))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + falta)
        # volver a arrancar el bot (en Windows os.execv deja la consola colgada)
        print("Listo, arrancando el bot...")
        sys.exit(subprocess.call([sys.executable] + sys.argv))


# ------------------------------------------------------------------ utilidades
def cargar_config():
    cfg = json.loads(json.dumps(CONFIG_DEFAULT))
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                guardado = json.load(f)
        except Exception:
            guardado = {}
        mapas = {k: dict(cfg[k]) for k in ("ligas_cmtracker", "ligas_sortitoutsi")}
        for k in mapas:
            mapas[k].update(guardado.get(k, {}))
        cfg.update(guardado)
        cfg.update(mapas)
    return cfg


def guardar_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


ESPECIALES = str.maketrans({"ø": "o", "Ø": "o", "æ": "ae", "Æ": "ae", "ß": "ss", "ł": "l", "Ł": "l",
                            "đ": "d", "Đ": "d", "ð": "d", "þ": "th", "ı": "i", "œ": "oe"})


def norm(s):
    s = (s or "").translate(ESPECIALES)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def nombre_archivo(s):
    return re.sub(r'[\\/:*?"<>|]', "_", s).strip()


def buscar_mundo_por_defecto():
    home = os.path.expanduser("~")
    for esc in ("OneDrive\\Escritorio", "OneDrive\\Desktop", "Escritorio", "Desktop"):
        c = os.path.join(home, esc, "_FL26-27-Def", "SiderAddons", "livecpk", "_FL26-27-Def")
        if os.path.exists(os.path.join(c, "fl26playerids.json")):
            return c
    return ""


def buscar_mundo_adentro(carpeta, prof=0):
    """busca fl26playerids.json en las subcarpetas (hasta 4 niveles, sin entrar a 'common')"""
    if prof > 4:
        return None
    try:
        hijos = [e for e in os.scandir(carpeta) if e.is_dir(follow_symlinks=False)]
    except OSError:
        return None
    for e in hijos:
        if os.path.exists(os.path.join(e.path, "fl26playerids.json")):
            return e.path
    for e in hijos:
        if e.name.lower() not in ("common", "asset", "content", "_packs", "modules"):
            r = buscar_mundo_adentro(e.path, prof + 1)
            if r:
                return r
    return None


def es_mundo(carpeta):
    return bool(carpeta) and os.path.exists(os.path.join(carpeta, "fl26playerids.json"))


# ------------------------------------------------------------------ datos del FL
def cargar_mundo(carpeta):
    with open(os.path.join(carpeta, "fl26playerids.json"), encoding="utf-8") as f:
        d = json.load(f)
    ligas = {}
    for clave, ids in (d.get("clubs") or {}).items():
        if "/" in clave:                       # club nuevo de una liga del mundo: "Liga/n"
            liga, idx = clave.rsplit("/", 1)
            idx = int(idx) if idx.isdigit() else idx
        else:                                  # jugadores nuevos agregados a un club que ya trae el juego
            liga, idx = NUEVOS_EN_JUEGO, (int(clave) if clave.isdigit() else clave)
        nombres = (d.get("names") or {}).get(clave, {})
        jugadores = [(int(v), nombres.get(k, "")) for k, v in ids.items() if str(v).lstrip("-").isdigit()]
        if jugadores:
            ligas.setdefault(liga, {})[idx] = jugadores
    return ligas


# ------------------------------------------------------------------ emparejar
def emparejar(cm_jugadores, clubes_fl):
    """Devuelve (pares, no_encontrados, asignacion). Cada par = (jugador_cm, fl_id, fl_nombre)."""
    fl_por_club = {i: [(pid, n, norm(n)) for pid, n in js] for i, js in clubes_fl.items()}

    # 1) cada equipo de cmtracker -> el club del FL con más nombres en común
    equipos_cm = {}
    for j in cm_jugadores:
        equipos_cm.setdefault(j["equipo"], []).append(j)
    asignacion = {}
    for eq, js in equipos_cm.items():
        nombres_cm = {norm(j["nombre"]) for j in js}
        mejor, puntos = None, 0
        for i, fl in fl_por_club.items():
            p = sum(1 for _, _, n in fl if n in nombres_cm)
            if p > puntos:
                mejor, puntos = i, p
        if mejor is not None and puntos >= 3:
            asignacion[eq] = mejor

    usados = set()
    pares, faltan = [], []

    def buscar(j, candidatos, estricto=False):
        """estricto (búsqueda en toda la liga): solo nombre idéntico o uno contenido en el otro"""
        n = norm(j["nombre"])
        libres = [c for c in candidatos if c[0] not in usados]
        for c in libres:
            if c[2] == n:
                return c
        partes = n.split()
        if estricto:
            if len(partes) < 2:
                return None
            m = [c for c in libres if len(c[2].split()) >= 2 and
                 (set(partes) <= set(c[2].split()) or set(c[2].split()) <= set(partes))]
            return m[0] if len(m) == 1 else None
        if partes:
            ap, ini = partes[-1], partes[0][0]
            m = [c for c in libres if c[2].split() and c[2].split()[-1] == ap and c[2][0] == ini]
            if len(m) == 1:
                return m[0]
            m = [c for c in libres if set(partes) <= set(c[2].split()) or set(c[2].split()) <= set(partes)]
            if len(m) == 1:
                return m[0]
        mejor, r = None, 0
        for c in libres:
            x = SequenceMatcher(None, n, c[2]).ratio()
            if x > r:
                mejor, r = c, x
        if mejor and r >= 0.85:
            return mejor
        return None

    pendientes = []
    for j in cm_jugadores:
        idx = asignacion.get(j["equipo"])
        c = buscar(j, fl_por_club[idx]) if idx is not None else None
        if c:
            usados.add(c[0])
            pares.append((j, c[0], c[1]))
        else:
            pendientes.append(j)

    # 2) los que no aparecieron en su equipo: en toda la liga (fichajes, préstamos)
    todos = [c for fl in fl_por_club.values() for c in fl]
    for j in pendientes:
        c = buscar(j, todos, estricto=True)
        if c:
            usados.add(c[0])
            pares.append((j, c[0], c[1]))
        else:
            faltan.append(j)
    return pares, faltan, asignacion


# ------------------------------------------------------------------ navegador
class Cancelado(Exception):
    pass


def abrir_navegador(pw, avisar):
    perfil = os.path.join(AQUI, "perfil_chrome")
    opciones = dict(user_data_dir=perfil, headless=False,
                    args=["--disable-blink-features=AutomationControlled"],
                    ignore_default_args=["--enable-automation"], viewport=None)
    avisar(0.01, "Abriendo Chrome...")
    try:
        return pw.chromium.launch_persistent_context(channel="chrome", **opciones)
    except Exception:
        try:
            return pw.chromium.launch_persistent_context(**opciones)
        except Exception:
            if CONGELADO:
                raise RuntimeError("No encontré Google Chrome. Instalalo (google.com/chrome) y probá de nuevo.")
            avisar(0.01, "No encontré Chrome: bajando el navegador de Playwright (una sola vez)...")
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
            return pw.chromium.launch_persistent_context(**opciones)


def esperar_carga(page):
    try:
        page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception:
        pass


# ------------------------------------------------------------------ cmtracker


def leer_cmtracker(liga_cm, db, cfg, avisar, cancelado):
    """avisar(fraccion 0..1 o None, texto o None, log=None); cancelado() -> bool"""
    from playwright.sync_api import sync_playwright

    base = "https://cmtracker.net/es/players?sort=overallrating%3Adesc&limit=100&page={p}&league__in={l}&db={db}"
    jugadores, vistos = [], set()
    JS = """() => [...document.querySelectorAll('td[data-field="player"]')].map(td => {
              const i = td.querySelector('img');
              const a = td.querySelector('a[title]');
              const l = td.querySelector('a[href*="/players/"]');
              const n = l ? l.innerText.trim() : '';
              return {nombre: n || (i ? i.alt : ''), equipo: a ? a.title : '',
                      url: i ? i.src : '', link: l ? l.getAttribute('href') : ''};
            })"""
    with sync_playwright() as pw:
        ctx = abrir_navegador(pw, avisar)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            total, p = None, 0
            while True:
                if cancelado():
                    raise Cancelado()
                avisar(0.02 + 0.18 * min(1, (p * 100) / (total or 600)),
                       f"Leyendo cmtracker, página {p + 1}... (si aparece la verificación, tildala en Chrome)")
                page.goto(base.format(p=p, l=liga_cm, db=db), wait_until="domcontentloaded")
                try:
                    page.wait_for_selector('td[data-field="player"]', timeout=180_000)
                except Exception:
                    avisar(None, None, "No cargó la lista de jugadores (¿liga vacía o verificación sin pasar?).")
                    break
                esperar_carga(page)
                time.sleep(1.5)
                if total is None:
                    nums = [int(re.sub(r"[.,]", "", x)) for x in
                            re.findall(r"([\d.,]+)[  ]+jugadores", page.inner_text("body"))]
                    if nums:
                        total = max(nums)
                        avisar(None, None, f"cmtracker tiene {total} jugadores en esta liga")
                filas = page.evaluate(JS)
                nuevos = 0
                for f in filas:
                    clave = f["link"] or (f["nombre"] + "|" + f["equipo"])
                    if clave in vistos:
                        continue
                    vistos.add(clave)
                    m = re.search(r"/heads/p(\d+)\.png", f["url"])
                    f["ea_id"] = m.group(1) if m else None
                    jugadores.append(f)
                    nuevos += 1
                avisar(None, None, f"Página {p + 1}: {nuevos} jugadores")
                p += 1
                if nuevos == 0 or len(filas) < 100 or p >= 60:
                    break

            imagenes = {}
            con_cara = [j for j in jugadores if j["ea_id"]]
            for n, j in enumerate(con_cara, 1):
                if cancelado():
                    raise Cancelado()
                try:
                    r = ctx.request.get(j["url"], timeout=30_000)
                    if r.ok:
                        imagenes[j["url"]] = r.body()
                except Exception:
                    pass
                avisar(0.20 + 0.70 * n / max(1, len(con_cara)), f"Bajando caras: {n} de {len(con_cara)}")
                time.sleep(cfg["pausa_descarga"])
        finally:
            ctx.close()
    return jugadores, imagenes


# ------------------------------------------------------------------ sortitoutsi
SOI = "https://sortitoutsi.net/football-manager-data-update"
SOI_CARA = "https://sortitoutsi.b-cdn.net/uploads/face/face_{id}.png"


def carpetas_megapack(carpeta):
    """la carpeta elegida y sus subcarpetas 'faces' (hasta 2 niveles)"""
    if not carpeta or not os.path.isdir(carpeta):
        return []
    out = [carpeta]
    try:
        for e in os.scandir(carpeta):
            if e.is_dir():
                if e.name.lower() == "faces":
                    out.append(e.path)
                try:
                    for e2 in os.scandir(e.path):
                        if e2.is_dir() and e2.name.lower() == "faces":
                            out.append(e2.path)
                except OSError:
                    pass
    except OSError:
        pass
    return out


def cara_local(dirs, fm_id):
    for d in dirs:
        for n in (f"face_{fm_id}.png", f"{fm_id}.png"):
            f = os.path.join(d, n)
            if os.path.exists(f):
                with open(f, "rb") as fh:
                    return fh.read()
    return None


JS_EQUIPOS_SOI = r"""() => {
    const t = [...document.querySelectorAll('table')].find(t => t.querySelector('a[href*="/football-manager-data-update/team/"]'));
    if (!t) return [];
    const vistos = new Set(), out = [];
    t.querySelectorAll('a[href*="/football-manager-data-update/team/"]').forEach(a => {
        const m = a.getAttribute('href').match(/team\/(\d+)/);
        if (m && !vistos.has(m[1]) && a.innerText.trim()) { vistos.add(m[1]); out.push([m[1], a.innerText.trim()]); }
    });
    return out;
}"""
JS_PLANTEL_SOI = r"""() => {
    // las tablas de jugadores (los del juego y los creados por sortitoutsi); no la de contratos/staff
    const ts = [...document.querySelectorAll('table')].filter(t =>
        [...t.querySelectorAll('th')].some(th => /Potential Ability|Position/.test(th.innerText)));
    const vistos = new Set(), out = [];
    ts.forEach(t => t.querySelectorAll('a[href*="person/"]').forEach(a => {
        const m = a.getAttribute('href').match(/person\/(\d+)/);
        if (m && !vistos.has(m[1])) { vistos.add(m[1]); out.push([m[1], a.innerText.trim()]); }
    }));
    return out;
}"""


def leer_sortitoutsi(comp_id, cfg, avisar, cancelado):
    from playwright.sync_api import sync_playwright

    dirs = carpetas_megapack(cfg.get("carpeta_megapack", ""))
    if cfg.get("carpeta_megapack"):
        avisar(None, None, ("Usando el megapack de: " + ", ".join(dirs)) if dirs else
               "No encontré la carpeta del megapack: bajo las caras de internet.")
    jugadores, imagenes = [], {}
    with sync_playwright() as pw:
        ctx = abrir_navegador(pw, avisar)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            avisar(0.03, "Leyendo la liga en sortitoutsi...")
            page.goto(f"{SOI}/competition/{comp_id}", wait_until="domcontentloaded")
            page.wait_for_selector('a[href*="/football-manager-data-update/team/"]', timeout=180_000)
            esperar_carga(page)
            equipos = page.evaluate(JS_EQUIPOS_SOI)
            avisar(None, None, f"sortitoutsi: {len(equipos)} equipos en la liga")
            for k, (tid, tnombre) in enumerate(equipos, 1):
                if cancelado():
                    raise Cancelado()
                avisar(0.03 + 0.17 * k / max(1, len(equipos)), f"Leyendo planteles: {tnombre} ({k} de {len(equipos)})")
                page.goto(f"{SOI}/team/{tid}", wait_until="domcontentloaded")
                try:
                    page.wait_for_selector("table th", timeout=60_000)
                except Exception:
                    avisar(None, None, f"  {tnombre}: no cargó el plantel")
                    continue
                esperar_carga(page)
                plantel = page.evaluate(JS_PLANTEL_SOI)
                for fm_id, nombre in plantel:
                    jugadores.append({"nombre": nombre, "equipo": tnombre, "url": "fm:" + fm_id, "fm_id": fm_id})
                avisar(None, None, f"  {tnombre}: {len(plantel)} jugadores")
                time.sleep(0.5)

            locales = 0
            for n, j in enumerate(jugadores, 1):
                if cancelado():
                    raise Cancelado()
                datos = cara_local(dirs, j["fm_id"]) if dirs else None
                if datos:
                    locales += 1
                else:
                    try:
                        r = ctx.request.get(SOI_CARA.format(id=j["fm_id"]), timeout=30_000)
                        if r.ok:
                            datos = r.body()
                        time.sleep(cfg["pausa_descarga"])
                    except Exception:
                        pass
                if datos:
                    imagenes[j["url"]] = datos
                avisar(0.20 + 0.70 * n / max(1, len(jugadores)), f"Buscando caras: {n} de {len(jugadores)}")
            if dirs:
                avisar(None, None, f"{locales} caras salieron del megapack, el resto de internet")
        finally:
            ctx.close()
    return jugadores, imagenes


# ------------------------------------------------------------------ guardar
def guardar_dds(pares, imagenes, cfg, avisar, destino):
    from PIL import Image

    os.makedirs(destino, exist_ok=True)
    t = int(cfg["tamano"])
    ok, sin_foto, ids = 0, [], []
    for k, (j, pid, _) in enumerate(pares, 1):
        datos = imagenes.get(j["url"])
        if not datos:
            sin_foto.append(j)
            continue
        try:
            img = Image.open(BytesIO(datos)).convert("RGBA")
        except Exception:
            img = None
        if img is None or img.width < 40 or img.getbbox() is None:
            sin_foto.append(j)
            continue
        img.resize((t, t), Image.LANCZOS).save(os.path.join(destino, f"{pid}.dds"),
                                               pixel_format=cfg["formato_dds"])
        ok += 1
        ids.append(pid)
        avisar(0.90 + 0.09 * k / max(1, len(pares)), f"Convirtiendo a DDS: {k} de {len(pares)}")
    return ok, sin_foto, ids


def _rangos(ids):
    out, ids = [], sorted(ids)
    i = 0
    while i < len(ids):
        j = i
        while j + 1 < len(ids) and ids[j + 1] == ids[j] + 1:
            j += 1
        out.append(f"{ids[i]}-{ids[j]}" if j > i else str(ids[i]))
        i = j + 1
    return out


def actualizar_world_txt(carpeta_mundo, ids_con_cara):
    """fl26regen le pone a cada jugador de 'newfaces' una cara del pack de regens Y su miniface,
    tapando la nuestra. En 'newfaces3d' conservan la cara 3D del pack pero usan su propia miniface."""
    # el acumulado del bot; si no, el que usa el juego (SiderAddons\\modules); si no, el del mundo
    candidatos = [WORLD_TXT,
                  os.path.join(os.path.dirname(os.path.dirname(os.path.normpath(carpeta_mundo))), "modules", "fl26world.txt"),
                  os.path.join(carpeta_mundo, "fl26world.txt")]
    origen = next((c for c in candidatos if os.path.exists(c)), None)
    if not origen:
        return None
    with open(origen, encoding="utf-8") as f:
        lineas = f.read().splitlines()
    nuevas, movidos, _ = pasar_a_3d(lineas, ids_con_cara)
    os.makedirs(os.path.dirname(WORLD_TXT), exist_ok=True)
    with open(WORLD_TXT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(nuevas) + "\n")
    return movidos


def pasar_a_3d(lineas, ids_con_cara):
    """líneas de un fl26world.txt -> (líneas nuevas, cuántos pasaron a newfaces3d, cuántos hay en newfaces)"""
    nf, n3 = set(), set()
    for l in lineas:
        m = re.match(r"\s*(newfaces3?d?)\s+(.*)$", l)
        if m:
            dst = n3 if m.group(1) == "newfaces3d" else nf
            for a, b in re.findall(r"(\d+)-?(\d*)", m.group(2)):
                dst.update(range(int(a), int(b or a) + 1))
    total = len(nf) + len(n3)
    mover = nf & set(ids_con_cara)
    if not mover:
        return lineas, 0, total
    nf -= mover
    n3 |= mover
    nuevas, puesto = [], False
    for l in lineas:
        if re.match(r"\s*newfaces3?d?\s", l):
            if not puesto:
                if nf:
                    nuevas.append("newfaces " + " ".join(_rangos(nf)))
                if n3:
                    nuevas.append("newfaces3d " + " ".join(_rangos(n3)))
                puesto = True
            continue
        nuevas.append(l)
    return nuevas, len(mover), total


def buscar_sider(carpeta):
    """la carpeta SiderAddons a partir de la del juego (o de la propia SiderAddons)"""
    for c in (carpeta, os.path.join(carpeta, "SiderAddons")):
        if os.path.exists(os.path.join(c, "sider.ini")):
            return c
    try:
        for e in os.scandir(carpeta):
            if e.is_dir() and os.path.exists(os.path.join(e.path, "SiderAddons", "sider.ini")):
                return os.path.join(e.path, "SiderAddons")
    except OSError:
        pass
    return None


def activar_minifaces(carpeta, avisar, cancelado):
    """mira TODAS las minifaces que el juego tiene activas (las carpetas cpk.root del sider.ini, sean
    del bot o de cualquier otro pack) y en SiderAddons\\modules\\fl26world.txt pasa esos jugadores a
    'newfaces3d', para que el mundo de FL Mod Studio no las tape con las genéricas."""
    sider = buscar_sider(carpeta)
    if not sider:
        raise RuntimeError("No encontré SiderAddons\\sider.ini en esa carpeta.\nElegí la carpeta del juego.")
    world = os.path.join(sider, "modules", "fl26world.txt")
    if not os.path.exists(world):
        raise RuntimeError("No hay SiderAddons\\modules\\fl26world.txt: no tenés un mundo de FL Mod Studio instalado.")
    raices = []
    with open(os.path.join(sider, "sider.ini"), encoding="utf-8", errors="replace") as f:
        for l in f:
            m = re.match(r'\s*cpk\.root\s*=\s*"([^"]+)"', l)
            if m:
                r = m.group(1).replace("\\", os.sep).replace("/", os.sep)
                raices.append(os.path.normpath(os.path.join(sider, r) if r.startswith(".") else r))
    ids, carpetas = set(), 0
    for k, raiz in enumerate(raices, 1):
        if cancelado():
            raise Cancelado()
        d = os.path.join(raiz, "common", "render", "symbol", "player")
        if os.path.isdir(d):
            antes = len(ids)
            ids |= {int(f[:-4]) for f in os.listdir(d) if f.lower().endswith(".dds") and f[:-4].isdigit()}
            if len(ids) > antes:
                carpetas += 1
                avisar(None, None, f"  {os.path.basename(raiz)}: minifaces encontradas")
        avisar(0.1 + 0.7 * k / max(1, len(raices)), f"Revisando carpetas activas: {k} de {len(raices)}")
    with open(world, encoding="utf-8") as f:
        lineas = f.read().splitlines()
    nuevas, movidos, total = pasar_a_3d(lineas, ids)
    if movidos:
        copia = world + ".antes_minifaces"
        if not os.path.exists(copia):
            shutil.copy2(world, copia)
        with open(world, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(nuevas) + "\n")
    avisar(1.0, "¡Listo!")
    return dict(minifaces=len(ids), carpetas=carpetas, movidos=movidos, nuevos=total, world=world)


def escribir_informe(liga, liga_cm, ok, pares, faltan, sin_foto):
    informe = os.path.join(AQUI, f"informe_{nombre_archivo(liga)}.txt")
    with open(informe, "w", encoding="utf-8") as f:
        f.write(f"Liga: {liga}  |  fuente: {liga_cm}\n")
        f.write(f"Minifaces hechas: {ok}\n\n")
        f.write("EMPAREJADOS (cmtracker -> FL):\n")
        for j, pid, n in sorted(pares, key=lambda x: (x[0]["equipo"], x[0]["nombre"])):
            marca = "" if norm(j["nombre"]) == norm(n) else "   <-- revisar"
            f.write(f"  {j['equipo']:<28} {j['nombre']:<30} -> {pid} {n}{marca}\n")
        f.write("\nNO ENCONTRADOS EN TU FL (sin miniface):\n")
        for j in sorted(faltan, key=lambda x: (x["equipo"], x["nombre"])):
            f.write(f"  {j['equipo']:<28} {j['nombre']}\n")
        f.write("\nSIN FOTO EN LA FUENTE:\n")
        for j in sorted(sin_foto, key=lambda x: (x["equipo"], x["nombre"])):
            f.write(f"  {j['equipo']:<28} {j['nombre']}\n")
    return informe


def trabajo(liga, clubes_fl, id_fuente, carpeta, cfg, avisar, cancelado):
    """todo el proceso de una liga; devuelve un resumen (dict)"""
    if cfg["fuente"] == "sortitoutsi":
        jugadores, imagenes = leer_sortitoutsi(id_fuente, cfg, avisar, cancelado)
    else:
        jugadores, imagenes = leer_cmtracker(id_fuente, cfg["db"], cfg, avisar, cancelado)
    if not jugadores:
        raise RuntimeError("No se leyó ningún jugador de " + cfg["fuente"] + ".")
    avisar(0.90, "Cruzando jugadores con tu mundo...")
    pares, faltan, asignacion = emparejar(jugadores, clubes_fl)
    ok, sin_foto, ids = guardar_dds(pares, imagenes, cfg, avisar, destino_liga(liga))
    movidos = actualizar_world_txt(carpeta, ids)
    with open(MARCA_MUNDO, "w", encoding="utf-8") as f:
        f.write(carpeta)
    escribir_leeme(liga, carpeta)
    informe = escribir_informe(liga, f"{cfg['fuente']} {id_fuente}", ok, pares, faltan, sin_foto)
    avisar(1.0, "¡Listo!")
    return dict(ok=ok, faltan=len(faltan), sin_foto=len(sin_foto), equipos=len(asignacion),
                equipos_cm=len({j["equipo"] for j in jugadores}), movidos=movidos, informe=informe,
                carpeta=carpeta_liga(liga))


# ------------------------------------------------------------------ base FM -> PES
BASE_JSON = os.path.join(AQUI, "base_fm_pes.json")
BASE_CSV = os.path.join(AQUI, "base_fm_pes.csv")
BASE_SIN = os.path.join(AQUI, "base_sin_id_fm.txt")
CACHE_SOI = os.path.join(AQUI, "cache_sortitoutsi.json")
SOI_WEB = "https://sortitoutsi.net"

JS_BUSQUEDA = r"""() => [...document.querySelectorAll('tr')]
    .filter(tr => tr.querySelector('a.item-title[href*="/person/"]'))
    .map(tr => {
        const p = tr.querySelector('a.item-title'), t = tr.querySelector('a[href*="/team/"]'),
              c = tr.querySelector('a[href*="/competition/"]');
        const id = (a, k) => a ? (a.getAttribute('href').match(new RegExp(k + '/(\\d+)')) || [])[1] || null : null;
        return {fm: id(p, 'person'), nombre: p.innerText.trim(), equipo: id(t, 'team'),
                equipo_nombre: t ? t.innerText.trim() : '', comp: id(c, 'competition')};
    })"""


def cargar_cache():
    try:
        with open(CACHE_SOI, encoding="utf-8") as f:
            c = json.load(f)
    except Exception:
        c = {}
    for k in ("busq", "comp", "equipo"):
        c.setdefault(k, {})
    return c


def guardar_cache(c):
    tmp = CACHE_SOI + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False)
    os.replace(tmp, CACHE_SOI)


def cargar_base():
    try:
        with open(BASE_JSON, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def elegir_sondas(jugadores, cuantas):
    """jugadores [(pes_id, nombre)] -> los nombres más 'únicos' (largos, con nombre y apellido)"""
    cand = [n for _, n in jugadores if len(norm(n).split()) >= 2 and len(norm(n)) >= 9]
    cand.sort(key=lambda n: -len(norm(n)))
    return cand[:cuantas]


class Sortitoutsi:
    """lee sortitoutsi con el navegador abierto (con caché en disco)"""

    def __init__(self, ctx, cache, cancelado):
        self.page = ctx.pages[0] if ctx.pages else ctx.new_page()
        self.cache, self.cancelado = cache, cancelado
        self.nuevas = 0
        self.con_filtro = False
        self.busquedas_vacias = 0
        self.busquedas_con_algo = 0

        def filtro(route):
            req = route.request
            host = urlparse(req.url).hostname or ""
            if req.resource_type in ("image", "media", "font") or "sortitoutsi" not in host:
                return route.abort()
            return route.continue_()
        try:
            self.page.route("**/*", filtro)   # sin imágenes ni publicidad: carga mucho más rápido
            self.con_filtro = True
        except Exception:
            pass

    def _ir(self, url, selector):
        if self.cancelado():
            raise Cancelado()
        for intento in range(3):
            try:
                self.page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                try:
                    self.page.wait_for_selector(selector, timeout=10_000)
                except Exception:
                    pass
                self.nuevas += 1
                time.sleep(0.3)
                return True
            except Exception:
                time.sleep(3 * (intento + 1))
        return False

    def buscar(self, nombre):
        k = norm(nombre)
        if k in self.cache["busq"]:
            return self.cache["busq"][k]
        from urllib.parse import quote_plus
        res = []
        if self._ir(f"{SOI_WEB}/search/database?search={quote_plus(nombre)}&game_id=26", "a.item-title"):
            res = self.page.evaluate(JS_BUSQUEDA)
        if res:
            self.busquedas_con_algo += 1
        else:
            self.busquedas_vacias += 1
            # si al principio nada devuelve resultados, puede ser el filtro de carga: lo saco y reintento
            if self.con_filtro and self.busquedas_con_algo == 0 and self.busquedas_vacias >= 6:
                try:
                    self.page.unroute("**/*")
                except Exception:
                    pass
                self.con_filtro = False
                for kk in [x for x, v in self.cache["busq"].items() if not v]:
                    del self.cache["busq"][kk]
                return self.buscar(nombre)
        self.cache["busq"][k] = res
        return res

    def equipos(self, comp):
        comp = str(comp)
        if comp not in self.cache["comp"]:
            res = []
            if self._ir(f"{SOI}/competition/{comp}", 'a[href*="/football-manager-data-update/team/"]'):
                res = self.page.evaluate(JS_EQUIPOS_SOI)
            self.cache["comp"][comp] = res
        return self.cache["comp"][comp]

    def plantel(self, equipo):
        equipo = str(equipo)
        if equipo not in self.cache["equipo"]:
            res = []
            if self._ir(f"{SOI}/team/{equipo}", "table th"):
                res = self.page.evaluate(JS_PLANTEL_SOI)
            self.cache["equipo"][equipo] = res
        return self.cache["equipo"][equipo]


def armar_base(carpeta, cfg, avisar, cancelado):
    """recorre todas las ligas del mundo y arma la tabla ID FM -> ID PES"""
    from playwright.sync_api import sync_playwright
    from collections import Counter

    ligas = cargar_mundo(carpeta)
    nombres_ligas = sorted(ligas, key=norm)
    total_pes = sum(len(c) for v in ligas.values() for c in v.values())
    cache = cargar_cache()
    filas, sin = [], {}
    usados_fm = set()

    with sync_playwright() as pw:
        ctx = abrir_navegador(pw, avisar)
        try:
            soi = Sortitoutsi(ctx, cache, cancelado)
            for li, liga in enumerate(nombres_ligas):
                clubes = ligas[liga]
                base_frac = li / len(nombres_ligas)
                paso = 1 / len(nombres_ligas)
                avisar(base_frac, f"[{li + 1}/{len(nombres_ligas)}] {liga}: buscando la liga en sortitoutsi...")

                # 1) ¿en qué competición de sortitoutsi está esta liga? (votan jugadores de distintos clubes)
                votos = Counter()
                for idx in list(clubes)[:8]:
                    for nombre in elegir_sondas(clubes[idx], 1):
                        for r in soi.buscar(nombre):
                            if r["comp"] and norm(r["nombre"]) == norm(nombre):
                                votos[r["comp"]] += 1
                comps = [c for c, v in votos.most_common(3) if v >= 2]

                cm = []
                for comp in comps:
                    eqs = soi.equipos(comp)
                    for k, (tid, tnom) in enumerate(eqs, 1):
                        avisar(base_frac + paso * 0.8 * k / max(1, len(eqs)), f"[{li + 1}/{len(nombres_ligas)}] {liga}: {tnom}")
                        for fm, nom in soi.plantel(tid):
                            cm.append({"nombre": nom, "equipo": tnom, "url": fm, "fm": fm})
                pares, faltan, asig = emparejar(cm, clubes) if cm else ([], [], {})
                pes_ok = {pid for _, pid, _ in pares}

                # 2) clubes que no aparecieron en esa competición: buscarlos de a uno
                for idx, js in clubes.items():
                    resto = [(pid, n) for pid, n in js if pid not in pes_ok]
                    if len(resto) < max(3, len(js) // 2):
                        continue
                    votos_eq = Counter()
                    nom_eq = {}
                    for nombre in elegir_sondas(resto, 3):
                        for r in soi.buscar(nombre):
                            if r["equipo"] and norm(r["nombre"]) == norm(nombre):
                                votos_eq[r["equipo"]] += 1
                                nom_eq[r["equipo"]] = r["equipo_nombre"]
                    if not votos_eq:
                        continue
                    tid = votos_eq.most_common(1)[0][0]
                    cm2 = [{"nombre": nom, "equipo": nom_eq[tid], "url": fm, "fm": fm} for fm, nom in soi.plantel(tid)]
                    p2, _, _ = emparejar(cm2, {idx: resto})
                    pares += p2
                    pes_ok |= {pid for _, pid, _ in p2}

                for j, pid, n in pares:
                    if j["fm"] in usados_fm:
                        continue
                    usados_fm.add(j["fm"])
                    filas.append({"id_fm": j["fm"], "nombre_fm": j["nombre"], "equipo_fm": j["equipo"],
                                  "id_pes": pid, "nombre_pes": n, "liga_pes": liga,
                                  "revisar": "" if norm(j["nombre"]) == norm(n) else "revisar"})
                sin[liga] = [n for js in clubes.values() for pid, n in js if pid not in pes_ok]
                avisar(base_frac + paso, None,
                       f"{liga}: {len(pes_ok)} de {sum(len(js) for js in clubes.values())} con ID de FM")
                guardar_cache(cache)
                _escribir_base(carpeta, filas, sin, total_pes)
        finally:
            guardar_cache(cache)
            ctx.close()
    _escribir_base(carpeta, filas, sin, total_pes)
    avisar(1.0, "¡Base lista!")
    return dict(con_fm=len(filas), total=total_pes, ligas=len(nombres_ligas))


def _escribir_base(carpeta, filas, sin, total):
    import csv
    datos = {"mundo": carpeta, "fecha": time.strftime("%Y-%m-%d %H:%M"), "total_pes": total,
             "fm_a_pes": {f["id_fm"]: f["id_pes"] for f in filas}}
    with open(BASE_JSON, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    with open(BASE_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id_fm", "nombre_fm", "equipo_fm", "id_pes", "nombre_pes", "liga_pes", "revisar"],
                           delimiter=";")
        w.writeheader()
        for fila in sorted(filas, key=lambda x: (x["liga_pes"], x["equipo_fm"], x["nombre_fm"])):
            w.writerow(fila)
    with open(BASE_SIN, "w", encoding="utf-8") as f:
        f.write("Jugadores de tu mundo SIN ID de FM encontrado (no se les va a poder poner foto de FM):\n\n")
        for liga in sorted(sin, key=norm):
            if sin[liga]:
                f.write(f"{liga} ({len(sin[liga])}):\n")
                for n in sorted(sin[liga], key=norm):
                    f.write(f"   {n}\n")


BASE_FM = os.path.join(AQUI, "base_fm.json.gz")


def guardar_base_fm(fm, ruta):
    """lista del FM -> json comprimido (sirve para cualquier mundo)"""
    import gzip
    tmp = ruta + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=9) as f:
        json.dump({"formato": "base_fm", "version": 1, "fecha": time.strftime("%Y-%m-%d"),
                   "jugadores": [[u, n, o, c, ce, p] for u, n, o, c, ce, p in fm]},
                  f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, ruta)


def cargar_base_fm(ruta):
    import gzip
    with gzip.open(ruta, "rt", encoding="utf-8") as f:
        d = json.load(f)
    return [(u, n, o, c, ce, p) for u, n, o, c, ce, p in d["jugadores"]], d.get("fecha", "?")


def leer_players_csv(csv_path, avisar, cancelado):
    """players.csv de fmsave -> [(uid, nombre, otros_nombres, club, club_cedente, pais_del_club)]"""
    import csv

    avisar(0.02, "Leyendo la lista del Football Manager...")
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        muestra = f.read(4096)
        f.seek(0)
        sep = ";" if muestra.count(";") > muestra.count(",") else ","
        lector = csv.DictReader(f, delimiter=sep)
        campos = [c.strip().lower() for c in (lector.fieldnames or [])]
        if "unique_id" not in campos or "name" not in campos:
            raise RuntimeError("Ese CSV no tiene las columnas 'unique_id' y 'name'.\n"
                               "Tiene que ser el players.csv que baja fmsave (Download CSV > players.csv).")
        lector.fieldnames = campos

        def limpio(v):
            v = (v or "").strip()
            return v[1:] if v.startswith("'") else v   # fmsave 'desarma' celdas que empiezan con = + - @

        fm = []          # (uid, nombre, otros_nombres, club, club_cedente)
        for k, r in enumerate(lector):
            uid = limpio(r.get("unique_id"))
            if not uid or not uid.lstrip("-").isdigit():
                continue
            nombre = limpio(r.get("name"))
            otros = {limpio(r.get(c)) for c in ("full_name", "common_name", "legal_name")} - {"", nombre}
            fn, ln = limpio(r.get("first_name")), limpio(r.get("last_name"))
            if fn and ln:
                otros.add(f"{fn} {ln}")
            fm.append((uid, nombre, sorted(otros - {nombre}), limpio(r.get("club_name")),
                       limpio(r.get("loan_parent_club_name")), limpio(r.get("club_nation_id"))))
            if k % 50000 == 0 and cancelado():
                raise Cancelado()
    avisar(0.15, None, f"Lista del FM: {len(fm)} jugadores")
    return fm


def cruzar_fm(fm, ligas, avisar, cancelado, p0=0.15, p1=0.95):
    """cruza la lista del FM con las ligas del mundo (por nombre y club).
    -> (filas [{id_fm, nombre_fm, equipo_fm, id_pes, nombre_pes, liga_pes, revisar}], sin {liga: [nombres]}, total)"""
    from collections import Counter, defaultdict

    avisar(p0, "Preparando la lista del Football Manager...")

    por_nombre = defaultdict(list)     # nombre normalizado -> índices en fm
    por_club = defaultdict(list)       # club -> índices en fm
    pais_de = {}                       # uid -> país (id) del club en el FM
    for i, (uid, nombre, otros, club, cedente, pais) in enumerate(fm):
        if i % 100000 == 0 and cancelado():
            raise Cancelado()
        pais_de[uid] = pais
        for n in {nombre, *otros}:
            if n:
                por_nombre[norm(n)].append(i)
        if club:
            por_club[club].append(i)
        if cedente and cedente != club:
            por_club[cedente].append(i)

    total = sum(len(c) for v in ligas.values() for c in v.values())
    usados_fm, filas, sin = set(), [], {}
    nombres_ligas = sorted(ligas, key=norm)
    for li, liga in enumerate(nombres_ligas):
        if cancelado():
            raise Cancelado()
        avisar(p0 + (p1 - p0) * li / max(1, len(nombres_ligas)), f"Cruzando {liga}...")
        ok_liga = set()
        sueltos = []                   # jugadores que no aparecieron en su club del FM
        paises = Counter()             # países de los clubes del FM que sí coincidieron
        for idx, js in ligas[liga].items():
            # ¿qué club del FM es este club del PES? el que más nombres comparte
            votos = Counter()
            for _, n in js:
                for i in por_nombre.get(norm(n), []):
                    for c in (fm[i][3], fm[i][4]):
                        if c:
                            votos[c] += 1
            pendientes = list(js)
            for club_fm, v in votos.most_common(2):
                if v < 3 or not pendientes:
                    break
                for usar_otros in (False, True):
                    cm = []
                    for i in por_club[club_fm]:
                        uid, nombre, otros = fm[i][:3]
                        if uid in usados_fm:
                            continue
                        for n in (otros if usar_otros else [nombre]):
                            cm.append({"nombre": n, "equipo": club_fm, "url": uid, "fm": uid, "nombre_fm": nombre})
                    if not cm or not pendientes:
                        continue
                    cm_por_club = {idx: pendientes}
                    pares, _, _ = emparejar(cm, cm_por_club) if len(cm) >= 3 else ([], [], {})
                    if not pares and cm:
                        # emparejar pide 3 coincidencias para reconocer el club; acá ya lo sabemos
                        pares = [(j, c[0], c[1]) for j in cm for c in [next(((pid, n) for pid, n in pendientes
                                 if norm(n) == norm(j["nombre"])), None)] if c]
                    for j, pid, n in pares:
                        if j["fm"] in usados_fm or pid in ok_liga:
                            continue
                        usados_fm.add(j["fm"])
                        ok_liga.add(pid)
                        paises[pais_de.get(j["fm"], "")] += 1
                        filas.append({"id_fm": j["fm"], "nombre_fm": j["nombre_fm"], "equipo_fm": club_fm,
                                      "id_pes": pid, "nombre_pes": n, "liga_pes": liga,
                                      "revisar": "" if norm(j["nombre_fm"]) == norm(n) or norm(j["nombre"]) == norm(n)
                                      else "revisar"})
                    pendientes = [(pid, n) for pid, n in pendientes if pid not in ok_liga]
            sueltos += pendientes
        # los que faltan: nombre idéntico y único en todo el FM, y en un club del MISMO PAÍS que la liga
        # (cambió de club dentro del país). Si no, lo dejamos sin ID: es mejor sin cara que con una ajena.
        total_ok = sum(paises.values())
        paises_liga = {p for p, v in paises.items() if p and total_ok and v / total_ok >= 0.10}
        for pid, n in sueltos:
            cands = [i for i in por_nombre.get(norm(n), []) if fm[i][0] not in usados_fm]
            cands = list({fm[i][0]: i for i in cands}.values())
            if len(cands) == 1 and len(norm(n).split()) >= 2 and fm[cands[0]][5] in paises_liga:
                uid, nombre, _, club = fm[cands[0]][:4]
                usados_fm.add(uid)
                ok_liga.add(pid)
                filas.append({"id_fm": uid, "nombre_fm": nombre, "equipo_fm": club, "id_pes": pid,
                              "nombre_pes": n, "liga_pes": liga, "revisar": "otro club"})
        sin[liga] = [n for js in ligas[liga].values() for pid, n in js if pid not in ok_liga]
    return filas, sin, total


def base_desde_csv(csv_path, carpeta, avisar, cancelado):
    """arma la base FM -> PES con el players.csv que exporta fmsave (https://rhiever.github.io/fmsave/app/)
    a partir de una partida guardada del Football Manager. No usa internet y tarda segundos.
    De paso guarda base_fm.json.gz (la lista del FM sola, sirve para cualquier mundo: la usa el conversor)."""
    fm = leer_players_csv(csv_path, avisar, cancelado)
    guardar_base_fm(fm, BASE_FM)
    avisar(None, None, f"Base del FM para el conversor guardada: {os.path.basename(BASE_FM)}")
    filas, sin, total = cruzar_fm(fm, cargar_mundo(carpeta), avisar, cancelado)
    _escribir_base(carpeta, filas, sin, total)
    avisar(1.0, "¡Base lista!")
    return dict(con_fm=len(filas), total=total, ligas=len(sin))


def indexar_fotos(carpeta_fotos, quiero, avisar, cancelado, p=0.02):
    """recorre la carpeta (y subcarpetas) -> ({id_fm: ruta de la foto}, archivos revisados).
    quiero: los IDs de FM que interesan (set/dict de strings)."""
    avisar(p, "Buscando fotos en la carpeta...")
    fotos = {}   # fm -> ruta
    exts = (".png", ".jpg", ".jpeg", ".webp")
    vistos = 0
    pila = [(carpeta_fotos, 0)]
    while pila:
        d, prof = pila.pop()
        try:
            it = os.scandir(d)
        except OSError:
            continue
        with it:
            for e in it:
                if e.is_dir(follow_symlinks=False):
                    if prof < 4 and "icon" not in e.name.lower():   # iconfaces = íconos chiquitos, no sirven
                        pila.append((e.path, prof + 1))
                    continue
                vistos += 1
                if vistos % 20000 == 0:
                    if cancelado():
                        raise Cancelado()
                    avisar(p, f"Buscando fotos en la carpeta... ({vistos} archivos revisados)")
                nom = e.name.lower()
                if not nom.endswith(exts) or nom.startswith("icon"):
                    continue
                m = re.match(r"(?:face_|r-)?(\d+)\b", nom)      # face_123.png, 123.png, 123 (1).png
                fm = m.group(1) if m else None
                if fm not in quiero:
                    otros = re.findall(r"\d{5,}", nom)
                    fm = otros[-1] if otros else None
                if fm in quiero and (fm not in fotos or nom.startswith("face_")):
                    fotos[fm] = e.path
    return fotos, vistos


def convertir_carpeta(carpeta_fotos, carpeta_mundo, cfg, avisar, cancelado, ligas_sel=None):
    """fotos con el ID de FM en el nombre (face_123.png, 123.png...) -> <ID PES>.dds,
    en una carpeta por liga. ligas_sel: lista de ligas a hacer (None = todas)."""
    base = cargar_base()
    if not base:
        raise RuntimeError("Primero armá la base FM -> PES.")
    liga_de = {pid: liga for liga, clubes in cargar_mundo(carpeta_mundo).items()
               for js in clubes.values() for pid, _ in js}
    sel = set(ligas_sel) if ligas_sel else None
    mapa = {fm: int(pid) for fm, pid in base["fm_a_pes"].items()
            if int(pid) in liga_de and (sel is None or liga_de[int(pid)] in sel)}
    if not mapa:
        raise RuntimeError("La base no tiene jugadores de esa liga.")
    fotos, vistos = indexar_fotos(carpeta_fotos, mapa, avisar, cancelado)
    avisar(0.10, None, f"Archivos revisados: {vistos}  |  fotos de jugadores de tu mundo: {len(fotos)}")

    from PIL import Image
    from collections import Counter
    t = int(cfg["tamano"])
    ok, vacias, ids = 0, 0, []
    por_liga = Counter()
    for k, (fm, ruta) in enumerate(fotos.items(), 1):
        if k % 50 == 0 and cancelado():
            raise Cancelado()
        try:
            img = Image.open(ruta).convert("RGBA")
        except Exception:
            img = None
        if img is None or img.width < 40 or img.getbbox() is None:
            vacias += 1
            continue
        pid = mapa[fm]
        liga = liga_de[pid]
        d = destino_liga(liga)
        os.makedirs(d, exist_ok=True)
        img.resize((t, t), Image.LANCZOS).save(os.path.join(d, f"{pid}.dds"), pixel_format=cfg["formato_dds"])
        ok += 1
        ids.append(pid)
        por_liga[liga] += 1
        avisar(0.10 + 0.88 * k / max(1, len(fotos)), f"Convirtiendo: {k} de {len(fotos)}")
    movidos = actualizar_world_txt(carpeta_mundo, ids)
    with open(MARCA_MUNDO, "w", encoding="utf-8") as f:
        f.write(carpeta_mundo)
    for liga in por_liga:
        escribir_leeme(liga, carpeta_mundo)
    for liga, n in sorted(por_liga.items(), key=lambda x: norm(x[0])):
        avisar(None, None, f"  {liga}: {n} minifaces")
    avisar(1.0, "¡Listo!")
    return dict(ok=ok, vacias=vacias, encontradas=len(fotos), en_base=len(mapa), movidos=movidos,
                ligas=len(por_liga), carpeta=carpeta_liga(next(iter(por_liga))) if len(por_liga) == 1 else SALIDA)


# ------------------------------------------------------------------ fotos de los DT
PACKS = os.path.join(AQUI, "Packs para compartir")
PACK_FORMATO = "minifaces_fm"


def imagen_a_dds(ruta, cfg):
    """foto -> bytes de un DDS de la miniface, o None si la foto no sirve (vacía, chiquita, rota)"""
    from PIL import Image
    try:
        img = Image.open(ruta).convert("RGBA")
    except Exception:
        return None
    if img.width < 40 or img.getbbox() is None:
        return None
    t = int(cfg["tamano"])
    buf = BytesIO()
    img.resize((t, t), Image.LANCZOS).save(buf, format="DDS", pixel_format=cfg["formato_dds"])
    return buf.getvalue()


def armar_packs(carpeta_fotos, carpeta_mundo, cfg, avisar, cancelado, ligas_sel=None):
    """un .zip por liga con las minifaces nombradas con el ID del FOOTBALL MANAGER (<id_fm>.dds).
    No dependen de ningún mundo: el conversor las pasa a los IDs del PES de cada uno.
    Cada pack trae el plantel completo de los clubes del FM que juegan esa liga en tu mundo."""
    import zipfile
    from collections import defaultdict
    if not os.path.exists(BASE_FM):
        raise RuntimeError("Falta base_fm.json.gz: importá de nuevo el players.csv (Paso 1, botón A).")
    avisar(0.01, "Cargando la lista del FM...")
    fm, fecha = cargar_base_fm(BASE_FM)
    ligas = cargar_mundo(carpeta_mundo)
    sel = [l for l in (ligas_sel or sorted(ligas, key=norm)) if l in ligas]
    filas, _, _ = cruzar_fm(fm, {l: ligas[l] for l in sel}, avisar, cancelado, 0.03, 0.25)

    ids_liga, clubes = defaultdict(set), defaultdict(set)
    for f in filas:
        ids_liga[f["liga_pes"]].add(f["id_fm"])
        if f["revisar"] != "otro club":
            clubes[f["liga_pes"]].add(f["equipo_fm"])
    ligas_de_club = defaultdict(set)
    for liga, cs in clubes.items():
        for c in cs:
            ligas_de_club[c].add(liga)
    for uid, _, _, club, cedente, _ in fm:          # el plantel entero de esos clubes en el FM
        for c in {club, cedente}:
            for liga in ligas_de_club.get(c, ()):
                ids_liga[liga].add(uid)
    quiero = set().union(*ids_liga.values()) if ids_liga else set()
    if not quiero:
        raise RuntimeError("No reconocí ningún club de esa liga en la lista del FM.")
    fotos, vistos = indexar_fotos(carpeta_fotos, quiero, avisar, cancelado, 0.27)
    avisar(0.35, None, f"Archivos revisados: {vistos}  |  fotos para los packs: {len(fotos)}")

    os.makedirs(PACKS, exist_ok=True)
    hechos, total_fotos, vacias = [], 0, 0
    trabajo_total = sum(len(ids_liga[l] & fotos.keys()) for l in sel) or 1
    hecho = 0
    for liga in sel:
        ids = sorted(ids_liga.get(liga, set()) & fotos.keys(), key=int)
        if not ids:
            avisar(None, None, f"  {liga}: sin fotos, no hago pack")
            continue
        nombre = f"Minifaces FM - {nombre_archivo(liga)}.zip"
        ruta = os.path.join(PACKS, nombre)
        tmp = ruta + ".tmp"
        n = 0
        cortar = False
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for uid in ids:
                hecho += 1
                if hecho % 50 == 0:
                    if cancelado():
                        cortar = True
                        break
                    avisar(0.35 + 0.64 * hecho / trabajo_total, f"{liga}: {n} minifaces")
                datos = imagen_a_dds(fotos[uid], cfg)
                if datos is None:
                    vacias += 1
                    continue
                z.writestr(f"{uid}.dds", datos)
                n += 1
            z.writestr("pack.json", json.dumps({
                "formato": PACK_FORMATO, "version": 1, "liga": liga, "jugadores": n,
                "tamano": int(cfg["tamano"]), "fecha": time.strftime("%Y-%m-%d"), "base_fm": fecha},
                ensure_ascii=False, indent=1))
            z.writestr("LEEME - README.txt", (
                f"[ES] Minifaces de {liga} ({n} jugadores) con el ID del Football Manager.\n"
                "No se pegan así nomás en el juego: abrí el 'Conversor de minifaces', elegí tu juego,\n"
                "agregá este .zip (sin descomprimir) y tocá Convertir e Instalar.\n\n"
                f"[PT] Minifaces de {liga} ({n} jogadores) com o ID do Football Manager.\n"
                "Não é só colar no jogo: abra o 'Conversor de minifaces', escolha seu jogo,\n"
                "adicione este .zip (sem descompactar) e clique em Converter e Instalar.\n\n"
                f"[EN] {liga} minifaces ({n} players) named with Football Manager IDs.\n"
                "Don't copy them straight into the game: open the 'Miniface Converter', choose your game,\n"
                "add this .zip (no need to unzip) and click Convert and Install.\n"))
        if cortar:
            os.remove(tmp)
            raise Cancelado()
        if n:
            os.replace(tmp, ruta)
            hechos.append((liga, n))
            total_fotos += n
            avisar(None, None, f"  {liga}: {n} minifaces -> {nombre}")
        else:
            os.remove(tmp)
    avisar(1.0, "¡Packs listos!")
    return dict(packs=len(hechos), fotos=total_fotos, vacias=vacias, carpeta=PACKS)


CARPETA_DT = "Minifaces DT"


def _wesys(d):
    """tablas de la base del PES (Team.bin, Coach.bin): 'WESYS' + zlib"""
    import struct
    import zlib
    if d[3:8] != b"WESYS":
        return d
    csz, usz = struct.unpack("<II", d[8:16])
    return zlib.decompress(d[16:16 + csz])


def dt_del_mundo(carpeta_mundo):
    """{clave del club ("Liga/n"): (id del equipo, id del DT, nombre del DT en el juego)} de los clubes
    NUEVOS del mundo (los clubes que ya trae el juego tienen sus propios DT con foto)"""
    with open(os.path.join(carpeta_mundo, "leaguebuilder-plan.json"), encoding="utf-8") as f:
        txt = f.read()
    i = txt.find('"leagues"')
    ligas, _ = json.JSONDecoder().raw_decode(txt, txt.index("[", i))   # solo la parte de las ligas
    del txt
    pesdb = os.path.join(carpeta_mundo, "common", "etc", "pesdb")
    with open(os.path.join(pesdb, "Team.bin"), "rb") as f:
        team = _wesys(f.read())
    dt_de = {int.from_bytes(team[o + 8:o + 12], "little"): int.from_bytes(team[o:o + 4], "little")
             for o in range(0, len(team) - 1531, 1532)}
    nombres = {}
    try:
        with open(os.path.join(pesdb, "Coach.bin"), "rb") as f:
            co = _wesys(f.read())
        for o in range(0, len(co) - 99, 100):
            nombres[int.from_bytes(co[o:o + 4], "little")] = co[o + 8:o + 54].split(b"\0")[0].decode("utf-8", "replace")
    except OSError:
        pass
    out = {}
    for liga in ligas:
        for k, tid in enumerate(liga.get("teams") or []):
            cid = dt_de.get(tid)
            if cid is not None:
                out[f"{liga['name']}/{k}"] = (tid, cid, nombres.get(cid, ""))
    return out


def fotos_dt(staff_csv, carpeta_fotos, carpeta_mundo, avisar, cancelado):
    """foto del DT real (según el FM) de cada club nuevo del mundo -> coach_<id del DT>.png (256x256)"""
    import csv
    from collections import Counter, defaultdict
    from PIL import Image

    avisar(0.02, "Leyendo los DT de tu mundo...")
    dts = dt_del_mundo(carpeta_mundo)
    avisar(None, None, f"Clubes nuevos del mundo con DT: {len(dts)}")

    # club del mundo -> club del FM: el club del FM donde están la mayoría de sus jugadores (según la base)
    import csv as _csv
    with open(os.path.join(carpeta_mundo, "fl26playerids.json"), encoding="utf-8") as f:
        clubs = (json.load(f).get("clubs") or {})
    equipo_fm = {}
    with open(BASE_CSV, encoding="utf-8-sig", newline="") as f:
        for r in _csv.DictReader(f, delimiter=";"):
            if r.get("revisar") != "otro club":
                equipo_fm[str(r["id_pes"])] = r["equipo_fm"]
    club_fm = {}
    for clave, ids in clubs.items():
        if clave in dts:
            v = Counter(equipo_fm[str(p)] for p in ids.values() if str(p) in equipo_fm)
            if v and v.most_common(1)[0][1] >= 3:
                club_fm[clave] = v.most_common(1)[0][0]
    avisar(0.10, None, f"Clubes reconocidos en el FM: {len(club_fm)}")

    # DT (manager del primer equipo) de cada club del FM
    avisar(0.12, "Leyendo el cuerpo técnico del FM...")
    managers = defaultdict(list)
    with open(staff_csv, encoding="utf-8-sig", newline="") as f:
        muestra = f.read(4096)
        f.seek(0)
        lector = csv.DictReader(f, delimiter=";" if muestra.count(";") > muestra.count(",") else ",")
        lector.fieldnames = [c.strip().lower() for c in (lector.fieldnames or [])]
        if "job_code" not in lector.fieldnames and "job" not in lector.fieldnames:
            raise RuntimeError("Ese CSV no tiene la columna 'job'. Tiene que ser el staff.csv que exporta fmsave.")
        for r in lector:
            cod = (r.get("job_code") or "").strip()
            lab = (r.get("job") or "").strip().lower()
            if cod == "16" or (lab in ("manager", "mánager", "entrenador")):
                uid = (r.get("unique_id") or "").strip()
                if uid.isdigit():
                    slot = (r.get("team_slot") or "").strip()
                    managers[(r.get("club_name") or "").strip()].append(
                        (int(slot) if slot.lstrip("-").isdigit() else 99, uid, (r.get("name") or "").strip()))
    elegido = {c: sorted(v)[0] for c, v in managers.items()}     # el de team_slot más bajo = primer equipo

    pedidos = {}   # uid FM -> [(id DT, club)]
    for clave, club in club_fm.items():
        if club in elegido:
            pedidos.setdefault(elegido[club][1], []).append((dts[clave][1], clave, club, elegido[club][2]))

    # buscar las fotos en la carpeta (megapack)
    avisar(0.20, "Buscando las fotos de los DT...")
    rutas = {}
    pila = [(carpeta_fotos, 0)]
    vistos = 0
    while pila:
        d, prof = pila.pop()
        try:
            it = os.scandir(d)
        except OSError:
            continue
        with it:
            for e in it:
                if e.is_dir(follow_symlinks=False):
                    if prof < 4 and "icon" not in e.name.lower():
                        pila.append((e.path, prof + 1))
                    continue
                vistos += 1
                if vistos % 20000 == 0:
                    if cancelado():
                        raise Cancelado()
                    avisar(0.25, f"Buscando las fotos de los DT... ({vistos} archivos)")
                m = re.match(r"(?:face_)?(\d+)\b", e.name.lower())
                if m and m.group(1) in pedidos and e.name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    rutas[m.group(1)] = e.path

    destino = os.path.join(SALIDA, CARPETA_DT, "common", "render", "symbol", "coach")
    os.makedirs(destino, exist_ok=True)
    hechos, sin_foto = [], []
    for k, (uid, lista) in enumerate(pedidos.items(), 1):
        img = None
        if uid in rutas:
            try:
                img = Image.open(rutas[uid]).convert("RGBA")
            except Exception:
                img = None
        if img is None or img.width < 40 or img.getbbox() is None:
            sin_foto += lista
            continue
        img.thumbnail((256, 256), Image.LANCZOS)
        lienzo = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        lienzo.paste(img, ((256 - img.width) // 2, (256 - img.height) // 2), img)
        for cid, clave, club, nombre in lista:
            lienzo.save(os.path.join(destino, f"coach_{cid}.png"))
            hechos.append((cid, clave, club, nombre))
        avisar(0.30 + 0.68 * k / max(1, len(pedidos)), f"Fotos de DT: {k} de {len(pedidos)}")

    with open(os.path.join(SALIDA, CARPETA_DT, "LEEME.txt"), "w", encoding="utf-8") as f:
        f.write(f"Fotos de los DT de los clubes nuevos ({len(hechos)}).\n"
                "Son las fotos de los técnicos REALES (según el Football Manager); en el juego el DT\n"
                "conserva el nombre que le puso el mundo.\n\n"
                f"1) Copiá la carpeta '{CARPETA_DT}' a ...\\SiderAddons\\livecpk\\\n"
                f"2) En sider.ini, arriba de todo: cpk.root = \".\\livecpk\\{CARPETA_DT}\"\n\n")
        for cid, clave, club, nombre in sorted(hechos, key=lambda x: x[1]):
            f.write(f"  coach_{cid}.png  <- {nombre}  ({club})  [{clave}]\n")
        f.write("\nSin foto en la carpeta:\n")
        for cid, clave, club, nombre in sorted(sin_foto, key=lambda x: x[1]):
            f.write(f"  {nombre}  ({club})  [{clave}]\n")
    avisar(1.0, "¡Listo!")
    return dict(ok=len(hechos), sin_foto=len(sin_foto), clubes=len(dts), reconocidos=len(club_fm),
                con_dt=len(pedidos), carpeta=os.path.join(SALIDA, CARPETA_DT))


# ------------------------------------------------------------------ juntar todas las ligas
TODAS_JUNTAS = "Minifaces TODAS LAS LIGAS"


def juntar_todas(avisar, cancelado):
    """copia los DDS de todas las carpetas de liga a una sola carpeta de contenido"""
    destino = os.path.join(SALIDA, TODAS_JUNTAS, "common", "render", "symbol", "player")
    if not os.path.isdir(SALIDA):
        raise RuntimeError("Todavía no hay minifaces hechas.")
    archivos = []
    for e in os.scandir(SALIDA):
        if e.is_dir() and e.name.startswith("Minifaces ") and e.name not in (TODAS_JUNTAS, CARPETA_DT):
            d = os.path.join(e.path, "common", "render", "symbol", "player")
            if os.path.isdir(d):
                archivos += [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(".dds")]
    if not archivos:
        raise RuntimeError("No encontré minifaces en 'Minifaces por liga'.")
    os.makedirs(destino, exist_ok=True)
    for k, f in enumerate(archivos, 1):
        if k % 200 == 0:
            if cancelado():
                raise Cancelado()
            avisar(k / len(archivos), f"Copiando: {k} de {len(archivos)}")
        shutil.copy2(f, destino)
    ids = sorted(int(os.path.basename(f)[:-4]) for f in archivos if os.path.basename(f)[:-4].isdigit())
    with open(os.path.join(SALIDA, TODAS_JUNTAS, "LEEME.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"Todas las minifaces juntas ({len(ids)} jugadores).\n\n"
                 f"1) Copiá la carpeta '{TODAS_JUNTAS}' a ...\\SiderAddons\\livecpk\\\n"
                 f"2) En sider.ini, arriba de todo: cpk.root = \".\\livecpk\\{TODAS_JUNTAS}\"\n"
                 "3) En SiderAddons\\modules\\fl26world.txt estos IDs tienen que estar en 'newfaces3d'\n"
                 "   (o usá el fl26world.txt que deja el bot en 'Minifaces por liga'):\n\n"
                 "newfaces3d " + " ".join(_rangos(ids)) + "\n")
    avisar(1.0, "¡Listo!")
    return dict(n=len(archivos), carpeta=os.path.join(SALIDA, TODAS_JUNTAS))


# ------------------------------------------------------------------ tema oscuro
COLORES = {
    "fondo": "#121418", "header": "#0d0f12", "card": "#1b1e24", "campo": "#23272f", "borde": "#2f3540",
    "texto": "#e7e9ee", "texto2": "#c3c8d2", "muted": "#8a93a3", "acento": "#3b82f6", "acento2": "#2563eb",
    "verde": "#22c55e", "boton": "#2a2f39", "boton2": "#343a46",
}


def aplicar_tema(root):
    from tkinter import ttk
    C = COLORES
    root.configure(bg=C["fondo"])
    st = ttk.Style(root)
    st.theme_use("clam")
    fuente = ("Segoe UI", 10)
    st.configure(".", background=C["fondo"], foreground=C["texto"], fieldbackground=C["campo"],
                 bordercolor=C["borde"], lightcolor=C["borde"], darkcolor=C["borde"], troughcolor=C["campo"],
                 focuscolor=C["acento"], selectbackground=C["acento"], selectforeground="#ffffff", font=fuente)
    st.configure("TFrame", background=C["fondo"])
    st.configure("Header.TFrame", background=C["header"])
    st.configure("Card.TFrame", background=C["card"])
    st.configure("TLabel", background=C["fondo"], foreground=C["texto"])
    st.configure("Title.TLabel", background=C["header"], foreground="#ffffff", font=("Segoe UI Semibold", 17))
    st.configure("HeaderSub.TLabel", background=C["header"], foreground=C["muted"], font=("Segoe UI", 9))
    st.configure("Muted.TLabel", background=C["fondo"], foreground=C["muted"])
    st.configure("Card.TLabel", background=C["card"], foreground=C["texto"])
    st.configure("CardMuted.TLabel", background=C["card"], foreground=C["muted"])
    st.configure("CardGood.TLabel", background=C["card"], foreground=C["verde"])
    st.configure("Caption.TLabel", background=C["card"], foreground=C["muted"], font=("Segoe UI Semibold", 8))
    st.configure("TButton", background=C["boton"], foreground=C["texto"], borderwidth=0, padding=(12, 6),
                 focusthickness=0)
    st.map("TButton", background=[("disabled", C["card"]), ("pressed", C["boton2"]), ("active", C["boton2"])],
           foreground=[("disabled", C["muted"])])
    st.configure("Accent.TButton", background=C["acento"], foreground="#ffffff", font=("Segoe UI Semibold", 10))
    st.map("Accent.TButton", background=[("disabled", C["boton"]), ("pressed", C["acento2"]), ("active", C["acento2"])],
           foreground=[("disabled", C["muted"])])
    st.configure("TRadiobutton", background=C["card"], foreground=C["texto"], indicatorcolor=C["campo"])
    st.map("TRadiobutton", background=[("active", C["card"])], indicatorcolor=[("selected", C["acento"])])
    st.configure("TEntry", fieldbackground=C["campo"], foreground=C["texto"], insertcolor=C["texto"], padding=4)
    st.configure("TCombobox", fieldbackground=C["campo"], background=C["boton"], foreground=C["texto"],
                 arrowcolor=C["texto"], padding=4)
    st.map("TCombobox", fieldbackground=[("readonly", C["campo"])], foreground=[("readonly", C["texto"])],
           selectbackground=[("readonly", C["campo"])], selectforeground=[("readonly", C["texto"])])
    root.option_add("*TCombobox*Listbox.background", C["campo"])
    root.option_add("*TCombobox*Listbox.foreground", C["texto"])
    root.option_add("*TCombobox*Listbox.selectBackground", C["acento"])
    root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
    root.option_add("*TCombobox*Listbox.font", fuente)
    st.configure("TNotebook", background=C["fondo"], borderwidth=0, tabmargins=(0, 4, 0, 0),
                 bordercolor=C["fondo"], lightcolor=C["fondo"], darkcolor=C["fondo"])
    st.configure("TNotebook.Tab", background=C["card"], foreground=C["muted"], padding=(18, 8), borderwidth=0,
                 bordercolor=C["fondo"], lightcolor=C["card"], darkcolor=C["card"])
    st.map("TNotebook.Tab", background=[("selected", C["acento"]), ("active", C["boton2"])],
           foreground=[("selected", "#ffffff"), ("active", C["texto"])],
           lightcolor=[("selected", C["acento"])], darkcolor=[("selected", C["acento"])])
    st.configure("Vertical.TScrollbar", background=C["boton"], troughcolor=C["campo"], arrowcolor=C["texto"],
                 borderwidth=0)
    st.configure("Green.Horizontal.TProgressbar", background=C["verde"], troughcolor=C["campo"], borderwidth=0,
                 thickness=10)


def barra_oscura(root):
    """barra de título oscura en Windows 10/11"""
    try:
        import ctypes
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        valor = ctypes.c_int(1)
        for attr in (20, 19):   # DWMWA_USE_IMMERSIVE_DARK_MODE (nuevo / viejo)
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(valor), ctypes.sizeof(valor)) == 0:
                break
    except Exception:
        pass


# ------------------------------------------------------------------ ventana
def abrir(path):
    try:
        os.startfile(path)  # Windows
    except Exception:
        pass


class App:
    def __init__(self):
        import tkinter as tk
        from tkinter import ttk
        self.cfg = cargar_config()
        if not es_mundo(self.cfg.get("carpeta_mundo")):
            self.cfg["carpeta_mundo"] = buscar_mundo_por_defecto()
        self.ligas = {}
        self.visibles = []
        self.q = queue.Queue()
        self.hilo = None
        self.cancelar = threading.Event()

        r = self.root = tk.Tk()
        r.protocol("WM_DELETE_WINDOW", self.cerrar)
        r.title("Bot de minifaces  -  FL26 / PES")
        try:
            r.iconbitmap(os.path.join(getattr(sys, "_MEIPASS", AQUI), "icono.ico"))
        except Exception:
            pass
        r.geometry("760x820")
        r.minsize(620, 640)
        aplicar_tema(r)
        C = COLORES
        pad = dict(padx=14, pady=5)

        # encabezado
        h = ttk.Frame(r, style="Header.TFrame")
        h.pack(fill="x")
        ttk.Label(h, text="Bot de minifaces", style="Title.TLabel").pack(side="left", padx=(16, 8), pady=(12, 10))
        ttk.Label(h, text="FL26 / PES  ·  cmtracker  ·  sortitoutsi  ·  Football Manager",
                  style="HeaderSub.TLabel").pack(side="left", pady=(18, 10))

        # mundo
        f = ttk.Frame(r, style="Card.TFrame")
        f.pack(fill="x", padx=14, pady=(12, 6))
        ttk.Label(f, text="MUNDO", style="Caption.TLabel").pack(anchor="w", padx=12, pady=(10, 0))
        fm_ = ttk.Frame(f, style="Card.TFrame")
        fm_.pack(fill="x", padx=12, pady=(2, 10))
        self.v_mundo = tk.StringVar()
        ttk.Label(fm_, textvariable=self.v_mundo, style="Card.TLabel", wraplength=560).pack(
            side="left", fill="x", expand=True)
        ttk.Button(fm_, text="Cambiar...", command=self.elegir_mundo).pack(side="right")

        nb = ttk.Notebook(r)
        nb.pack(fill="both", expand=True, padx=14, pady=6)
        t1 = ttk.Frame(nb)
        t2 = ttk.Frame(nb)
        nb.add(t2, text="  Base FM → PES  ")
        nb.add(t1, text="  Bajar por liga  ")

        # ---------- pestaña: bajar por liga
        f = ttk.Frame(t1, style="Card.TFrame")
        f.pack(fill="x", **pad)
        ttk.Label(f, text="DE DÓNDE SALEN LAS CARAS", style="Caption.TLabel").pack(anchor="w", padx=12, pady=(10, 2))
        self.v_fuente = tk.StringVar(value=self.cfg.get("fuente", "cmtracker"))
        fr = ttk.Frame(f, style="Card.TFrame")
        fr.pack(fill="x", padx=12, pady=(2, 6))
        ttk.Radiobutton(fr, text="cmtracker (caras del FC)", value="cmtracker", variable=self.v_fuente,
                        command=self.cambiar_fuente).pack(side="left")
        ttk.Radiobutton(fr, text="sortitoutsi (fotos recortadas del FM)", value="sortitoutsi",
                        variable=self.v_fuente, command=self.cambiar_fuente).pack(side="left", padx=18)
        self.f_mega = ttk.Frame(f, style="Card.TFrame")
        self.v_mega = tk.StringVar()
        ttk.Label(self.f_mega, text="Megapack:", style="Card.TLabel").pack(side="left")
        ttk.Label(self.f_mega, textvariable=self.v_mega, wraplength=380, style="CardMuted.TLabel").pack(
            side="left", fill="x", expand=True, padx=6)
        ttk.Button(self.f_mega, text="Quitar", command=lambda: self.poner_megapack("")).pack(side="right")
        ttk.Button(self.f_mega, text="Elegir...", command=self.elegir_megapack).pack(side="right", padx=4)

        f = ttk.Frame(t1, style="Card.TFrame")
        f.pack(fill="both", expand=True, **pad)
        ttk.Label(f, text="LIGA  ·  doble clic para bajar", style="Caption.TLabel").pack(anchor="w", padx=12, pady=(10, 2))
        fb = ttk.Frame(f, style="Card.TFrame")
        fb.pack(fill="x", padx=12, pady=(2, 4))
        ttk.Label(fb, text="Buscar:", style="Card.TLabel").pack(side="left")
        self.v_buscar = tk.StringVar()
        self.v_buscar.trace_add("write", lambda *a: self.llenar_lista())
        ttk.Entry(fb, textvariable=self.v_buscar).pack(side="left", fill="x", expand=True, padx=6)
        fl = ttk.Frame(f, style="Card.TFrame")
        fl.pack(fill="both", expand=True, padx=12, pady=(2, 4))
        self.lista = tk.Listbox(fl, activestyle="none", font=("Segoe UI", 10), exportselection=False,
                                bg=C["campo"], fg=C["texto"], selectbackground=C["acento"],
                                selectforeground="#ffffff", highlightthickness=1, highlightbackground=C["borde"],
                                highlightcolor=C["acento"], relief="flat", bd=0)
        sb = ttk.Scrollbar(fl, orient="vertical", command=self.lista.yview)
        self.lista.config(yscrollcommand=sb.set)
        self.lista.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.lista.bind("<Double-Button-1>", lambda e: self.empezar())
        self.lista.bind("<<ListboxSelect>>", lambda e: self.mostrar_info())
        self.v_info = tk.StringVar(value="Elegí una liga de la lista.  (✓ = ya sé su número en la fuente elegida)")
        ttk.Label(f, textvariable=self.v_info, style="CardMuted.TLabel").pack(fill="x", padx=12, pady=(2, 8))
        fb = ttk.Frame(t1)
        fb.pack(fill="x", **pad)
        self.b_empezar = ttk.Button(fb, text="Bajar minifaces", style="Accent.TButton", command=self.empezar)
        self.b_empezar.pack(side="left")

        # ---------- pestaña: base FM -> PES
        f = ttk.Frame(t2, style="Card.TFrame")
        f.pack(fill="x", **pad)
        ttk.Label(f, text="PASO 1  ·  ARMAR LA BASE (ID de FM → ID de tu PES)", style="Caption.TLabel").pack(
            anchor="w", padx=12, pady=(10, 2))
        ttk.Label(f, style="Card.TLabel", wraplength=640, justify="left", text=(
            "A) Rápido (segundos): con el players.csv que baja fmsave de una partida guardada del FM.\n"
            "B) Sin el FM (tarda una hora): recorre las ligas en sortitoutsi.")).pack(fill="x", padx=12, pady=2)
        fb2 = ttk.Frame(f, style="Card.TFrame")
        fb2.pack(fill="x", padx=12, pady=(6, 4))
        self.b_csv = ttk.Button(fb2, text="A)  Importar lista del FM...", style="Accent.TButton",
                                command=self.click_importar_csv)
        self.b_csv.pack(side="left")
        self.b_base = ttk.Button(fb2, text="B)  Armar desde sortitoutsi", command=self.click_armar_base)
        self.b_base.pack(side="left", padx=8)
        ttk.Button(fb2, text="Abrir tabla (Excel)", command=lambda: abrir(BASE_CSV)).pack(side="right")
        self.v_base = tk.StringVar()
        ttk.Label(f, textvariable=self.v_base, style="CardGood.TLabel", wraplength=640, justify="left").pack(
            fill="x", padx=12, pady=(4, 10))

        f = ttk.Frame(t2, style="Card.TFrame")
        f.pack(fill="x", **pad)
        ttk.Label(f, text="PASO 2  ·  CONVERTIR FOTOS A MINIFACES", style="Caption.TLabel").pack(
            anchor="w", padx=12, pady=(10, 2))
        ttk.Label(f, style="Card.TLabel", wraplength=640, justify="left", text=(
            "Elegí la liga y después la carpeta con fotos que tengan el ID de FM en el nombre "
            "(face_91140089.png...), por ejemplo el megapack. Quedan en DDS con el ID del PES, una carpeta "
            "por liga dentro de 'Minifaces por liga'. El bot no toca el juego.")).pack(fill="x", padx=12, pady=2)
        fl2 = ttk.Frame(f, style="Card.TFrame")
        fl2.pack(fill="x", padx=12, pady=(8, 4))
        ttk.Label(fl2, text="Liga:", style="Card.TLabel").pack(side="left")
        self.v_liga_conv = tk.StringVar(value=TODAS_LIGAS)
        self.cb_liga = ttk.Combobox(fl2, textvariable=self.v_liga_conv, state="readonly", height=25)
        self.cb_liga.pack(side="left", fill="x", expand=True, padx=8)
        fb3 = ttk.Frame(f, style="Card.TFrame")
        fb3.pack(fill="x", padx=12, pady=(4, 12))
        self.b_conv = ttk.Button(fb3, text="Convertir carpeta de fotos...", style="Accent.TButton",
                                 command=self.click_convertir)
        self.b_conv.pack(side="left")

        f = ttk.Frame(t2, style="Card.TFrame")
        f.pack(fill="x", **pad)
        ttk.Label(f, text="PACKS PARA COMPARTIR  ·  con ID de FM, sirven para cualquier mundo",
                  style="Caption.TLabel").pack(anchor="w", padx=12, pady=(10, 2))
        ttk.Label(f, style="Card.TLabel", wraplength=640, justify="left", text=(
            "Hace un .zip por liga (la elegida en el Paso 2, o todas) con las minifaces nombradas con el ID "
            "del FM. La gente los convierte a su mundo con el 'Conversor de minifaces'.")).pack(
            fill="x", padx=12, pady=2)
        fb6 = ttk.Frame(f, style="Card.TFrame")
        fb6.pack(fill="x", padx=12, pady=(6, 12))
        self.b_packs = ttk.Button(fb6, text="Armar packs...", command=self.click_packs)
        self.b_packs.pack(side="left")
        ttk.Button(fb6, text="Abrir carpeta de packs",
                   command=lambda: (os.makedirs(PACKS, exist_ok=True), abrir(PACKS))).pack(side="left", padx=8)

        f = ttk.Frame(t2, style="Card.TFrame")
        f.pack(fill="x", **pad)
        ttk.Label(f, text="PASO 3 (OPCIONAL)  ·  FOTOS DE LOS DT", style="Caption.TLabel").pack(
            anchor="w", padx=12, pady=(10, 2))
        ttk.Label(f, style="Card.TLabel", wraplength=640, justify="left", text=(
            "Pone la foto del DT real (según el FM) a los clubes nuevos del mundo. Necesita el staff.csv "
            "(usá 'Exportar DT del FM.bat') y la carpeta del megapack.")).pack(fill="x", padx=12, pady=2)
        fb4 = ttk.Frame(f, style="Card.TFrame")
        fb4.pack(fill="x", padx=12, pady=(6, 12))
        self.b_dt = ttk.Button(fb4, text="Hacer fotos de los DT...", command=self.click_dt)
        self.b_dt.pack(side="left")

        f = ttk.Frame(t2, style="Card.TFrame")
        f.pack(fill="x", **pad)
        ttk.Label(f, text="EN EL JUEGO  ·  ACTIVAR MINIFACES (sirve para cualquier pack, no solo los del bot)",
                  style="Caption.TLabel").pack(anchor="w", padx=12, pady=(10, 2))
        ttk.Label(f, style="Card.TLabel", wraplength=640, justify="left", text=(
            "Con un mundo de FL Mod Studio las minifaces no se ven aunque estén instaladas. Este botón revisa "
            "todas las minifaces activas en el juego y arregla el fl26world.txt para que se vean. Usalo después "
            "de instalar minifaces nuevas o de reinstalar el mundo.")).pack(fill="x", padx=12, pady=2)
        fb5 = ttk.Frame(f, style="Card.TFrame")
        fb5.pack(fill="x", padx=12, pady=(6, 12))
        self.b_activar = ttk.Button(fb5, text="Activar minifaces en el juego...", command=self.click_activar)
        self.b_activar.pack(side="left")

        # ---------- progreso, botones y registro (abajo)
        f = ttk.Frame(r)
        f.pack(fill="x", padx=14, pady=(6, 0))
        self.v_prog = tk.DoubleVar(value=0)
        ttk.Progressbar(f, variable=self.v_prog, maximum=100, style="Green.Horizontal.TProgressbar").pack(fill="x")
        fe = ttk.Frame(f)
        fe.pack(fill="x", pady=(6, 0))
        self.v_estado = tk.StringVar(value="Listo para empezar.")
        ttk.Label(fe, textvariable=self.v_estado, style="Muted.TLabel").pack(side="left", fill="x", expand=True)
        self.b_cancelar = ttk.Button(fe, text="Cancelar", command=self.cancelar.set, state="disabled")
        self.b_cancelar.pack(side="right")
        ttk.Button(fe, text="Abrir carpeta de salida", command=lambda: abrir(self.carpeta_salida())).pack(
            side="right", padx=8)
        self.b_juntar = ttk.Button(fe, text="Juntar todas en una carpeta", command=self.click_juntar)
        self.b_juntar.pack(side="right")

        f = ttk.Frame(r, style="Card.TFrame")
        f.pack(fill="both", expand=False, padx=14, pady=(8, 14))
        ttk.Label(f, text="REGISTRO", style="Caption.TLabel").pack(anchor="w", padx=12, pady=(8, 0))
        self.log = tk.Text(f, height=8, font=("Consolas", 9), state="disabled", wrap="word",
                           bg=C["campo"], fg=C["texto2"], insertbackground=C["texto"], relief="flat", bd=0,
                           highlightthickness=0, padx=8, pady=6)
        self.log.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        barra_oscura(r)

        self.cargar_ligas()
        self.llenar_combo()
        self.cambiar_fuente()
        self.estado_base()
        r.after(100, self.revisar_cola)

    # ---- fuente
    def mapa(self):
        return self.cfg["ligas_sortitoutsi"] if self.cfg["fuente"] == "sortitoutsi" else self.cfg["ligas_cmtracker"]

    def cambiar_fuente(self):
        self.cfg["fuente"] = self.v_fuente.get()
        guardar_config(self.cfg)
        if self.cfg["fuente"] == "sortitoutsi":
            self.f_mega.pack(fill="x", padx=6, pady=(2, 6))
            self.poner_megapack(self.cfg.get("carpeta_megapack", ""), guardar=False)
        else:
            self.f_mega.pack_forget()
        sel = self.lista.curselection()
        self.llenar_lista()
        if sel:
            self.lista.selection_set(sel[0])
            self.mostrar_info()

    def poner_megapack(self, c, guardar=True):
        self.cfg["carpeta_megapack"] = c
        if guardar:
            guardar_config(self.cfg)
        self.v_mega.set(c or "(ninguno: las caras se bajan de internet, de a una)")

    def elegir_megapack(self):
        from tkinter import filedialog
        c = filedialog.askdirectory(title="Carpeta del megapack (la que tiene los face_<id>.png)",
                                    initialdir=self.cfg.get("carpeta_megapack") or os.path.expanduser("~"))
        if c:
            self.poner_megapack(os.path.normpath(c))

    # ---- helpers de ventana
    def carpeta_salida(self):
        os.makedirs(SALIDA, exist_ok=True)
        return SALIDA

    def escribir(self, txt):
        self.log.config(state="normal")
        self.log.insert("end", txt + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def cargar_ligas(self):
        c = self.cfg.get("carpeta_mundo", "")
        if es_mundo(c):
            self.v_mundo.set(c)
            try:
                self.ligas = cargar_mundo(c)
            except Exception as e:
                self.ligas = {}
                self.escribir(f"No pude leer fl26playerids.json: {e}")
        else:
            self.v_mundo.set("(sin elegir: tocá 'Cambiar...' y elegí la carpeta que tiene fl26playerids.json)")
            self.ligas = {}
        self.llenar_lista()

    def llenar_combo(self):
        if hasattr(self, "cb_liga"):
            self.cb_liga["values"] = [TODAS_LIGAS] + sorted(self.ligas, key=norm)
            if self.v_liga_conv.get() not in self.cb_liga["values"]:
                self.v_liga_conv.set(TODAS_LIGAS)

    def llenar_lista(self):
        filtro = norm(self.v_buscar.get())
        self.visibles = [n for n in sorted(self.ligas, key=norm) if filtro in norm(n)]
        self.lista.delete(0, "end")
        for n in self.visibles:
            marca = "   ✓" if n in self.mapa() else ""
            self.lista.insert("end", f"{n}   ({len(self.ligas[n])} equipos){marca}")

    def liga_elegida(self):
        sel = self.lista.curselection()
        return self.visibles[sel[0]] if sel else None

    def mostrar_info(self):
        liga = self.liga_elegida()
        if not liga:
            return
        n = sum(len(v) for v in self.ligas[liga].values())
        cm = self.mapa().get(liga)
        fuente = self.cfg["fuente"]
        extra = f"{fuente}: {cm}" if cm else f"te voy a pedir el link de {fuente}"
        self.v_info.set(f"{liga}: {len(self.ligas[liga])} equipos, {n} jugadores en tu mundo  -  {extra}")

    def elegir_mundo(self):
        from tkinter import filedialog, messagebox
        c = filedialog.askdirectory(title="Carpeta del mundo (la que tiene fl26playerids.json)",
                                    initialdir=self.cfg.get("carpeta_mundo") or os.path.expanduser("~"))
        if not c:
            return
        c = os.path.normpath(c)
        if not es_mundo(c):
            c = buscar_mundo_adentro(c) or c   # si eligió una carpeta de más arriba, lo busca adentro
        if not es_mundo(c):
            messagebox.showerror("Bot de minifaces", "No encontré fl26playerids.json en esa carpeta.\n\n"
                                 "Si el mundo se está descomprimiendo, esperá a que termine.\n"
                                 "Si no, elegí ...\\SiderAddons\\livecpk\\_FL26-<nombre del mundo>")
            return
        self.cfg["carpeta_mundo"] = c
        guardar_config(self.cfg)
        self.cargar_ligas()
        self.llenar_combo()
        self.estado_base()

    # ---- base FM -> PES
    def estado_base(self):
        b = cargar_base()
        if not b:
            self.v_base.set("Base: todavía no está armada.")
            return
        otro = "" if os.path.normcase(b.get("mundo", "")) == os.path.normcase(self.cfg["carpeta_mundo"]) else \
            "\n¡OJO! Esta base es de otro mundo; armala de nuevo para el mundo elegido."
        self.v_base.set(f"Base: {len(b['fm_a_pes'])} de {b.get('total_pes', '?')} jugadores de tu mundo con ID de FM "
                        f"(armada el {b.get('fecha', '?')}).{otro}")

    def lanzar(self, func, titulo, tipo_fin):
        """corre func(avisar, cancelado) en un hilo y manda el resultado a la cola"""
        self.cancelar.clear()
        for b in (self.b_empezar, self.b_base, self.b_conv, self.b_csv, self.b_juntar, self.b_dt, self.b_activar,
                  self.b_packs):
            b.config(state="disabled")
        self.b_cancelar.config(state="normal")
        self.lista.config(state="disabled")
        self.v_prog.set(0)
        self.escribir(f"--- {titulo} ---")

        def avisar(frac, texto, log=None):
            self.q.put(("avance", frac, texto, log))

        def correr():
            try:
                self.q.put((tipo_fin, func(avisar, self.cancelar.is_set)))
            except Cancelado:
                self.q.put(("cancelado",))
            except Exception:
                self.q.put(("error", traceback.format_exc()))

        self.hilo = threading.Thread(target=correr, daemon=True)
        self.hilo.start()

    def click_armar_base(self):
        from tkinter import messagebox
        if self.hilo and self.hilo.is_alive():
            return
        carpeta = self.cfg["carpeta_mundo"]
        if not es_mundo(carpeta):
            messagebox.showinfo("Bot de minifaces", "Primero elegí el mundo (arriba, 'Cambiar...').")
            return
        if not messagebox.askyesno("Armar base FM → PES",
                                   f"Voy a recorrer las {len(self.ligas)} ligas de tu mundo en sortitoutsi.\n"
                                   "Tarda bastante (puede ser más de una hora). Se abre Chrome: no lo cierres.\n"
                                   "Si lo cortás, la próxima vez sigue desde donde quedó.\n\n¿Arranco?"):
            return
        cfg = json.loads(json.dumps(self.cfg))
        self.lanzar(lambda av, ca: armar_base(carpeta, cfg, av, ca), "Armar base FM → PES", "fin_base")

    def click_dt(self):
        from tkinter import filedialog, messagebox
        if self.hilo and self.hilo.is_alive():
            return
        carpeta = self.cfg["carpeta_mundo"]
        if not cargar_base() or not os.path.exists(BASE_CSV):
            messagebox.showinfo("Bot de minifaces", "Primero armá la base (Paso 1).")
            return
        if not os.path.exists(os.path.join(carpeta, "common", "etc", "pesdb", "Team.bin")):
            messagebox.showerror("Bot de minifaces", "Para los DT necesito el mundo INSTALADO en el juego:\n"
                                 "elegí arriba ...\\SP Football Life\\SiderAddons\\livecpk\\_FL26...\n"
                                 "(el del zip descomprimido no trae Team.bin).")
            return
        staff = filedialog.askopenfilename(title="staff.csv del FM (lo hace 'Exportar DT del FM.bat')",
                                           filetypes=[("CSV", "*.csv"), ("Todos", "*.*")], initialdir=AQUI)
        if not staff:
            return
        fotos = filedialog.askdirectory(title="Carpeta con las fotos (megapack)",
                                        initialdir=self.cfg.get("carpeta_fotos") or os.path.expanduser("~"))
        if not fotos:
            return
        self.lanzar(lambda av, ca: fotos_dt(staff, os.path.normpath(fotos), carpeta, av, ca),
                    "Fotos de los DT", "fin_dt")

    def click_activar(self):
        from tkinter import filedialog
        if self.hilo and self.hilo.is_alive():
            return
        c = filedialog.askdirectory(title="Carpeta del juego (la que tiene SiderAddons)",
                                    initialdir=self.cfg.get("carpeta_juego") or "D:\\")
        if not c:
            return
        c = os.path.normpath(c)
        self.cfg["carpeta_juego"] = c
        guardar_config(self.cfg)
        self.lanzar(lambda av, ca: activar_minifaces(c, av, ca), "Activar minifaces en el juego", "fin_activar")

    def click_packs(self):
        from tkinter import filedialog, messagebox
        if self.hilo and self.hilo.is_alive():
            return
        carpeta = self.cfg["carpeta_mundo"]
        if not es_mundo(carpeta):
            messagebox.showinfo("Bot de minifaces", "Primero elegí el mundo (arriba, 'Cambiar...').")
            return
        if not os.path.exists(BASE_FM):
            messagebox.showinfo("Bot de minifaces", "Falta la lista del FM (base_fm.json.gz).\n\n"
                                "Importá de nuevo el players.csv con el botón A del Paso 1 (tarda un minuto) "
                                "y después armá los packs.")
            return
        fotos = filedialog.askdirectory(title="Carpeta con las fotos (megapack de sortitoutsi)",
                                        initialdir=self.cfg.get("carpeta_fotos") or self.cfg.get("carpeta_megapack")
                                        or os.path.expanduser("~"))
        if not fotos:
            return
        fotos = os.path.normpath(fotos)
        self.cfg["carpeta_fotos"] = fotos
        guardar_config(self.cfg)
        liga = self.v_liga_conv.get()
        sel = None if liga == TODAS_LIGAS else [liga]
        cfg = json.loads(json.dumps(self.cfg))
        self.lanzar(lambda av, ca: armar_packs(fotos, carpeta, cfg, av, ca, sel), f"Armar packs ({liga})", "fin_packs")

    def click_juntar(self):
        if self.hilo and self.hilo.is_alive():
            return
        self.lanzar(juntar_todas, "Juntar todas las minifaces en una carpeta", "fin_juntar")

    def click_importar_csv(self):
        from tkinter import filedialog, messagebox
        if self.hilo and self.hilo.is_alive():
            return
        carpeta = self.cfg["carpeta_mundo"]
        if not es_mundo(carpeta):
            messagebox.showinfo("Bot de minifaces", "Primero elegí el mundo (arriba, 'Cambiar...').")
            return
        ruta = filedialog.askopenfilename(
            title="players.csv de fmsave (rhiever.github.io/fmsave/app > Download CSV > players.csv)",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialdir=os.path.join(os.path.expanduser("~"), "Downloads"))
        if not ruta:
            return
        self.lanzar(lambda av, ca: base_desde_csv(ruta, carpeta, av, ca), "Importar lista del FM", "fin_base")

    def click_convertir(self):
        from tkinter import filedialog, messagebox
        if self.hilo and self.hilo.is_alive():
            return
        b = cargar_base()
        if not b:
            messagebox.showinfo("Bot de minifaces", "Primero armá la base (botón 'Armar / actualizar base').")
            return
        carpeta = self.cfg["carpeta_mundo"]
        if os.path.normcase(b.get("mundo", "")) != os.path.normcase(carpeta):
            if not messagebox.askyesno("Bot de minifaces", "La base es de otro mundo y los IDs no van a coincidir.\n"
                                       "¿Seguir igual?"):
                return
        fotos = filedialog.askdirectory(title="Carpeta con las fotos (con el ID de FM en el nombre)",
                                        initialdir=self.cfg.get("carpeta_fotos") or self.cfg.get("carpeta_megapack")
                                        or os.path.expanduser("~"))
        if not fotos:
            return
        fotos = os.path.normpath(fotos)
        self.cfg["carpeta_fotos"] = fotos
        guardar_config(self.cfg)
        if not self.salida_ok(carpeta):
            return
        liga = self.v_liga_conv.get()
        sel = None if liga == TODAS_LIGAS else [liga]
        cfg = json.loads(json.dumps(self.cfg))
        self.lanzar(lambda av, ca: convertir_carpeta(fotos, carpeta, cfg, av, ca, sel),
                    f"Convertir fotos ({liga})", "fin_conv")

    def salida_ok(self, carpeta):
        """si 'Minifaces por liga' tiene cosas de otro mundo, ofrece vaciarla"""
        from tkinter import messagebox
        if os.path.exists(MARCA_MUNDO):
            with open(MARCA_MUNDO, encoding="utf-8") as f:
                anterior = f.read().strip()
            if os.path.normcase(anterior) != os.path.normcase(carpeta):
                if messagebox.askyesno("Bot de minifaces",
                                       "La carpeta 'Minifaces por liga' tiene minifaces de otro mundo:\n"
                                       f"{anterior}\n\nLos IDs no sirven para este mundo. ¿La vacío y empiezo de cero?"):
                    shutil.rmtree(SALIDA, ignore_errors=True)
                else:
                    return False
        return True

    # ---- proceso
    def empezar(self):
        from tkinter import messagebox, simpledialog
        if self.hilo and self.hilo.is_alive():
            return
        liga = self.liga_elegida()
        if not liga:
            messagebox.showinfo("Bot de minifaces", "Elegí una liga de la lista.")
            return
        carpeta = self.cfg["carpeta_mundo"]

        # ¿la salida tiene minifaces de otro mundo?
        if not self.salida_ok(carpeta):
            return

        fuente = self.cfg["fuente"]
        liga_cm = self.mapa().get(liga)
        while not liga_cm:
            if fuente == "sortitoutsi":
                txt = simpledialog.askstring(
                    "Liga en sortitoutsi",
                    f"No sé qué número tiene '{liga}' en sortitoutsi.\n\n"
                    "Buscá la liga en sortitoutsi.net (Data Update) y pegá acá el link,\n"
                    "algo como .../football-manager-data-update/competition/23\n(o solo el número):",
                    parent=self.root)
            else:
                txt = simpledialog.askstring(
                    "Liga en cmtracker",
                    f"No sé qué número tiene '{liga}' en cmtracker.\n\n"
                    "Abrí cmtracker.net, filtrá los jugadores por esa liga\n"
                    "y pegá acá el link (o solo el número de league__in):",
                    parent=self.root)
            if txt is None:
                return
            txt = txt.strip()
            if txt.isdigit():
                liga_cm = int(txt)
            elif fuente == "sortitoutsi":
                m = re.search(r"competition/(\d+)", txt)
                if m:
                    liga_cm = int(m.group(1))
            else:
                q = parse_qs(urlparse(txt).query)
                if q.get("league__in"):
                    liga_cm = int(q["league__in"][0].split(",")[0])
                    if q.get("db"):
                        self.cfg["db"] = q["db"][0]
        self.mapa()[liga] = liga_cm
        guardar_config(self.cfg)
        sel = self.lista.curselection()
        self.llenar_lista()
        if sel:
            self.lista.selection_set(sel[0])

        clubes = self.ligas[liga]
        cfg = json.loads(json.dumps(self.cfg))
        self.lanzar(lambda av, ca: trabajo(liga, clubes, liga_cm, carpeta, cfg, av, ca),
                    f"{liga} ({fuente} {liga_cm})", "fin")

    def revisar_cola(self):
        from tkinter import messagebox
        try:
            while True:
                m = self.q.get_nowait()
                if m[0] == "avance":
                    _, frac, texto, log = m
                    if frac is not None:
                        self.v_prog.set(frac * 100)
                    if texto:
                        self.v_estado.set(texto)
                    if log:
                        self.escribir(log)
                elif m[0] == "fin":
                    r = m[1]
                    self.terminar()
                    self.escribir(f"Minifaces hechas: {r['ok']}  |  no encontrados en tu mundo: {r['faltan']}  |  "
                                  f"sin foto: {r['sin_foto']}  |  equipos reconocidos: {r['equipos']} de {r['equipos_cm']}")
                    self.escribir(f"Informe: {r['informe']}")
                    if messagebox.askyesno(
                            "¡Listo!",
                            f"Minifaces hechas: {r['ok']}\n"
                            f"No encontrados en tu mundo: {r['faltan']}\n"
                            f"Sin foto en la fuente: {r['sin_foto']}\n\n"
                            f"Quedaron en:\n{r['carpeta']}\n"
                            "(adentro hay un LEEME.txt con cómo instalarlas)\n\n¿Abro la carpeta?"):
                        abrir(r["carpeta"])
                elif m[0] == "fin_base":
                    r = m[1]
                    self.terminar()
                    self.estado_base()
                    self.escribir(f"Base lista: {r['con_fm']} de {r['total']} jugadores con ID de FM ({r['ligas']} ligas).")
                    if messagebox.askyesno("¡Base lista!",
                                           f"{r['con_fm']} de {r['total']} jugadores de tu mundo tienen su ID de FM.\n\n"
                                           "Los que no se encontraron están en 'base_sin_id_fm.txt'.\n\n"
                                           "¿Abro la tabla?"):
                        abrir(BASE_CSV)
                elif m[0] == "fin_conv":
                    r = m[1]
                    self.terminar()
                    self.escribir(f"Fotos de jugadores de tu mundo: {r['encontradas']}  |  convertidas: {r['ok']}  |  "
                                  f"vacías: {r['vacias']}")
                    if messagebox.askyesno("¡Listo!",
                                           f"Fotos encontradas de jugadores de tu mundo: {r['encontradas']}\n"
                                           f"Minifaces hechas: {r['ok']} (en {r['ligas']} liga/s)\n\n"
                                           f"Quedaron en:\n{r['carpeta']}\n"
                                           "(una carpeta por liga, cada una con su LEEME.txt)\n\n¿Abro la carpeta?"):
                        abrir(r["carpeta"])
                elif m[0] == "fin_dt":
                    r = m[1]
                    self.terminar()
                    self.escribir(f"DT: clubes nuevos {r['clubes']} | reconocidos en el FM {r['reconocidos']} | "
                                  f"con DT en el FM {r['con_dt']} | fotos hechas {r['ok']} | sin foto {r['sin_foto']}")
                    if messagebox.askyesno("¡Listo!", f"Fotos de DT hechas: {r['ok']}\n\nQuedaron en:\n{r['carpeta']}\n"
                                           "(adentro hay un LEEME.txt)\n\n¿Abro la carpeta?"):
                        abrir(r["carpeta"])
                elif m[0] == "fin_activar":
                    r = m[1]
                    self.terminar()
                    self.escribir(f"Minifaces activas en el juego: {r['minifaces']} (en {r['carpetas']} carpetas) | "
                                  f"jugadores nuevos del mundo: {r['nuevos']} | pasados a newfaces3d ahora: {r['movidos']}")
                    messagebox.showinfo("¡Listo!",
                                        f"Minifaces activas encontradas: {r['minifaces']}\n"
                                        f"Jugadores del mundo que ahora van a mostrar su miniface: {r['movidos']}\n\n"
                                        + ("Ya estaba todo activado." if not r["movidos"] else
                                           "Listo, abrí el juego.\n(Copia del original: fl26world.txt.antes_minifaces)"))
                elif m[0] == "fin_packs":
                    r = m[1]
                    self.terminar()
                    self.escribir(f"Packs hechos: {r['packs']}  |  minifaces: {r['fotos']}  |  fotos vacías: {r['vacias']}")
                    if messagebox.askyesno("¡Packs listos!", f"Packs hechos: {r['packs']} ({r['fotos']} minifaces)\n\n"
                                           f"Quedaron en:\n{r['carpeta']}\n\n¿Abro la carpeta?"):
                        abrir(r["carpeta"])
                elif m[0] == "fin_juntar":
                    r = m[1]
                    self.terminar()
                    self.escribir(f"Juntadas {r['n']} minifaces en {r['carpeta']}")
                    if messagebox.askyesno("¡Listo!", f"{r['n']} minifaces juntas en:\n{r['carpeta']}\n\n¿Abro la carpeta?"):
                        abrir(os.path.join(r["carpeta"], "common", "render", "symbol", "player"))
                elif m[0] == "cancelado":
                    self.terminar()
                    self.v_estado.set("Cancelado.")
                    self.escribir("Cancelado.")
                elif m[0] == "error":
                    self.terminar()
                    self.v_estado.set("Error (mirá el registro)")
                    self.escribir(m[1])
                    messagebox.showerror("Error", "Algo falló. Mandale a Claude una captura del registro.\n\n"
                                         + m[1].strip().splitlines()[-1])
        except queue.Empty:
            pass
        self.root.after(100, self.revisar_cola)

    def terminar(self):
        for b in (self.b_empezar, self.b_base, self.b_conv, self.b_csv, self.b_juntar, self.b_dt, self.b_activar,
                  self.b_packs):
            b.config(state="normal")
        self.b_cancelar.config(state="disabled")
        self.lista.config(state="normal")

    def cerrar(self):
        """cerrar de verdad: corta la descarga, cierra Chrome y termina el programa"""
        from tkinter import messagebox
        if self.hilo and self.hilo.is_alive():
            if not messagebox.askyesno("Bot de minifaces", "Todavía está trabajando. ¿Cortar y cerrar?"):
                return
            self.cancelar.set()
        try:
            self.root.destroy()
        finally:
            os._exit(0)   # mata también el hilo de descarga y el Chrome que abrió el bot

    def run(self):
        self.root.mainloop()
        os._exit(0)


if __name__ == "__main__":
    try:
        asegurar_dependencias()
        App().run()
    except SystemExit:
        raise
    except Exception:
        if CONGELADO:      # sin consola: mostrar el error en una ventana
            try:
                import tkinter as _tk
                from tkinter import messagebox as _mb
                _r = _tk.Tk()
                _r.withdraw()
                _mb.showerror("Bot de minifaces", "Error al arrancar:\n\n" + traceback.format_exc()[-1500:])
            except Exception:
                pass
        else:
            traceback.print_exc()
            input("\nERROR - mandale una captura de esto a Claude. Enter para cerrar...")
