"""
Conversor de minifaces - FL26 / PES
-----------------------------------
Pasa packs de minifaces con el ID del Football Manager (<id_fm>.dds, los hace el 'Bot de minifaces')
a los IDs del PES de TU mundo de FL Mod Studio. Trae adentro la lista del FM (base_fm.json.gz),
así que cada uno solo elige su juego, agrega los packs y toca Convertir.

Se puede arrastrar al .exe la carpeta del juego y/o los .zip de los packs.
"""
import json
import os
import queue
import re
import shutil
import sys
import threading
import traceback
import zipfile

import bot_minifaces as bm
from textos_conversor import IDIOMAS, TEXTOS
from bot_minifaces import (COLORES, PACK_FORMATO, Cancelado, abrir, activar_minifaces, aplicar_tema,
                           barra_oscura, buscar_mundo_adentro, buscar_sider, cargar_base_fm, cargar_mundo,
                           cruzar_fm, es_mundo)

AQUI = bm.AQUI
CONTENIDO = "Minifaces FM"                                  # carpeta de contenido que va a livecpk
SALIDA = os.path.join(AQUI, "Minifaces para tu mundo")
DESTINO = os.path.join(SALIDA, CONTENIDO, "common", "render", "symbol", "player")
MARCA = os.path.join(SALIDA, "mundo.txt")
CFG = os.path.join(AQUI, "config_conversor.json")
CACHE = os.path.join(AQUI, "cache_conversor.json")


# ------------------------------------------------------------------ idioma
IDIOMA = "es"


def tr(clave, **kw):
    t = TEXTOS[clave].get(IDIOMA) or TEXTOS[clave]["es"]
    return t.format(**kw) if kw and isinstance(t, str) else t


def idioma_sistema():
    """idioma de Windows: español, portugués o (cualquier otro) inglés"""
    try:
        import ctypes
        lid = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
        return {0x0A: "es", 0x16: "pt"}.get(lid, "en")
    except Exception:
        import locale
        l = (locale.getlocale()[0] or "").lower()
        return "es" if l.startswith(("es", "spanish")) else "pt" if l.startswith(("pt", "portug")) else "en"


MENSAJES_BOT = [   # mensajes que vienen de bot_minifaces (en español) -> clave traducida
    (re.compile(r"^Cruzando (.+)\.\.\.$"), lambda m: tr("cruzando", liga=m.group(1))),
    (re.compile(r"^Preparando la lista del Football Manager\.\.\.$"), lambda m: tr("preparando")),
    (re.compile(r"^Revisando carpetas activas: (\d+) de (\d+)$"), lambda m: tr("revisando", k=m.group(1), n=m.group(2))),
    (re.compile(r"^  (.+): minifaces encontradas$"), lambda m: tr("encontradas_en", c=m.group(1))),
    (re.compile(r"^¡Listo!$"), lambda m: tr("listo")),
]


def traducir(texto):
    if not texto or IDIOMA == "es":
        return texto
    for rx, f in MENSAJES_BOT:
        m = rx.match(texto)
        if m:
            return f(m)
    return texto


# ------------------------------------------------------------------ datos
def buscar_base():
    """base_fm.json.gz al lado del .exe (si hay una más nueva) o la que viene adentro del .exe"""
    for d in (AQUI, getattr(sys, "_MEIPASS", None)):
        if d and os.path.exists(os.path.join(d, "base_fm.json.gz")):
            return os.path.join(d, "base_fm.json.gz")
    return None


def raices_activas(sider):
    """carpetas de contenido activas en sider.ini, en orden (la de más arriba manda)"""
    raices = []
    try:
        with open(os.path.join(sider, "sider.ini"), encoding="utf-8", errors="replace") as f:
            for l in f:
                m = re.match(r'\s*cpk\.root\s*=\s*"([^"]+)"', l)
                if m:
                    r = m.group(1).replace("\\", os.sep).replace("/", os.sep)
                    raices.append(os.path.normpath(os.path.join(sider, r) if not os.path.isabs(r) else r))
    except OSError:
        pass
    return raices


def ubicar(ruta):
    """lo que haya elegido la persona (juego, SiderAddons, carpeta del mundo o fl26playerids.json)
    -> (carpeta del mundo, carpeta SiderAddons o None)"""
    ruta = os.path.normpath(ruta)
    if os.path.isfile(ruta):
        ruta = os.path.dirname(ruta)
    if es_mundo(ruta):                       # ...\SiderAddons\livecpk\_FL26xxx
        sider = os.path.dirname(os.path.dirname(ruta))
        return ruta, (sider if os.path.exists(os.path.join(sider, "sider.ini")) else None)
    sider = buscar_sider(ruta)
    if sider:
        for r in raices_activas(sider):      # el mundo que está activo en el juego
            if es_mundo(r):
                return r, sider
        return buscar_mundo_adentro(os.path.join(sider, "livecpk")), sider
    return buscar_mundo_adentro(ruta), None


def datos_mundo(mundo):
    ligas = cargar_mundo(mundo)
    return dict(ligas=len([l for l in ligas if l != bm.NUEVOS_EN_JUEGO]),
                jugadores=sum(len(js) for clubes in ligas.values() for js in clubes.values()))


def mapa_fm_a_pes(base, mundo, avisar, cancelado):
    """{id_fm: id_pes} para este mundo. Se guarda en cache: la segunda vez es instantáneo."""
    j = os.path.join(mundo, "fl26playerids.json")
    clave = [os.path.normcase(mundo), os.path.getmtime(j), os.path.getsize(j),
             os.path.getmtime(base), os.path.getsize(base)]
    try:
        with open(CACHE, encoding="utf-8") as f:
            c = json.load(f)
        if c.get("clave") == clave:
            avisar(0.30, tr("cache"))
            return {k: int(v) for k, v in c["mapa"].items()}, c["total"]
    except Exception:
        pass
    avisar(0.02, tr("cargando_fm"))
    fm, _ = cargar_base_fm(base)
    filas, _, total = cruzar_fm(fm, cargar_mundo(mundo), avisar, cancelado, 0.05, 0.30)
    mapa = {f["id_fm"]: int(f["id_pes"]) for f in filas}
    try:
        with open(CACHE, "w", encoding="utf-8") as f:
            json.dump({"clave": clave, "mapa": mapa, "total": total}, f)
    except OSError:
        pass
    return mapa, total


def leer_pack(ruta):
    """-> (nombre, {id_fm: función que devuelve los bytes del DDS})"""
    archivos = {}
    nombre = os.path.splitext(os.path.basename(ruta.rstrip("\\/")))[0]
    if os.path.isdir(ruta):
        for raiz, _, fs in os.walk(ruta):
            for f in fs:
                m = re.fullmatch(r"(?:face_)?(\d+)\.dds", f.lower())
                if m:
                    p = os.path.join(raiz, f)
                    archivos[m.group(1)] = (lambda p=p: open(p, "rb").read())
        info = os.path.join(ruta, "pack.json")
        if os.path.exists(info):
            try:
                with open(info, encoding="utf-8") as fh:
                    nombre = json.load(fh).get("liga") or nombre
            except Exception:
                pass
        return nombre, archivos
    z = zipfile.ZipFile(ruta)
    for n in z.namelist():
        m = re.fullmatch(r"(?:face_)?(\d+)\.dds", os.path.basename(n).lower())
        if m:
            archivos[m.group(1)] = (lambda n=n: z.read(n))
    if "pack.json" in z.namelist():
        try:
            info = json.loads(z.read("pack.json"))
            if info.get("formato") == PACK_FORMATO:
                nombre = info.get("liga") or nombre
        except Exception:
            pass
    return nombre, archivos


def contar_pack(ruta):
    try:
        nombre, archivos = leer_pack(ruta)
        return nombre, len(archivos)
    except Exception:
        return os.path.basename(ruta), 0


def convertir(packs, mundo, avisar, cancelado):
    base = buscar_base()
    if not base:
        raise RuntimeError(tr("err_base"))
    mapa, total = mapa_fm_a_pes(base, mundo, avisar, cancelado)
    if not mapa:
        raise RuntimeError(tr("err_ninguno"))

    # si lo que hay en la carpeta de salida es de otro mundo, se borra (los IDs no sirven)
    if os.path.exists(MARCA):
        with open(MARCA, encoding="utf-8") as f:
            anterior = f.read().strip()
        if os.path.normcase(anterior) != os.path.normcase(mundo) and os.path.isdir(os.path.join(SALIDA, CONTENIDO)):
            shutil.rmtree(os.path.join(SALIDA, CONTENIDO))
            avisar(None, None, tr("borre_otro"))
    os.makedirs(DESTINO, exist_ok=True)
    with open(MARCA, "w", encoding="utf-8") as f:
        f.write(mundo)

    resumen, puestas = [], 0
    for k, ruta in enumerate(packs):
        nombre, archivos = leer_pack(ruta)
        n = 0
        for i, (fm, leer) in enumerate(archivos.items(), 1):
            if i % 100 == 0:
                if cancelado():
                    raise Cancelado()
                avisar(0.30 + 0.68 * (k + i / max(1, len(archivos))) / len(packs),
                       tr("progreso_pack", nombre=nombre, i=i, n=len(archivos)))
            pid = mapa.get(fm)
            if pid is None:
                continue
            with open(os.path.join(DESTINO, f"{pid}.dds"), "wb") as f:
                f.write(leer())
            n += 1
        resumen.append((nombre, len(archivos), n))
        puestas += n
        avisar(None, None, tr("resumen_pack", nombre=nombre, n=n, t=len(archivos)))
    ids = sorted(int(f[:-4]) for f in os.listdir(DESTINO) if f[:-4].isdigit())
    with open(os.path.join(SALIDA, CONTENIDO, "LEEME.txt"), "w", encoding="utf-8") as f:
        f.write(tr("leeme", mundo=mundo, n=len(ids), carpeta=CONTENIDO))
    avisar(1.0, tr("listo"))
    return dict(resumen=resumen, puestas=puestas, total_carpeta=len(ids), mundo_total=total,
                reconocidos=len(mapa), carpeta=os.path.join(SALIDA, CONTENIDO))


def poner_en_sider_ini(sider, carpeta):
    """agrega cpk.root = ".\\livecpk\\<carpeta>" arriba de las otras carpetas (si no está). -> True si cambió"""
    ini = os.path.join(sider, "sider.ini")
    with open(ini, "rb") as f:
        crudo = f.read()
    try:
        texto, cod = crudo.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        texto, cod = crudo.decode("latin-1"), "latin-1"
    fin = "\r\n" if "\r\n" in texto else "\n"
    lineas = texto.splitlines()
    objetivo = os.path.normcase(os.path.normpath(os.path.join(sider, "livecpk", carpeta)))
    if any(os.path.normcase(r) == objetivo for r in raices_activas(sider)):
        return False
    nueva = f'cpk.root = ".\\livecpk\\{carpeta}"'
    pos = next((i for i, l in enumerate(lineas) if re.match(r"\s*cpk\.root\s*=", l)), None)
    if pos is None:
        raise RuntimeError(tr("err_cpk"))
    lineas.insert(pos, nueva)
    copia = ini + ".antes_conversor"
    if not os.path.exists(copia):
        shutil.copy2(ini, copia)
    with open(ini, "w", encoding=cod, newline="") as f:
        f.write(fin.join(lineas) + fin)
    return True


def instalar(juego, avisar, cancelado):
    sider = buscar_sider(juego)
    if not sider:
        raise RuntimeError(tr("err_sider"))
    if not os.path.exists(os.path.join(sider, "modules", "fl26world.txt")):
        raise RuntimeError(tr("err_world"))
    origen = os.path.join(SALIDA, CONTENIDO)
    if not os.path.isdir(DESTINO) or not os.listdir(DESTINO):
        raise RuntimeError(tr("falta_convertir"))
    destino = os.path.join(sider, "livecpk", CONTENIDO)
    archivos = [(r, f) for r, _, fs in os.walk(origen) for f in fs]
    for k, (r, f) in enumerate(archivos, 1):
        if k % 200 == 0:
            if cancelado():
                raise Cancelado()
            avisar(0.8 * k / len(archivos), tr("copiando", k=k, n=len(archivos)))
        d = os.path.join(destino, os.path.relpath(r, origen))
        os.makedirs(d, exist_ok=True)
        shutil.copy2(os.path.join(r, f), d)
    cambio_ini = poner_en_sider_ini(sider, CONTENIDO)
    avisar(0.85, tr("arreglando"))
    r = activar_minifaces(juego, avisar, cancelado)
    r.update(copiadas=len(archivos), cambio_ini=cambio_ini, destino=destino)
    avisar(1.0, tr("instalado"))
    return r


# ------------------------------------------------------------------ config
def cargar_cfg():
    try:
        with open(CFG, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def guardar_cfg(c):
    try:
        with open(CFG, "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False, indent=1)
    except OSError:
        pass


# ------------------------------------------------------------------ ventana
class App:
    def __init__(self, argumentos):
        import tkinter as tk
        global IDIOMA
        self.cfg = cargar_cfg()
        IDIOMA = self.cfg.get("idioma") if self.cfg.get("idioma") in IDIOMAS else idioma_sistema()
        self.q = queue.Queue()
        self.hilo = None
        self.cancelar = threading.Event()
        self.mundo = None
        self.sider = None
        self.lineas_log = []
        self.packs = [p for p in self.cfg.get("packs", []) if os.path.exists(p)]

        r = self.root = tk.Tk()
        r.protocol("WM_DELETE_WINDOW", self.cerrar)
        try:
            r.iconbitmap(os.path.join(getattr(sys, "_MEIPASS", AQUI), "icono.ico"))
        except Exception:
            pass
        r.geometry("720x770")
        r.minsize(600, 620)
        aplicar_tema(r)
        self.construir()
        barra_oscura(r)

        self.escribir(tr("base_ok") if buscar_base() else tr("base_falta"))
        # lo que arrastraron al .exe: carpeta del juego / mundo y .zip de packs
        for a in argumentos:
            if a.lower().endswith(".zip") or (os.path.isdir(a) and not ubicar(a)[0]):
                self.sumar_pack(a)
            else:
                self.cfg["juego"] = a
        self.poner_juego(self.cfg.get("juego"), avisar_error=bool(argumentos))
        self.refrescar_packs()
        if not self.cfg.get("tutorial_visto"):
            r.after(400, self.tutorial)
        r.after(100, self.revisar_cola)

    def construir(self):
        """arma (o rearma, al cambiar de idioma) todos los controles de la ventana"""
        import tkinter as tk
        from tkinter import ttk
        r = self.root
        for w in r.winfo_children():
            w.destroy()
        r.title(tr("titulo"))
        C = COLORES
        pad = dict(padx=14, pady=5)

        h = ttk.Frame(r, style="Header.TFrame")
        h.pack(fill="x")
        hd = ttk.Frame(h, style="Header.TFrame")
        hd.pack(side="right", padx=(8, 16))
        self.v_idioma = tk.StringVar(value=IDIOMAS[IDIOMA])
        cb = ttk.Combobox(hd, textvariable=self.v_idioma, values=list(IDIOMAS.values()), state="readonly", width=11)
        cb.pack(side="right", padx=(6, 0))
        cb.bind("<<ComboboxSelected>>", lambda e: self.cambiar_idioma())
        ttk.Button(hd, text=tr("ayuda"), command=self.tutorial).pack(side="right")
        hi = ttk.Frame(h, style="Header.TFrame")
        hi.pack(side="left", padx=16, pady=(10, 10))
        ttk.Label(hi, text=tr("titulo"), style="Title.TLabel").pack(anchor="w")
        ttk.Label(hi, text=tr("sub"), style="HeaderSub.TLabel").pack(anchor="w")

        # 1) juego
        f = ttk.Frame(r, style="Card.TFrame")
        f.pack(fill="x", padx=14, pady=(12, 5))
        ttk.Label(f, text=tr("paso1"), style="Caption.TLabel").pack(anchor="w", padx=12, pady=(10, 2))
        self.v_mundo = tk.StringVar(value=getattr(self, "texto_mundo", tr("elegi_juego")))
        ttk.Label(f, textvariable=self.v_mundo, style="Card.TLabel", wraplength=640, justify="left").pack(
            fill="x", padx=12, pady=2)
        fb = ttk.Frame(f, style="Card.TFrame")
        fb.pack(fill="x", padx=12, pady=(6, 12))
        ttk.Button(fb, text=tr("elegir_juego"), style="Accent.TButton", command=self.elegir_juego).pack(side="left")
        ttk.Button(fb, text=tr("o_json"), command=self.elegir_json).pack(side="left", padx=8)

        # 2) packs
        f = ttk.Frame(r, style="Card.TFrame")
        f.pack(fill="both", expand=True, **pad)
        ttk.Label(f, text=tr("paso2"), style="Caption.TLabel").pack(anchor="w", padx=12, pady=(10, 2))
        fl = ttk.Frame(f, style="Card.TFrame")
        fl.pack(fill="both", expand=True, padx=12, pady=(2, 4))
        self.lista = tk.Listbox(fl, activestyle="none", font=("Segoe UI", 10), exportselection=False,
                                selectmode="extended", bg=C["campo"], fg=C["texto"], selectbackground=C["acento"],
                                selectforeground="#ffffff", highlightthickness=1, highlightbackground=C["borde"],
                                highlightcolor=C["acento"], relief="flat", bd=0, height=8)
        sb = ttk.Scrollbar(fl, orient="vertical", command=self.lista.yview)
        self.lista.config(yscrollcommand=sb.set)
        self.lista.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        fb = ttk.Frame(f, style="Card.TFrame")
        fb.pack(fill="x", padx=12, pady=(4, 12))
        ttk.Button(fb, text=tr("agregar_packs"), command=self.agregar_packs).pack(side="left")
        ttk.Button(fb, text=tr("agregar_carpeta"), command=self.agregar_carpeta).pack(side="left", padx=8)
        ttk.Button(fb, text=tr("quitar"), command=self.quitar_packs).pack(side="left")

        # 3) convertir / instalar
        f = ttk.Frame(r, style="Card.TFrame")
        f.pack(fill="x", **pad)
        ttk.Label(f, text=tr("paso3"), style="Caption.TLabel").pack(anchor="w", padx=12, pady=(10, 2))
        ttk.Label(f, style="Card.TLabel", wraplength=640, justify="left", text=tr("paso3_texto")).pack(
            fill="x", padx=12, pady=2)
        fb = ttk.Frame(f, style="Card.TFrame")
        fb.pack(fill="x", padx=12, pady=(6, 12))
        self.b_conv = ttk.Button(fb, text=tr("convertir"), style="Accent.TButton", command=self.click_convertir)
        self.b_conv.pack(side="left")
        self.b_inst = ttk.Button(fb, text=tr("instalar"), command=self.click_instalar)
        self.b_inst.pack(side="left", padx=8)
        ttk.Button(fb, text=tr("abrir_carpeta"), command=self.abrir_salida).pack(side="right")

        # progreso y registro
        f = ttk.Frame(r)
        f.pack(fill="x", padx=14, pady=(6, 0))
        self.v_prog = tk.DoubleVar(value=0)
        ttk.Progressbar(f, variable=self.v_prog, maximum=100, style="Green.Horizontal.TProgressbar").pack(fill="x")
        fe = ttk.Frame(f)
        fe.pack(fill="x", pady=(6, 0))
        self.v_estado = tk.StringVar(value=tr("listo_empezar"))
        ttk.Label(fe, textvariable=self.v_estado, style="Muted.TLabel").pack(side="left", fill="x", expand=True)
        self.b_cancelar = ttk.Button(fe, text=tr("cancelar"), command=self.cancelar.set, state="disabled")
        self.b_cancelar.pack(side="right")
        f = ttk.Frame(r, style="Card.TFrame")
        f.pack(fill="both", padx=14, pady=(8, 14))
        self.log = tk.Text(f, height=7, font=("Consolas", 9), state="disabled", wrap="word", bg=C["campo"],
                           fg=C["texto2"], relief="flat", bd=0, highlightthickness=0, padx=8, pady=6)
        self.log.pack(fill="both", expand=True, padx=12, pady=12)
        if self.lineas_log:
            self.log.config(state="normal")
            self.log.insert("end", "\n".join(self.lineas_log) + "\n")
            self.log.see("end")
            self.log.config(state="disabled")

    def cambiar_idioma(self):
        global IDIOMA
        nuevo = next(k for k, v in IDIOMAS.items() if v == self.v_idioma.get())
        if nuevo == IDIOMA:
            return
        if self.hilo and self.hilo.is_alive():
            from tkinter import messagebox
            self.v_idioma.set(IDIOMAS[IDIOMA])
            messagebox.showinfo(tr("titulo"), tr("ocupado"))
            return
        IDIOMA = nuevo
        self.cfg["idioma"] = nuevo
        guardar_cfg(self.cfg)
        self.construir()
        self.poner_juego(self.cfg.get("juego"), avisar_error=False)
        self.refrescar_packs()

    def tutorial(self):
        """ventanita cortita de 'cómo se usa'"""
        import tkinter as tk
        from tkinter import ttk
        C = COLORES
        v = tk.Toplevel(self.root)
        v.title(tr("tuto_titulo"))
        v.configure(bg=C["fondo"])
        v.resizable(False, False)
        v.transient(self.root)
        try:
            v.iconbitmap(os.path.join(getattr(sys, "_MEIPASS", AQUI), "icono.ico"))
        except Exception:
            pass
        ttk.Label(v, text=tr("tuto_titulo"), font=("Segoe UI Semibold", 15)).pack(anchor="w", padx=20, pady=(16, 8))
        for num, titulo, texto in tr("tuto"):
            f = ttk.Frame(v, style="Card.TFrame")
            f.pack(fill="x", padx=20, pady=4)
            tk.Label(f, text=num, bg=C["acento"], fg="#ffffff", font=("Segoe UI Semibold", 14), width=2).pack(
                side="left", fill="y", padx=(0, 10))
            g = ttk.Frame(f, style="Card.TFrame")
            g.pack(side="left", fill="x", expand=True, pady=8, padx=(0, 10))
            ttk.Label(g, text=titulo, style="Card.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w")
            ttk.Label(g, text=texto, style="CardMuted.TLabel", wraplength=440, justify="left").pack(anchor="w")
        ttk.Label(v, text=tr("tuto_archivos"), style="Muted.TLabel", wraplength=500, justify="left").pack(
            anchor="w", padx=20, pady=(10, 4))

        def cerrar():
            self.cfg["tutorial_visto"] = True
            guardar_cfg(self.cfg)
            v.destroy()
        ttk.Button(v, text=tr("entendido"), style="Accent.TButton", command=cerrar).pack(anchor="e", padx=20, pady=(6, 16))
        v.protocol("WM_DELETE_WINDOW", cerrar)
        barra_oscura(v)
        v.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - v.winfo_width()) // 2
        y = self.root.winfo_rooty() + 60
        v.geometry(f"+{max(0, x)}+{max(0, y)}")
        v.grab_set()
        v.focus_set()

    # ---- helpers
    def escribir(self, txt):
        self.lineas_log.append(txt)
        self.log.config(state="normal")
        self.log.insert("end", txt + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def poner_juego(self, ruta, avisar_error=True):
        from tkinter import messagebox
        self.mundo = self.sider = None
        if ruta and os.path.exists(ruta):
            self.mundo, self.sider = ubicar(ruta)
            if self.mundo:
                self.cfg["juego"] = ruta
                guardar_cfg(self.cfg)
                nombre = os.path.basename(self.mundo)
                try:
                    d = datos_mundo(self.mundo)
                    txt = tr("mundo_info", mundo=nombre, ligas=d["ligas"], jug=d["jugadores"])
                except Exception as e:
                    txt = tr("mundo_error", mundo=nombre, e=e)
                txt += "\n" + (tr("juego_info", juego=os.path.dirname(self.sider)) if self.sider else tr("sin_juego"))
                self.texto_mundo = txt
                self.v_mundo.set(txt)
                return
            if avisar_error:
                messagebox.showerror(tr("titulo"), tr("no_hay_mundo"))
        self.texto_mundo = tr("elegi_juego")
        self.v_mundo.set(self.texto_mundo)

    def elegir_juego(self):
        from tkinter import filedialog
        c = filedialog.askdirectory(title=tr("dlg_juego"), initialdir=self.cfg.get("juego") or "C:\\")
        if c:
            self.poner_juego(os.path.normpath(c))

    def elegir_json(self):
        from tkinter import filedialog
        c = filedialog.askopenfilename(title=tr("dlg_json"),
                                       filetypes=[("fl26playerids.json", "fl26playerids.json"), ("JSON", "*.json")])
        if c:
            self.poner_juego(os.path.normpath(c))

    def sumar_pack(self, ruta):
        ruta = os.path.normpath(ruta)
        if ruta not in self.packs:
            self.packs.append(ruta)

    def refrescar_packs(self):
        self.lista.delete(0, "end")
        self.info_packs = []
        for p in self.packs:
            nombre, n = contar_pack(p)
            self.info_packs.append((nombre, n))
            self.lista.insert("end", tr("pack_item", nombre=nombre, n=n) if n else tr("pack_vacio", nombre=nombre))
        self.cfg["packs"] = self.packs
        guardar_cfg(self.cfg)

    def agregar_packs(self):
        from tkinter import filedialog
        fs = filedialog.askopenfilenames(title=tr("dlg_packs"), filetypes=[("Packs", "*.zip")],
                                         initialdir=self.cfg.get("carpeta_packs") or os.path.expanduser("~"))
        for p in fs:
            self.sumar_pack(p)
        if fs:
            self.cfg["carpeta_packs"] = os.path.dirname(fs[0])
            self.refrescar_packs()

    def agregar_carpeta(self):
        from tkinter import filedialog
        c = filedialog.askdirectory(title=tr("dlg_carpeta"),
                                    initialdir=self.cfg.get("carpeta_packs") or os.path.expanduser("~"))
        if not c:
            return
        zips = sorted(os.path.join(c, f) for f in os.listdir(c) if f.lower().endswith(".zip"))
        for p in zips or [c]:
            self.sumar_pack(p)
        self.cfg["carpeta_packs"] = c
        self.refrescar_packs()

    def quitar_packs(self):
        for i in sorted(self.lista.curselection(), reverse=True):
            del self.packs[i]
        self.refrescar_packs()

    def abrir_salida(self):
        os.makedirs(SALIDA, exist_ok=True)
        abrir(os.path.join(SALIDA, CONTENIDO) if os.path.isdir(os.path.join(SALIDA, CONTENIDO)) else SALIDA)

    # ---- trabajo en segundo plano
    def lanzar(self, func, titulo, tipo):
        self.cancelar.clear()
        for b in (self.b_conv, self.b_inst):
            b.config(state="disabled")
        self.b_cancelar.config(state="normal")
        self.v_prog.set(0)
        self.escribir(f"--- {titulo} ---")

        def avisar(frac, texto, log=None):
            self.q.put(("avance", frac, traducir(texto), traducir(log)))

        def correr():
            try:
                self.q.put((tipo, func(avisar, self.cancelar.is_set)))
            except Cancelado:
                self.q.put(("cancelado",))
            except Exception:
                self.q.put(("error", traceback.format_exc()))

        self.hilo = threading.Thread(target=correr, daemon=True)
        self.hilo.start()

    def click_convertir(self):
        from tkinter import messagebox
        if self.hilo and self.hilo.is_alive():
            return
        if not self.mundo:
            messagebox.showinfo(tr("titulo"), tr("falta_juego"))
            return
        if not self.packs:
            messagebox.showinfo(tr("titulo"), tr("falta_pack"))
            return
        mundo, packs = self.mundo, list(self.packs)
        self.lanzar(lambda av, ca: convertir(packs, mundo, av, ca), tr("convertir"), "fin_conv")

    def click_instalar(self):
        from tkinter import filedialog, messagebox
        if self.hilo and self.hilo.is_alive():
            return
        if not os.path.isdir(DESTINO) or not os.listdir(DESTINO):
            messagebox.showinfo(tr("titulo"), tr("falta_convertir"))
            return
        juego = os.path.dirname(self.sider) if self.sider else None
        if not juego:
            juego = filedialog.askdirectory(title=tr("dlg_juego"))
            if not juego:
                return
        if not messagebox.askyesno(tr("titulo"), tr("confirmar_instalar", juego=juego, carpeta=CONTENIDO)):
            return
        self.lanzar(lambda av, ca: instalar(juego, av, ca), tr("instalar"), "fin_inst")

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
                elif m[0] == "fin_conv":
                    r = m[1]
                    self.terminar()
                    self.escribir(tr("log_reconocidos", n=r["reconocidos"], t=r["mundo_total"]))
                    self.escribir(tr("log_puestas", n=r["puestas"], t=r["total_carpeta"]))
                    detalle = "\n".join(f"  {n}: " + tr("de", p=p, t=t) for n, t, p in r["resumen"][:12])
                    if len(r["resumen"]) > 12:
                        detalle += "\n" + tr("mas_packs", n=len(r["resumen"]) - 12)
                    if messagebox.askyesno(tr("fin_conv_titulo"), tr("fin_conv", n=r["puestas"], detalle=detalle)):
                        self.click_instalar()
                elif m[0] == "fin_inst":
                    r = m[1]
                    self.terminar()
                    self.escribir(tr("log_instalado", n=r["copiadas"], m=r["movidos"],
                                     ini=tr("ini_agregada") if r["cambio_ini"] else tr("ini_estaba")))
                    messagebox.showinfo(tr("fin_inst_titulo"), tr("fin_inst", n=r["copiadas"], m=r["movidos"]))
                elif m[0] == "cancelado":
                    self.terminar()
                    self.v_estado.set(tr("cancelado"))
                    self.escribir(tr("cancelado"))
                elif m[0] == "error":
                    self.terminar()
                    self.v_estado.set(tr("error_estado"))
                    self.escribir(m[1])
                    messagebox.showerror(tr("error"), m[1].strip().splitlines()[-1].split(": ", 1)[-1])
        except queue.Empty:
            pass
        self.root.after(100, self.revisar_cola)

    def terminar(self):
        for b in (self.b_conv, self.b_inst):
            b.config(state="normal")
        self.b_cancelar.config(state="disabled")

    def cerrar(self):
        if self.hilo and self.hilo.is_alive():
            self.cancelar.set()
        try:
            self.root.destroy()
        finally:
            os._exit(0)

    def run(self):
        self.root.mainloop()
        os._exit(0)


if __name__ == "__main__":
    try:
        App([a for a in sys.argv[1:] if os.path.exists(a)]).run()
    except SystemExit:
        raise
    except Exception:
        if bm.CONGELADO:
            try:
                import tkinter as _tk
                from tkinter import messagebox as _mb
                _r = _tk.Tk()
                _r.withdraw()
                _mb.showerror(tr("titulo"), tr("error_arranque") + "\n\n" + traceback.format_exc()[-1500:])
            except Exception:
                pass
        else:
            traceback.print_exc()
            input("\nERROR. Enter para cerrar...")
