"""Textos del Conversor de minifaces en español, portugués e inglés."""

IDIOMAS = {"es": "Español", "pt": "Português", "en": "English"}

TEXTOS = {
    # ---------------------------------------------------------------- ventana
    "titulo": {"es": "Conversor de minifaces", "pt": "Conversor de minifaces", "en": "Miniface Converter"},
    "sub": {"es": "packs con ID de FM  →  tu mundo de Football Life",
            "pt": "packs com ID do FM  →  seu mundo do Football Life",
            "en": "FM-ID packs  →  your Football Life world"},
    "ayuda": {"es": "¿Cómo se usa?", "pt": "Como usar?", "en": "How to use"},
    "paso1": {"es": "1  ·  TU JUEGO", "pt": "1  ·  SEU JOGO", "en": "1  ·  YOUR GAME"},
    "elegir_juego": {"es": "Elegir carpeta del juego...", "pt": "Escolher pasta do jogo...",
                     "en": "Choose game folder..."},
    "o_json": {"es": "o el fl26playerids.json...", "pt": "ou o fl26playerids.json...",
               "en": "or the fl26playerids.json..."},
    "paso2": {"es": "2  ·  PACKS DE MINIFACES (.zip con ID de FM)",
              "pt": "2  ·  PACKS DE MINIFACES (.zip com ID do FM)",
              "en": "2  ·  MINIFACE PACKS (.zip with FM IDs)"},
    "agregar_packs": {"es": "Agregar packs...", "pt": "Adicionar packs...", "en": "Add packs..."},
    "agregar_carpeta": {"es": "Agregar carpeta...", "pt": "Adicionar pasta...", "en": "Add folder..."},
    "quitar": {"es": "Quitar", "pt": "Remover", "en": "Remove"},
    "paso3": {"es": "3  ·  CONVERTIR E INSTALAR", "pt": "3  ·  CONVERTER E INSTALAR", "en": "3  ·  CONVERT AND INSTALL"},
    "paso3_texto": {
        "es": "Convertir: les pone el ID del PES de tu mundo y las deja en 'Minifaces para tu mundo'.\n"
              "Instalar: las copia al juego, las activa en sider.ini y arregla el fl26world.txt "
              "para que se vean (guarda copia de los originales).",
        "pt": "Converter: coloca o ID do PES do seu mundo e salva em 'Minifaces para tu mundo'.\n"
              "Instalar: copia para o jogo, ativa no sider.ini e ajusta o fl26world.txt "
              "para que apareçam (faz cópia dos originais).",
        "en": "Convert: gives them the PES IDs of your world and saves them in 'Minifaces para tu mundo'.\n"
              "Install: copies them to the game, enables them in sider.ini and fixes fl26world.txt "
              "so they show up (backs up the originals)."},
    "convertir": {"es": "Convertir", "pt": "Converter", "en": "Convert"},
    "instalar": {"es": "Instalar en el juego", "pt": "Instalar no jogo", "en": "Install in the game"},
    "abrir_carpeta": {"es": "Abrir carpeta", "pt": "Abrir pasta", "en": "Open folder"},
    "cancelar": {"es": "Cancelar", "pt": "Cancelar", "en": "Cancel"},
    "listo_empezar": {"es": "Listo para empezar.", "pt": "Pronto para começar.", "en": "Ready."},
    "mundo_info": {"es": "Mundo: {mundo}  ·  {ligas} ligas  ·  {jug} jugadores nuevos",
                   "pt": "Mundo: {mundo}  ·  {ligas} ligas  ·  {jug} jogadores novos",
                   "en": "World: {mundo}  ·  {ligas} leagues  ·  {jug} new players"},
    "mundo_error": {"es": "Mundo: {mundo}  (no pude leerlo: {e})", "pt": "Mundo: {mundo}  (não consegui ler: {e})",
                    "en": "World: {mundo}  (couldn't read it: {e})"},
    "juego_info": {"es": "Juego: {juego}", "pt": "Jogo: {juego}", "en": "Game: {juego}"},
    "sin_juego": {"es": "(no encontré el juego: para 'Instalar' te lo voy a pedir)",
                  "pt": "(não achei o jogo: vou pedir na hora de 'Instalar')",
                  "en": "(game folder not found: I'll ask for it when you 'Install')"},
    "elegi_juego": {"es": "Elegí la carpeta del juego (la que tiene SiderAddons).",
                    "pt": "Escolha a pasta do jogo (a que tem SiderAddons).",
                    "en": "Choose the game folder (the one with SiderAddons)."},
    "no_hay_mundo": {"es": "Ahí no encontré ningún mundo de FL Mod Studio (fl26playerids.json).\n\n"
                           "Elegí la carpeta del juego, la que tiene SiderAddons.",
                     "pt": "Não encontrei nenhum mundo do FL Mod Studio aí (fl26playerids.json).\n\n"
                           "Escolha a pasta do jogo, a que tem SiderAddons.",
                     "en": "No FL Mod Studio world found there (fl26playerids.json).\n\n"
                           "Choose the game folder, the one with SiderAddons."},
    "pack_item": {"es": "{nombre}   ({n} minifaces)", "pt": "{nombre}   ({n} minifaces)",
                  "en": "{nombre}   ({n} minifaces)"},
    "pack_vacio": {"es": "{nombre}   (¡no tiene minifaces!)", "pt": "{nombre}   (não tem minifaces!)",
                   "en": "{nombre}   (no minifaces inside!)"},
    "base_ok": {"es": "Lista del FM: OK", "pt": "Lista do FM: OK", "en": "FM list: OK"},
    "base_falta": {"es": "Lista del FM: NO ESTÁ (falta base_fm.json.gz)",
                   "pt": "Lista do FM: NÃO ENCONTRADA (falta base_fm.json.gz)",
                   "en": "FM list: MISSING (base_fm.json.gz not found)"},
    "dlg_juego": {"es": "Carpeta del juego (la que tiene SiderAddons)", "pt": "Pasta do jogo (a que tem SiderAddons)",
                  "en": "Game folder (the one with SiderAddons)"},
    "dlg_json": {"es": "fl26playerids.json de tu mundo", "pt": "fl26playerids.json do seu mundo",
                 "en": "fl26playerids.json of your world"},
    "dlg_packs": {"es": "Packs de minifaces (.zip)", "pt": "Packs de minifaces (.zip)", "en": "Miniface packs (.zip)"},
    "dlg_carpeta": {"es": "Carpeta con packs (.zip) o con minifaces <id_fm>.dds",
                    "pt": "Pasta com packs (.zip) ou com minifaces <id_fm>.dds",
                    "en": "Folder with packs (.zip) or with <fm_id>.dds minifaces"},
    "falta_juego": {"es": "Primero elegí la carpeta del juego (paso 1).",
                    "pt": "Primeiro escolha a pasta do jogo (passo 1).",
                    "en": "First choose the game folder (step 1)."},
    "falta_pack": {"es": "Agregá al menos un pack de minifaces (paso 2).",
                   "pt": "Adicione pelo menos um pack de minifaces (passo 2).",
                   "en": "Add at least one miniface pack (step 2)."},
    "falta_convertir": {"es": "Primero tocá 'Convertir'.", "pt": "Primeiro clique em 'Converter'.",
                        "en": "Click 'Convert' first."},
    "confirmar_instalar": {
        "es": "Voy a instalar las minifaces en:\n{juego}\n\n"
              "- copio la carpeta '{carpeta}' a SiderAddons\\livecpk\n"
              "- la activo en sider.ini (arriba de todo)\n"
              "- arreglo el fl26world.txt para que se vean\n\n"
              "Guardo copia de sider.ini y fl26world.txt la primera vez.  ¿Sigo?",
        "pt": "Vou instalar as minifaces em:\n{juego}\n\n"
              "- copio a pasta '{carpeta}' para SiderAddons\\livecpk\n"
              "- ativo no sider.ini (no topo)\n"
              "- ajusto o fl26world.txt para que apareçam\n\n"
              "Faço cópia do sider.ini e do fl26world.txt na primeira vez.  Continuar?",
        "en": "I'll install the minifaces in:\n{juego}\n\n"
              "- copy the '{carpeta}' folder to SiderAddons\\livecpk\n"
              "- enable it in sider.ini (at the top)\n"
              "- fix fl26world.txt so they show up\n\n"
              "sider.ini and fl26world.txt are backed up the first time.  Continue?"},
    "log_reconocidos": {"es": "Jugadores de tu mundo reconocidos en el FM: {n} de {t}",
                        "pt": "Jogadores do seu mundo reconhecidos no FM: {n} de {t}",
                        "en": "Players of your world found in FM: {n} of {t}"},
    "log_puestas": {"es": "Minifaces puestas ahora: {n}  |  total en la carpeta: {t}",
                    "pt": "Minifaces colocadas agora: {n}  |  total na pasta: {t}",
                    "en": "Minifaces done now: {n}  |  total in the folder: {t}"},
    "fin_conv_titulo": {"es": "¡Convertido!", "pt": "Convertido!", "en": "Converted!"},
    "fin_conv": {"es": "Minifaces para tu mundo: {n}\n\n{detalle}\n\n(Un pack trae todo el plantel del FM: "
                       "los que no están en tu mundo se saltean.)\n\n¿Las instalo en el juego ahora?",
                 "pt": "Minifaces para o seu mundo: {n}\n\n{detalle}\n\n(Um pack traz o elenco inteiro do FM: "
                       "os que não estão no seu mundo são ignorados.)\n\nInstalar no jogo agora?",
                 "en": "Minifaces for your world: {n}\n\n{detalle}\n\n(A pack has the whole FM squad: "
                       "players not in your world are skipped.)\n\nInstall them in the game now?"},
    "mas_packs": {"es": "  ... y {n} packs más", "pt": "  ... e mais {n} packs", "en": "  ... and {n} more packs"},
    "de": {"es": "{p} de {t}", "pt": "{p} de {t}", "en": "{p} of {t}"},
    "ini_agregada": {"es": "agregada la carpeta", "pt": "pasta adicionada", "en": "folder added"},
    "ini_estaba": {"es": "ya estaba", "pt": "já estava", "en": "already there"},
    "log_instalado": {"es": "Copiadas al juego: {n}  |  sider.ini: {ini}  |  activadas en el mundo ahora: {m}",
                      "pt": "Copiadas para o jogo: {n}  |  sider.ini: {ini}  |  ativadas no mundo agora: {m}",
                      "en": "Copied to the game: {n}  |  sider.ini: {ini}  |  enabled in the world now: {m}"},
    "fin_inst_titulo": {"es": "¡Instalado!", "pt": "Instalado!", "en": "Installed!"},
    "fin_inst": {"es": "Minifaces copiadas al juego: {n}\nJugadores del mundo que ahora muestran su miniface: {m}\n\n"
                       "Abrí el juego y fijate.\n\nSi reinstalás o rearmás el mundo, volvé a tocar 'Instalar en el juego'.",
                 "pt": "Minifaces copiadas para o jogo: {n}\nJogadores do mundo que agora mostram a miniface: {m}\n\n"
                       "Abra o jogo e confira.\n\nSe reinstalar ou refizer o mundo, clique de novo em 'Instalar no jogo'.",
                 "en": "Minifaces copied to the game: {n}\nWorld players now showing their miniface: {m}\n\n"
                       "Open the game and check.\n\nIf you reinstall or rebuild the world, click 'Install in the game' again."},
    "cancelado": {"es": "Cancelado.", "pt": "Cancelado.", "en": "Cancelled."},
    "error_estado": {"es": "Error (mirá el registro)", "pt": "Erro (veja o registro)", "en": "Error (see the log)"},
    "error": {"es": "Error", "pt": "Erro", "en": "Error"},
    "error_arranque": {"es": "Error al arrancar:", "pt": "Erro ao iniciar:", "en": "Startup error:"},
    "ocupado": {"es": "Esperá a que termine lo que está haciendo.", "pt": "Espere terminar o que está fazendo.",
                "en": "Wait until the current task finishes."},
    # ---------------------------------------------------------------- mensajes del trabajo
    "cache": {"es": "Usando el cruce que ya estaba hecho para este mundo",
              "pt": "Usando o cruzamento já feito para este mundo",
              "en": "Using the saved matching for this world"},
    "cargando_fm": {"es": "Cargando la lista del Football Manager...", "pt": "Carregando a lista do Football Manager...",
                    "en": "Loading the Football Manager list..."},
    "preparando": {"es": "Preparando la lista del Football Manager...", "pt": "Preparando a lista do Football Manager...",
                   "en": "Preparing the Football Manager list..."},
    "cruzando": {"es": "Cruzando {liga}...", "pt": "Cruzando {liga}...", "en": "Matching {liga}..."},
    "revisando": {"es": "Revisando carpetas activas: {k} de {n}", "pt": "Verificando pastas ativas: {k} de {n}",
                  "en": "Checking active folders: {k} of {n}"},
    "encontradas_en": {"es": "  {c}: minifaces encontradas", "pt": "  {c}: minifaces encontradas",
                       "en": "  {c}: minifaces found"},
    "borre_otro": {"es": "Borré las minifaces convertidas antes para otro mundo.",
                   "pt": "Apaguei as minifaces convertidas antes para outro mundo.",
                   "en": "Deleted the minifaces converted earlier for another world."},
    "progreso_pack": {"es": "{nombre}: {i} de {n}", "pt": "{nombre}: {i} de {n}", "en": "{nombre}: {i} of {n}"},
    "resumen_pack": {"es": "  {nombre}: {n} de {t} son jugadores de tu mundo",
                     "pt": "  {nombre}: {n} de {t} são jogadores do seu mundo",
                     "en": "  {nombre}: {n} of {t} are players of your world"},
    "listo": {"es": "¡Listo!", "pt": "Pronto!", "en": "Done!"},
    "copiando": {"es": "Copiando al juego: {k} de {n}", "pt": "Copiando para o jogo: {k} de {n}",
                 "en": "Copying to the game: {k} of {n}"},
    "arreglando": {"es": "Arreglando el fl26world.txt...", "pt": "Ajustando o fl26world.txt...",
                   "en": "Fixing fl26world.txt..."},
    "instalado": {"es": "¡Instalado!", "pt": "Instalado!", "en": "Installed!"},
    # ---------------------------------------------------------------- errores
    "err_base": {"es": "Falta la lista del FM (base_fm.json.gz). Pedile el conversor completo a quien te lo pasó.",
                 "pt": "Falta a lista do FM (base_fm.json.gz). Peça o conversor completo para quem te passou.",
                 "en": "The FM list (base_fm.json.gz) is missing. Ask for the full converter from whoever gave it to you."},
    "err_ninguno": {"es": "No pude reconocer a ningún jugador de tu mundo en la lista del FM.",
                    "pt": "Não reconheci nenhum jogador do seu mundo na lista do FM.",
                    "en": "Couldn't find any player of your world in the FM list."},
    "err_sider": {"es": "En esa carpeta no encontré SiderAddons\\sider.ini.",
                  "pt": "Não encontrei SiderAddons\\sider.ini nessa pasta.",
                  "en": "SiderAddons\\sider.ini not found in that folder."},
    "err_world": {"es": "No hay SiderAddons\\modules\\fl26world.txt: no tenés un mundo de FL Mod Studio instalado.",
                  "pt": "Não existe SiderAddons\\modules\\fl26world.txt: você não tem um mundo do FL Mod Studio instalado.",
                  "en": "SiderAddons\\modules\\fl26world.txt is missing: no FL Mod Studio world is installed."},
    "err_cpk": {"es": "El sider.ini no tiene ninguna línea cpk.root: ¿es el sider.ini del Football Life?",
                "pt": "O sider.ini não tem nenhuma linha cpk.root: é o sider.ini do Football Life?",
                "en": "sider.ini has no cpk.root line: is it the Football Life sider.ini?"},
    # ---------------------------------------------------------------- LEEME de la carpeta de salida
    "leeme": {
        "es": "Minifaces para el mundo: {mundo}\n({n} jugadores)\n\n"
              "Lo más fácil: en el Conversor tocá 'Instalar en el juego'.\n\nA mano:\n"
              "1) Copiá la carpeta '{carpeta}' a ...\\SiderAddons\\livecpk\\\n"
              "2) En sider.ini, arriba de todo: cpk.root = \".\\livecpk\\{carpeta}\"\n"
              "3) Pasá estos jugadores de 'newfaces' a 'newfaces3d' en SiderAddons\\modules\\fl26world.txt\n"
              "   (el Conversor lo hace solo con 'Instalar en el juego').\n",
        "pt": "Minifaces para o mundo: {mundo}\n({n} jogadores)\n\n"
              "O mais fácil: no Conversor clique em 'Instalar no jogo'.\n\nNa mão:\n"
              "1) Copie a pasta '{carpeta}' para ...\\SiderAddons\\livecpk\\\n"
              "2) No sider.ini, no topo: cpk.root = \".\\livecpk\\{carpeta}\"\n"
              "3) Passe esses jogadores de 'newfaces' para 'newfaces3d' em SiderAddons\\modules\\fl26world.txt\n"
              "   (o Conversor faz isso sozinho com 'Instalar no jogo').\n",
        "en": "Minifaces for the world: {mundo}\n({n} players)\n\n"
              "Easiest: in the Converter click 'Install in the game'.\n\nBy hand:\n"
              "1) Copy the '{carpeta}' folder to ...\\SiderAddons\\livecpk\\\n"
              "2) In sider.ini, at the top: cpk.root = \".\\livecpk\\{carpeta}\"\n"
              "3) Move these players from 'newfaces' to 'newfaces3d' in SiderAddons\\modules\\fl26world.txt\n"
              "   (the Converter does it for you with 'Install in the game').\n"},
    # ---------------------------------------------------------------- tutorial
    "tuto_titulo": {"es": "Cómo se usa", "pt": "Como usar", "en": "How to use"},
    "tuto": {
        "es": [("1", "Elegí tu juego",
                "Tocá 'Elegir carpeta del juego' y elegí la carpeta de tu Football Life (la que tiene SiderAddons). "
                "La app encuentra sola tu mundo de FL Mod Studio."),
               ("2", "Agregá los packs",
                "Tocá 'Agregar packs' y elegí los .zip de minifaces que bajaste "
                "(por ejemplo 'Minifaces FM - 2. Bundesliga.zip'). No hace falta descomprimirlos."),
               ("3", "Convertí e instalá",
                "Tocá 'Convertir' y después 'Instalar en el juego'. Abrí el juego y listo.")],
        "pt": [("1", "Escolha seu jogo",
                "Clique em 'Escolher pasta do jogo' e escolha a pasta do seu Football Life (a que tem SiderAddons). "
                "O app encontra sozinho o seu mundo do FL Mod Studio."),
               ("2", "Adicione os packs",
                "Clique em 'Adicionar packs' e escolha os .zip de minifaces que você baixou "
                "(por exemplo 'Minifaces FM - 2. Bundesliga.zip'). Não precisa descompactar."),
               ("3", "Converta e instale",
                "Clique em 'Converter' e depois em 'Instalar no jogo'. Abra o jogo e pronto.")],
        "en": [("1", "Choose your game",
                "Click 'Choose game folder' and pick your Football Life folder (the one with SiderAddons). "
                "The app finds your FL Mod Studio world by itself."),
               ("2", "Add the packs",
                "Click 'Add packs' and pick the miniface .zip files you downloaded "
                "(e.g. 'Minifaces FM - 2. Bundesliga.zip'). No need to unzip them."),
               ("3", "Convert and install",
                "Click 'Convert' and then 'Install in the game'. Open the game and you're done.")]},
    "tuto_archivos": {
        "es": "Qué necesitás:  un mundo de FL Mod Studio instalado y los packs .zip con ID de FM "
              "(los packs comunes con IDs del PES no sirven).\n"
              "Si reinstalás o rearmás el mundo, volvé a tocar 'Instalar en el juego'.",
        "pt": "O que você precisa:  um mundo do FL Mod Studio instalado e os packs .zip com ID do FM "
              "(packs comuns com IDs do PES não servem).\n"
              "Se reinstalar ou refizer o mundo, clique de novo em 'Instalar no jogo'.",
        "en": "What you need:  an installed FL Mod Studio world and the .zip packs with FM IDs "
              "(regular packs with PES IDs won't work).\n"
              "If you reinstall or rebuild the world, click 'Install in the game' again."},
    "entendido": {"es": "Entendido", "pt": "Entendi", "en": "Got it"},
}
