# 🛡️ Zelda Multi-Launcher Hub v2.1 (Premium Edition)

[Français](#-version-française) | [English](#-english-version)

---

## 🇫🇷 Version Française

Ce projet est un hub centralisé qui automatise le lancement de vos jeux (Natif ou Émulés), la gestion de vos manettes, votre tracking (PopTracker) et vos connexions Archipelago.

---

### 🔍 Analyse du Fonctionnement (Comment ça marche ?)

Le Zelda Hub repose sur une architecture en trois couches principales :

#### 1. Le Cœur de Lancement (`launcher_core.py`)

C'est le "moteur" du Hub. Il gère l'interaction directe avec les processus Windows :

- **Contrôleurs d'Émulateurs** : Des classes dédiées pour **BizHawk**, **Dolphin**, **MelonDS**, **Azahar**, **RetroArch** et les jeux **Natifs** (Ship of Harkinian, Majora's Mask).
- **Fermeture Robuste (Strate par Strate)** : Pour éviter que les émulateurs ne corrompent vos sauvegardes, le Hub utilise une fermeture intelligente :
  1.  **Signal Lua (BizHawk)** : Envoie une commande `client.exit()` via un script temporaire pour une fermeture parfaite.
  2.  **WM_CLOSE** : Tente une fermeture standard propre.
  3.  **TaskKill (Force)** : Dernier recours si le processus est "gelé".
- **Focus Automatique** : Force la fenêtre du jeu au premier plan au démarrage pour vous éviter de devoir cliquer dessus.

#### 2. Le Gestionnaire de Manettes (`controller/`)

Le Hub ne se contente pas de lancer le jeu, il prépare aussi votre matériel :

- **Profilage Dynamique** : Quand vous lancez Ocarina of Time, le Hub charge le fichier `oot.json`. Quand vous passez sur Wind Waker, il charge `ww.json`.
- **Mapping Direct** : Le système communique avec les émulateurs pour adapter les boutons à la volée selon le jeu sélectionné.

#### 3. L'Interface Premium (`ui_main_v2.py`)

L'interface utilisateur (UI) est construite avec **CustomTkinter** pour un rendu moderne (Bleu Saphir et Dark Mode) :

- **Dashboard à Cartes** : Chaque jeu a sa "carte" avec sa jaquette, permettant d'activer/désactiver le tracker ou l'auto-config manette avant le lancement.
- **Quick Switcher (V1 Engine + V2 Look)** : Un menu flottant ( accessible à la manette) qui permet de changer de jeu sans jamais toucher au clavier ni à la souris.
- **OBS Integration** : Utilise `obs-websocket` pour changer automatiquement vos scènes de stream dès qu'un jeu est lancé.

---

### 🏗️ Guide d'Installation & Configuration

Suivez attentivement ces étapes pour garantir le bon fonctionnement de l'ensemble du système.

#### 1️⃣ Installation & Prérequis

- **Python 3.10+** : Installez-le et installez les dépendances :
  ```powershell
  pip install customtkinter Pillow psutil pywin32 keyboard obs-websocket-py
  ```
- **Archipelago (Obligatoire)** : Téléchargez et installez la dernière version de **Archipelago**.

#### 2️⃣ Configuration Archipelago

Pour que le Hub puisse communiquer avec vos parties Multi-mondes :

1.  **APWorlds** : Ajoutez tous les fichiers `.apworld` correspondants à vos jeux Zelda dans votre dossier Archipelago.
2.  **Génération YAML** : Utilisez le bouton de génération pour créer vos fichiers de configuration (`.yaml`).
3.  **Slot Names** : Ouvrez vos fichiers YAML et changez les **noms des slots** (ex: remplacez "Player1" par un pseudo unique).
4.  **Hébergement** : Générez votre partie sur le site Archipelago ou hébergez le serveur localement.

#### 📦 Liens Utiles APWorlds
Si vous n'avez pas encore les fichiers `.apworld`, voici où les trouver :
- **Soh Ocarina of Time** : [GitHub Releases](https://github.com/HarbourMasters/Archipelago-SoH/releases)
- **Ocarina of Time** : Déjà inclus par défaut
- **Majora's Mask** : [GitHub Releases](https://github.com/RecompRando/MMRecompRando/releases)
- **Twilight Princess** : [GitHub Releases](https://github.com/WritingHusky/Twilight_Princess_apworld/releases)
- **Wind Waker** : Déjà inclus par défaut
- **Skyward Sword** : [GitHub Releases](https://github.com/Battlecats59/SS_APWorld/releases)
- **Zelda 1** : Déjà inclus par défaut
- **Zelda 2** : [GitHub Releases](https://github.com/PinkSwitch/Archipelago/releases?q=zelda&expanded=true)
- **Oracle of Ages** : [Dernière Release](https://github.com/SenPierre/ArchipelagoOoA/releases/latest)
- **Oracle of Seasons** : [Dernière Release](https://github.com/Dinopony/ArchipelagoOoS/releases/latest)
- **Link's Awakening DX** : Déjà inclus par défaut
- **A Link Between Worlds** : [GitHub Releases](https://github.com/randomsalience/albw-archipelago/releases)
- **A Link to the Past** : Déjà inclus par défaut
- **Minish Cap** : [GitHub Releases](https://github.com/eternalcode0/Archipelago/releases)
- **Phantom Hourglass** : [GitHub Releases](https://github.com/carrotinator/Archipelago/releases)
- **Spirit Tracks** : [GitHub Releases](https://github.com/DayKat/spirit-tracks/releases)

#### 3️⃣ Configuration du Zelda Hub

Lancez Zelda-Hub.exe et configurez les onglets suivants via le bouton **⚙️ Chemins Install** :

- **Tab Archipelago** : Insérez les noms des slots (ceux définis dans vos YAML) pour chaque jeu.
- **Tab Connexion AP** : Renseignez l'adresse du serveur (ex: `archipelago.gg:12345`) et le mot de passe si nécessaire.
- **Tab Émulateurs** : Renseignez les chemins vers vos émulateurs (`BizHawk.exe`, `Dolphin.exe`, etc.) ainsi que le chemin vers votre installation de **Archipelago**.

#### 4️⃣ Préparation des ROMs (Extraction & Patch)

_Les ROMs ne sont pas fournies avec le Hub. Vous devez posséder les versions originales des jeux._

1.  **Préparation** : Décompressez le dossier du monde (Zip) que vous avez généré sur Archipelago.
2.  **Extracteur** : Ouvrez l'outil d'extraction dans `Extractor/patcher.exe`.
3.  **Chemins** : Dans l'extracteur, configurez :
    - Le chemin vers `ArchipelagoLauncher.exe`.
    - Le dossier contenant vos fichiers de patch (`.apml`, `.apzs`, etc.).
4.  **Extraction** : Actualisez la liste et vérifiez si les patchs sont trouvés (sinon, lancez vos patchs manuellement un par un). Lancez ensuite l'**Extraction Totale**.
5.  **Finalisation** : Une fois les ROMs générées, déplacez-les (le fichier ROM, pas le patch) dans le dossier **PatchFile** de votre Hub.

#### 5️⃣ PopTracker (Base)

Dans les paramètres du Hub, indiquez le chemin vers `poptracker.exe` pour que le tracking automatique fonctionne au lancement d'un jeu.

#### 6️⃣ PopTracker (Configuration des Packs)

Pour une automatisation totale du tracking :

1.  **Chemins des Packs** : Dans l'onglet PopTracker du Hub, vous devez renseigner le chemin vers le dossier de chaque pack spécifique à vos jeux.
2.  **Sélection des Modes** : Choisissez le mode/variante que vous souhaitez lancer par défaut pour chaque titre.
3.  **Priorité Archipelago** : Il est fortement conseillé de **prioriser les modes avec "AP"** (ex: `Items & Locations (AP)`) pour permettre la connexion automatique au serveur au démarrage du jeu.

#### 7️⃣ Mode Streamer (Intégration OBS)

Le Hub peut piloter OBS pour vous simplifier la vie en plein stream :

1.  **Activation** : Dans l'onglet **Streaming**, cochez la case "Activer la synchronisation OBS".
2.  **Connexion** : Renseignez le **Port WebSocket** (généralement `4455`) et le **mot de passe** configurés dans OBS (Menu Outils > Paramètres de serveur WebSocket).
3.  **Test** : Utilisez le bouton de test pour vérifier que le Hub arrive bien à communiquer avec votre OBS.
4.  **Configuration des Scènes** : Pour chaque jeu, vous pouvez définir le nom de la scène à laquelle OBS doit passer automatiquement. Vous pouvez personnaliser ces noms directement dans la liste de l'onglet Streaming.

#### 8️⃣ Tracker Spécial Skyward Sword (Web)

Ce tracker fonctionne différemment car il nécessite un hébergement web local (automatisé par le Hub via Vite).

- **Mode Streamer** : Si vous utilisez OBS, vous pouvez intégrer différentes pages du tracker en tant que "Source Navigateur" pour vos scènes :
  - URL type : `http://localhost:5173/#/items?ip=ADRESSE_IP&port=PORT_AP&slot=NOM_SLOT&autolaunch=true`
  - **Vues disponibles** : Vous pouvez remplacer `/items` dans l'URL par l'une des vues suivantes selon vos besoins : `items`, `map`, `locations`, `chat`, `dungeons`, ou `counters`.
- **Installation** : Assurez-vous que le dossier du tracker est bien sélectionné dans l'onglet **Trackers** du Setup. Le Hub s'occupera de lancer le serveur `npm start` et d'installer les dépendances au premier lancement.

---

### 🕹️ Contrôles du Quick Switcher

Le **Quick Switcher** est accessible via le raccourci clavier `Ctrl+Shift+S` ou via le bouton **"Hub"** configuré sur votre manette.

| Action               | Manette                      | Clavier            |
| :------------------- | :--------------------------- | :----------------- |
| **Ouvrir/Fermer**    | Bouton Central (Guide)       | `Ctrl + Shift + S` |
| **Sélectionner**     | Stick Gauche / D-Pad Up/Down | Flèches Haut/Bas   |
| **Valider (Lancer)** | Bouton A (Face Bas)          | Entrée             |
| **Annuler**          | Bouton B (Face Droite)       | Echap              |

---

### 📂 Organisation des Fichiers

- `python_src/` : Code source Python.
- `python_src/controller/profiles/` : Fichiers JSON contenant vos mappings par jeu.
- `python_src/assets/images/` : Jaquettes des jeux affichées sur le Dashboard.
- `config.json` : Stocke tous vos réglages, chemins et préférences.

---

<br>

---

## 🇺🇸 English Version

This project is a centralized hub that automates launching your games (Native or Emulated), managing your controllers, tracking your progress (PopTracker), and handling your Archipelago connections.

---

### 🔍 Functional Analysis (How it works?)

The Zelda Hub is built on a three-layer architecture:

#### 1. The Launch Core (`launcher_core.py`)

This is the "engine" of the Hub. It manages direct interactions with Windows processes:

- **Emulator Controllers**: Dedicated classes for **BizHawk**, **Dolphin**, **MelonDS**, **Azahar**, **RetroArch**, and **Native** games (Ship of Harkinian, Majora's Mask).
- **Robust Closing (Layer by Layer)**: To prevent emulators from corrupting your saves, the Hub uses an intelligent closing system:
  1.  **Lua Signal (BizHawk)**: Sends a `client.exit()` command via a temporary script for a perfect shutdown.
  2.  **WM_CLOSE**: Attempts a standard clean close.
  3.  **TaskKill (Force)**: A last resort if the process is "frozen".
- **Automatic Focus**: Forces the game window to the foreground on startup so you don't have to manually click it.

#### 2. The Controller Manager (`controller/`)

The Hub doesn't just launch the game; it also prepares your hardware:

- **Dynamic Profiling**: When you launch Ocarina of Time, the Hub loads the `oot.json` file. When you switch to Wind Waker, it loads `ww.json`.
- **Direct Mapping**: The system communicates with emulators to adapt buttons on the fly based on the selected game.

#### 3. The Premium Interface (`ui_main_v2.py`)

The user interface (UI) is built with **CustomTkinter** for a modern look (Sapphire Blue and Dark Mode):

- **Card Dashboard**: Each game has its "card" with its box art, allowing you to toggle the tracker or controller auto-config before launching.
- **Quick Switcher (V1 Engine + V2 Look)**: A floating menu (accessible via controller) that lets you switch games without touching the keyboard or mouse.
- **OBS Integration**: Uses `obs-websocket` to automatically change your stream scenes as soon as a game is launched.

---

### 🏗️ Installation & Configuration Guide

Follow these steps carefully to ensure the entire system works correctly.

#### 1️⃣ Installation & Prerequisites

- **Python 3.10+**: Install it and then install the dependencies:
  ```powershell
  pip install customtkinter Pillow psutil pywin32 keyboard obs-websocket-py
  ```
- **Archipelago (Required)**: Download and install the latest version of **Archipelago**.

#### 2️⃣ Archipelago Configuration

For the Hub to communicate with your Multiworld games:

1.  **APWorlds**: Add all `.apworld` files corresponding to your Zelda games to your Archipelago folder.
2.  **YAML Generation**: Use the generation button to create your configuration files (`.yaml`).
3.  **Slot Names**: Open your YAML files and change the **slot names** (e.g., replace "Player1" with a unique nickname/handle).
4.  **Hosting**: Generate your game on the Archipelago website or host the server locally.

#### 📦 Useful APWorld Links
If you don't have the `.apworld` files yet, here is where to find them:
- **Soh Ocarina of Time**: [GitHub Releases](https://github.com/HarbourMasters/Archipelago-SoH/releases)
- **Ocarina of Time**: Already included by default
- **Majora's Mask**: [GitHub Releases](https://github.com/RecompRando/MMRecompRando/releases)
- **Twilight Princess**: [GitHub Releases](https://github.com/WritingHusky/Twilight_Princess_apworld/releases)
- **Wind Waker**: Already included by default
- **Skyward Sword**: [GitHub Releases](https://github.com/Battlecats59/SS_APWorld/releases)
- **Zelda 1**: Already included by default
- **Zelda 2**: [GitHub Releases](https://github.com/PinkSwitch/Archipelago/releases?q=zelda&expanded=true)
- **Oracle of Ages**: [Latest Release](https://github.com/SenPierre/ArchipelagoOoA/releases/latest)
- **Oracle of Seasons**: [Latest Release](https://github.com/Dinopony/ArchipelagoOoS/releases/latest)
- **Link's Awakening DX**: Already included by default
- **A Link Between Worlds**: [GitHub Releases](https://github.com/randomsalience/albw-archipelago/releases)
- **A Link to the Past**: Already included by default
- **Minish Cap**: [GitHub Releases](https://github.com/eternalcode0/Archipelago/releases)
- **Phantom Hourglass**: [GitHub Releases](https://github.com/carrotinator/Archipelago/releases)
- **Spirit Tracks**: [GitHub Releases](https://github.com/DayKat/spirit-tracks/releases)

#### 3️⃣ Zelda Hub Configuration

Run `python python_src/ui_main_v2.py` and configure the following tabs via the **⚙️ Install Paths** button:

- **Archipelago Tab**: Enter the slot names (defined in your YAMLs) for each game.
- **AP Connection Tab**: Enter the server address (e.g., `archipelago.gg:12345`) and password if necessary.
- **Emulators Tab**: Enter the paths to your emulators (`BizHawk.exe`, `Dolphin.exe`, etc.) as well as the path to your **Archipelago** installation.

#### 4️⃣ ROM Preparation (Extraction & Patch)

_ROMs are not provided with the Hub. You must own the original versions of the games._

1.  **Preparation**: Unzip the world folder (Zip) generated on Archipelago.
2.  **Extractor**: Open the extraction tool in `Extractor/patcher.exe`.
3.  **Paths**: In the extractor, configure:
    - The path to `ArchipelagoLauncher.exe`.
    - The folder containing your patch files (`.apml`, `.apzs`, etc.).
4.  **Extraction**: Refresh the list and check if patches are found (if not, apply your patches manually one by one). Then run the **Full Extraction**.
5.  **Finalization**: Once the ROMs are generated, move them (the ROM file, not the patch) into your Hub's **PatchFile** folder.

#### 5️⃣ PopTracker (Base)

In the Hub settings, specify the path to `poptracker.exe` so that automatic tracking works when a game is launched.

#### 6️⃣ PopTracker (Pack Configuration)

For total tracking automation:

1.  **Pack Paths**: In the Hub's PopTracker tab, enter the path to each specific pack folder for your games.
2.  **Mode Selection**: Choose the mode/variant you want to launch by default for each title.
3.  **Archipelago Priority**: It is strongly recommended to **prioritize modes with "AP"** (e.g., `Items & Locations (AP)`) to allow automatic server connection when the game starts.

#### 7️⃣ Streamer Mode (OBS Integration)

The Hub can control OBS to simplify your streaming workflow:

1.  **Activation**: In the **Streaming** tab, check the "Enable OBS Synchronization" box.
2.  **Connection**: Enter the **WebSocket Port** (usually `4455`) and the **password** configured in OBS (Tools Menu > WebSocket Server Settings).
3.  **Test**: Use the test button to check if the Hub can communicate with your OBS instance.
4.  **Scene Configuration**: For each game, you can define the name of the scene OBS should automatically switch to. You can customize these names directly in the Streaming tab list.

#### 8️⃣ Special Skyward Sword Tracker (Web)

This tracker operates differently as it requires local web hosting (automated by the Hub via Vite).

- **Streamer Mode**: For OBS users, you can integrate various tracker pages as a "Browser Source" in your scenes:
  - Sample URL: `http://localhost:5173/#/items?ip=IP_ADDRESS&port=AP_PORT&slot=SLOT_NAME&autolaunch=true`
  - **Available Views**: You can replace `/items` in the URL with any of the following views: `items`, `map`, `locations`, `chat`, `dungeons`, or `counters`.
- **Setup**: Ensure the tracker's folder is selected in the **Trackers** tab of the Setup. The Hub will automatically run `npm start` and install dependencies on the first launch.

---

### 🕹️ Quick Switcher Controls

The **Quick Switcher** is accessible via the keyboard shortcut `Ctrl+Shift+S` or via the **"Hub"** button configured on your controller.

| Action               | Controller                 | Keyboard           |
| :------------------- | :------------------------- | :----------------- |
| **Open/Close**       | Central Button (Guide)     | `Ctrl + Shift + S` |
| **Select**           | Left Stick / D-Pad Up/Down | Up/Down Arrow Keys |
| **Confirm (Launch)** | A Button (Face Down)       | Enter              |
| **Cancel**           | B Button (Face Right)      | Escape             |

---

### 📂 File Organization

- `python_src/`: Python source code.
- `python_src/controller/profiles/`: JSON files containing your per-game mappings.
- `python_src/assets/images/`: Game box arts displayed on the Dashboard.
- `config.json`: Stores all your settings, paths, and preferences.

---
