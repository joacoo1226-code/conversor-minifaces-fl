# Conversor de minifaces – Football Life (FL Mod Studio)

🇪🇸 [Español](#-español) · 🇧🇷 [Português](#-português)

---

## 🇪🇸 Español

Minifaces de muchas ligas hechas con las fotos del Football Manager, y un **conversor** para que funcionen en **tu** mundo.

### ¿Por qué hace falta el conversor?
Cada mundo de FL Mod Studio usa **IDs distintos** para los jugadores. Si pegás las caras así nomás, en tu mundo no aparecen o le salen a otro jugador.
Por eso los packs vienen con el **ID del Football Manager**, y el conversor las pasa a los IDs de **tu** mundo.

### Cómo se usa
1. Bajá `Conversor de minifaces.exe` (en **Releases**, a la derecha) y los packs de las ligas que quieras (.zip, no hace falta descomprimirlos).
2. Abrí el conversor y elegí la carpeta de tu Football Life.
3. Agregá los packs → **Convertir** → **Instalar en el juego**. Listo.

Viene en español, portugués e inglés y tiene un tutorial adentro.

### ¿Qué hace exactamente?
- Busca a cada jugador de tu mundo en la lista del FM (por nombre y club) y le pone su ID.
- Copia las caras a `SiderAddons\livecpk\Minifaces FM` y las activa en `sider.ini`.
- Arregla `SiderAddons\modules\fl26world.txt` (pasa esos jugadores de `newfaces` a `newfaces3d`), porque si no el mundo tapa las minifaces con caras genéricas.

### Seguridad
- **No se conecta a internet**, no instala nada y solo toca la carpeta del juego que elegís.
- La primera vez guarda copia de `sider.ini` y `fl26world.txt` (`.antes_conversor` / `.antes_minifaces`) para volver atrás.
- Windows puede mostrar *"Windows protegió su PC"* porque es un programa casero sin firma digital: **Más información → Ejecutar de todas formas**.
- Algún antivirus puede marcarlo: es un falso positivo común en programas hechos con PyInstaller.
- El código está acá completo. Si preferís, corré `conversor_minifaces.py` con Python 3.10+ en vez del .exe (necesita `base_fm.json.gz` al lado).

### Archivos
| Archivo | Qué es |
|---|---|
| `conversor_minifaces.py` | El conversor (ventana, conversión e instalación) |
| `textos_conversor.py` | Textos en español, portugués e inglés |
| `bot_minifaces.py` | Funciones compartidas (lectura del mundo, cruce con el FM, arreglo del fl26world.txt) |
| `Armar conversor.bat` | Arma el .exe con PyInstaller |

---

## 🇧🇷 Português

Minifaces de várias ligas feitas com as fotos do Football Manager, e um **conversor** para que funcionem no **seu** mundo.

### Por que precisa do conversor?
Cada mundo do FL Mod Studio usa **IDs diferentes** para os jogadores. Se você colar as faces direto, elas não aparecem no seu mundo ou aparecem em outro jogador.
Por isso os packs vêm com o **ID do Football Manager**, e o conversor passa para os IDs do **seu** mundo.

### Como usar
1. Baixe o `Conversor de minifaces.exe` (em **Releases**, à direita) e os packs das ligas que quiser (.zip, não precisa descompactar).
2. Abra o conversor e escolha a pasta do seu Football Life.
3. Adicione os packs → **Converter** → **Instalar no jogo**. Pronto.

Vem em espanhol, português e inglês, com tutorial dentro.

### Segurança
- **Não se conecta à internet**, não instala nada e só mexe na pasta do jogo que você escolher.
- Na primeira vez faz cópia do `sider.ini` e do `fl26world.txt` para poder voltar atrás.
- O Windows pode mostrar *"O Windows protegeu o computador"* porque é um programa caseiro sem assinatura digital: **Mais informações → Executar assim mesmo**.
- Algum antivírus pode acusar: é um falso positivo comum em programas feitos com PyInstaller.
- O código está todo aqui. Se preferir, rode `conversor_minifaces.py` com Python 3.10+ em vez do .exe.
