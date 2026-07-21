# 🛡️ Zelda Multi-Launcher Hub v2.1 (Premium Edition)

[Français](#-version-française) | [English](#-english-version)

---

## 🇫🇷 Version Française

Ce projet est un hub centralisé qui automatise le lancement de vos jeux (Natif ou Émulés), votre tracking (PopTracker) et vos connexions Archipelago.

---

### 🔍 Analyse du Fonctionnement (Comment ça marche ?)

Le Zelda Hub repose sur une architecture en deux couches principales :

#### 1. Le Cœur de Lancement (`launcher_core.py`)

C'est le "moteur" du Hub. Il gère l'interaction directe avec les processus Windows :

- **Contrôleurs d'Émulateurs** : Des classes dédiées pour **BizHawk**, **Dolphin**, **MelonDS**, **Azahar**, **RetroArch**, **Cemu** et les jeux **Natifs/PC** (Ship of Harkinian, Majora's Mask, Zelda's Adventure).
- **Fermeture Robuste (Strate par Strate)** : Pour éviter que les émulateurs ne corrompent vos sauvegardes, le Hub utilise une fermeture intelligente :
  1.  **Signal Lua (BizHawk)** : Envoie une commande `client.exit()` via un script temporaire pour une fermeture parfaite.
  2.  **WM_CLOSE** : Tente une fermeture standard propre.
  3.  **TaskKill (Force)** : Dernier recours si le processus est "gelé".
- **Focus Automatique** : Force la fenêtre du jeu au premier plan au démarrage pour vous éviter de devoir cliquer dessus.

#### 2. L'Interface Premium (`ui_main_v2.py`)

L'interface utilisateur (UI) est construite avec **CustomTkinter** pour un rendu moderne (Bleu Saphir et Dark Mode) :

- **Dashboard à Cartes** : Chaque jeu a sa "carte" avec sa jaquette, permettant d'activer/désactiver le tracker avant le lancement.
- **Quick Switcher (V1 Engine + V2 Look)** : Un menu flottant ( accessible à la manette) qui permet de changer de jeu sans jamais toucher au clavier ni à la souris.
- **OBS Integration** : Utilise `obs-websocket` pour changer automatiquement vos scènes de stream dès qu'un jeu est lancé.

---

### 🏗️ Guide d'Installation & Configuration

Suivez attentivement ces étapes pour garantir le bon fonctionnement de l'ensemble du système.

#### 1️⃣ Installation & Prérequis

- **Python 3.12** : [Téléchargez et installez Python 3.12](https://www.python.org/downloads/). _Important : Cochez bien la case "Add Python to PATH" lors de l'installation._
- **Node.js** : [Téléchargez et installez Node.js](https://nodejs.org/). (Nécessaire pour le fonctionnement des trackers web).
- **Scripts d'installation** : Une fois les prérequis installés, allez dans le dossier `scripts/` et lancez **`INSTALL_ALL.bat`**. Ce script s'occupera d'installer toutes les dépendances Python et Node pour vous.
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
- **Link's Awakening DX Beta** : [GitHub Releases](https://github.com/threeandthreee/Archipelago/releases)
- **A Link Between Worlds** : [GitHub Releases](https://github.com/randomsalience/albw-archipelago/releases)
- **A Link to the Past** : Déjà inclus par défaut
- **A Link to the Past OWR** : [GitHub Releases](https://github.com/aurabot24/Archipelago-ALttPR/releases/)
- **Minish Cap** : [GitHub Releases](https://github.com/eternalcode0/Archipelago/releases)
- **Phantom Hourglass** : [GitHub Releases](https://github.com/carrotinator/Archipelago/releases)
- **Spirit Tracks** : [GitHub Releases](https://github.com/DayKat/spirit-tracks/releases)
- **Zelda's Adventure** : [GitHub Releases](https://github.com/nebbii/za-gdx/releases)



#### 📦 Liens PopTracker
Pour profiter du tracking automatique, voici les packs recommandés pour chaque jeu. **Note : Il est vivement recommandé de rejoindre les discords des différentes communautés pour avoir les dernières versions à jour.**

- **Soh Ocarina of Time** : [GitHub Releases](https://github.com/Brian0255/ship-of-harkinian-ap-tracker/releases)
- **Ocarina of Time** : [GitHub Releases](https://github.com/StripesOO7/oot-tracker/releases)
- **Majora's Mask** : [GitHub Releases](https://github.com/G4M3RL1F3/Majoras-Mask-AP-PopTracker-Pack/releases)
- **Twilight Princess** : [GitHub Releases](https://github.com/Kizugaya/TPRAP_poptracker/releases)
- **Wind Waker** : [GitHub Releases](https://github.com/Mysteryem/ww-poptracker/releases/tag/v1.3.0)
- **Zelda 1** : [GitHub Releases](https://github.com/Br00ty/tloz_brooty/releases)
- **Zelda 2, Adventure of Link** : [GitHub Releases](https://github.com/palex00/zelda-2-ap-tracker/releases/latest/)
- **Oracle of Ages** : [GitHub Releases](https://github.com/Dranzior/ooa_brooty/releases)
- **Oracle of Seasons** : [GitHub Releases](https://github.com/OmegaZeron/Oracle-of-Seasons-AP-Poptracker-Pack/releases/latest)
- **Link's Awakening DX** : [Magpie Tracker](https://magpietracker.us/)
- **Link's Awakening DX Beta** : [Magpie Tracker](https://magpietracker.us/)
- **A Link Between Worlds** : [GitHub Releases](https://github.com/Legendgreat/albw-ap-poptracker/releases)
- **A Link to the Past** : [GitHub Releases](https://github.com/StripesOO7/alttp-ap-poptracker-pack/releases)
- **Minish Cap** : [GitHub Releases](https://github.com/deoxis9001/tmcrando_maptracker_deoxis/releases)
- **Phantom Hourglass** : [GitHub Repo](https://github.com/ZobeePlays/PH-AP-Item-Tracker/tree/main)
- **Spirit Tracks** : [GitHub Repo](https://github.com/carrotinator/spirit-tracks-poptracker-ap)

#### 📖 Guides de Configuration (Setup)
Voici les guides officiels pour configurer chaque jeu avec Archipelago :

- **Soh Ocarina of Time** : [Guide Setup](https://github.com/HarbourMasters/Archipelago-SoH/blob/oot-soh/worlds/oot_soh/docs/guide_en.md)
- **Ocarina of Time** : [Archipelago Tutorial](https://archipelago.gg/tutorial/Ocarina%20of%20Time/setup_en)
- **Majora's Mask** : [GitHub Repo](https://github.com/RecompRando/MMRecompRando)
- **Twilight Princess** : [Guide Setup](https://github.com/WritingHusky/Twilight_Princess_apworld/blob/main/docs/setup_en.md)
  - _Note : Placez les 3 fichiers (`REL loader`, `custom seed`, `RandomizerAP.US.gci`) dans le dossier `SaveData` de Dolphin (GameCube)._
- **Wind Waker (Dolphin)** : [Archipelago Tutorial](https://archipelago.gg/tutorial/The%20Wind%20Waker/setup_en)
- **Wind Waker HD (Cemu)** : [Archipelago Tutorial](https://github.com/Teotia444/twwhd-apworld/blob/main/docs/setup_en.md)
- **Zelda 1** : [Archipelago Tutorial](https://archipelago.gg/tutorial/The%20Legend%20of%20Zelda/multiworld_en)
- **Zelda 2** : [GitHub Releases](https://github.com/PinkSwitch/Archipelago/releases/tag/Zelda2ap1.1)
- **Oracle of Ages** : [Guide Setup](https://github.com/josephanimate2021/ArchipelagoOoA/blob/ooa_dev/worlds/tloz_ooa/docs/ooa_setup_en.md)
- **Oracle of Seasons** : [Guide Setup](https://github.com/Dinopony/ArchipelagoOoS/blob/oos/worlds/tloz_oos/docs/oos_setup_en.md)
- **Link's Awakening DX** : [Archipelago Tutorial](https://archipelago.gg/tutorial/#Links%20Awakening%20DX)
- **Link's Awakening DX Beta** : [GitHub Releases](https://github.com/threeandthreee/Archipelago/releases)
- **A Link Between Worlds** : [Guide Setup](https://github.com/randomsalience/albw-archipelago/blob/main/docs/setup_en.md)
  - _Important (Azahar) : Allez dans `File > Open Azahar Folder`. Créez un dossier `load`, et à l'intérieur un dossier `mods`. Ensuite, dans `Emulation > Configure > General > Debug`, assurez-vous que `Enable RPC Server` est coché._
- **A Link to the Past** : [Archipelago Tutorial](https://archipelago.gg/tutorial/#A%20Link%20to%20the%20Past)
- **A Link to the Past OWR** : [GitHub Repo](https://github.com/aurabot24/Archipelago-ALttPR)

- **Minish Cap** : [Guide Setup](https://github.com/eternalcode0/Archipelago/blob/feat/new-game-minish-cap/worlds/tmc/docs/setup_en.md)
- **Phantom Hourglass** : [Guide Setup](https://github.com/carrotinator/Archipelago/blob/main/worlds/tloz_ph/docs/setup.md)
- **Spirit Tracks** : [Guide Setup](https://github.com/DayKat/spirit-tracks/blob/main/worlds/tloz_st/docs/setup.md)
- **Zelda's Adventure (za-gdx)** : [GitHub Repo](https://github.com/nebbii/za-gdx)
  - **Premier Lancement Obligatoire** : Avant de pouvoir lancer le jeu via le Hub, vous devez effectuer le premier lancement manuellement dans le dossier du jeu pour extraire et convertir les ressources en utilisant la commande suivante (en spécifiant le chemin vers votre `chdman.exe` de MAME/RetroArch) :
    ```bash
    ./gradlew.bat lwjgl3:run -Pchdman=/chemin/vers/votre/chdman.exe
    ```
  - **Lancement par le Hub** : Une fois cette conversion faite, le Hub se charge du lancement en exécutant simplement :
    ```bash
    ./gradlew.bat lwjgl3:run
    ```


#### 3️⃣ Configuration du Zelda Hub

Lancez Zelda-Hub.exe et configurez les onglets suivants via le bouton **⚙️ Chemins Install** :

- **Tab Slots** : Insérez les noms des slots (ceux définis dans vos YAML) pour chaque jeu.
- **Tab Archipelago** : Renseignez l'adresse du serveur (ex: `archipelago.gg:12345`) et le mot de passe si nécessaire.
- **Tab Émulateurs** : Renseignez les chemins vers vos émulateurs (`BizHawk.exe`, `Dolphin.exe`, `Cemu.exe`, etc.) ainsi que le chemin vers votre installation de **Archipelago**.



#### 4️⃣ Préparation des ROMs (Extraction & Patch)

_Les ROMs ne sont pas fournies avec le Hub. Vous devez posséder les versions originales des jeux._

1.  **Préparation** : Décompressez le dossier du monde (Zip) que vous avez généré sur Archipelago.
2.  **Extracteur** : Ouvrez l'outil d'extraction dans `Extractor/ZeldaHubPatcher.exe`.
3.  **Chemins** : Dans l'extracteur, configurez :
    - Le chemin vers le dossier PatchFile.
    - Le dossier contenant vos fichiers de patch (`.apml`, `.apzs`, etc.).
4.  **Extraction** : Lancez ensuite le **Run Patch Process**.

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
- `python_src/assets/images/` : Jaquettes des jeux affichées sur le Dashboard.
- `config.json` : Stocke tous vos réglages, chemins et préférences.

---

<br>

---

## 🇺🇸 English Version

This project is a centralized hub that automates launching your games (Native or Emulated), tracking your progress (PopTracker), and handling your Archipelago connections.

---

### 🔍 Functional Analysis (How it works?)

The Zelda Hub is built on a two-layer architecture:

#### 1. The Launch Core (`launcher_core.py`)

This is the "engine" of the Hub. It manages direct interactions with Windows processes:

- **Emulator Controllers**: Dedicated classes for **BizHawk**, **Dolphin**, **MelonDS**, **Azahar**, **RetroArch**, **Cemu**, and **Native/PC** games (Ship of Harkinian, Majora's Mask, Zelda's Adventure).
- **Robust Closing (Layer by Layer)**: To prevent emulators from corrupting your saves, the Hub uses an intelligent closing system:
  1.  **Lua Signal (BizHawk)**: Sends a `client.exit()` command via a temporary script for a perfect shutdown.
  2.  **WM_CLOSE**: Attempts a standard clean close.
  3.  **TaskKill (Force)**: A last resort if the process is "frozen".
- **Automatic Focus**: Forces the game window to the foreground on startup so you don't have to manually click it.

#### 2. The Premium Interface (`ui_main_v2.py`)

The user interface (UI) is built with **CustomTkinter** for a modern look (Sapphire Blue and Dark Mode):

- **Card Dashboard**: Each game has its "card" with its box art, allowing you to toggle the tracker before launching.
- **Quick Switcher (V1 Engine + V2 Look)**: A floating menu (accessible via controller) that lets you switch games without touching the keyboard or mouse.
- **OBS Integration**: Uses `obs-websocket` to automatically change your stream scenes as soon as a game is launched.

---

### 🏗️ Installation & Configuration Guide

Follow these steps carefully to ensure the entire system works correctly.

#### 1️⃣ Installation & Prerequisites

- **Python 3.12**: [Download and install Python 3.12](https://www.python.org/downloads/). _Important: Make sure to check "Add Python to PATH" during installation._
- **Node.js**: [Download and install Node.js](https://nodejs.org/). (Required for web trackers).
- **Setup Scripts**: Once the prerequisites are installed, go to the `scripts/` folder and run **`INSTALL_ALL.bat`**. This script will automatically install all Python and Node dependencies for you.
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
- **Link's Awakening DX Beta**: [GitHub Releases](https://github.com/threeandthreee/Archipelago/releases)
- **A Link Between Worlds**: [GitHub Releases](https://github.com/randomsalience/albw-archipelago/releases)
- **A Link to the Past**: Already included by default
- **A Link to the Past OWR**: [GitHub Releases](https://github.com/aurabot24/Archipelago-ALttPR/releases/)
- **Minish Cap**: [GitHub Releases](https://github.com/eternalcode0/Archipelago/releases)
- **Phantom Hourglass**: [GitHub Releases](https://github.com/carrotinator/Archipelago/releases)
- **Spirit Tracks**: [GitHub Releases](https://github.com/DayKat/spirit-tracks/releases)
- **Zelda's Adventure**: [GitHub Releases](https://github.com/nebbii/za-gdx/releases)


#### 📦 PopTracker Links
To enjoy automatic tracking, here are the recommended packs for each game. **Note: It is strongly recommended to join the various community Discord servers to get the latest versions.**

- **Soh Ocarina of Time** : [GitHub Releases](https://github.com/Brian0255/ship-of-harkinian-ap-tracker/releases)
- **Ocarina of Time** : [GitHub Releases](https://github.com/StripesOO7/oot-tracker/releases)
- **Majora's Mask** : [GitHub Releases](https://github.com/G4M3RL1F3/Majoras-Mask-AP-PopTracker-Pack/releases)
- **Twilight Princess** : [GitHub Releases](https://github.com/Kizugaya/TPRAP_poptracker/releases)
- **Wind Waker** : [GitHub Releases](https://github.com/Mysteryem/ww-poptracker/releases/tag/v1.3.0)
- **Zelda 1** : [GitHub Releases](https://github.com/Br00ty/tloz_brooty/releases)
- **Zelda 2, Adventure of Link** : [GitHub Releases](https://github.com/palex00/zelda-2-ap-tracker/releases/latest/)
- **Oracle of Ages** : [GitHub Releases](https://github.com/Dranzior/ooa_brooty/releases)
- **Oracle of Seasons** : [GitHub Releases](https://github.com/OmegaZeron/Oracle-of-Seasons-AP-Poptracker-Pack/releases/latest)
- **Link's Awakening DX** : [Magpie Tracker](https://magpietracker.us/)
- **Link's Awakening DX Beta** : [Magpie Tracker](https://magpietracker.us/)
- **A Link Between Worlds** : [GitHub Releases](https://github.com/Legendgreat/albw-ap-poptracker/releases)
- **A Link to the Past** : [GitHub Releases](https://github.com/StripesOO7/alttp-ap-poptracker-pack/releases)
- **Minish Cap** : [GitHub Releases](https://github.com/deoxis9001/tmcrando_maptracker_deoxis/releases)
- **Phantom Hourglass** : [GitHub Repo](https://github.com/ZobeePlays/PH-AP-Item-Tracker/tree/main)
- **Spirit Tracks** : [GitHub Repo](https://github.com/carrotinator/spirit-tracks-poptracker-ap)

#### 📖 Setup Guides
Official guides to configure each game with Archipelago:

- **Soh Ocarina of Time**: [Setup Guide](https://github.com/HarbourMasters/Archipelago-SoH/blob/oot-soh/worlds/oot_soh/docs/guide_en.md)
- **Ocarina of Time**: [Archipelago Tutorial](https://archipelago.gg/tutorial/Ocarina%20of%20Time/setup_en)
- **Majora's Mask**: [GitHub Repo](https://github.com/RecompRando/MMRecompRando)
- **Twilight Princess**: [Setup Guide](https://github.com/WritingHusky/Twilight_Princess_apworld/blob/main/docs/setup_en.md)
  - _Note: Place the 3 files (`REL loader`, `custom seed`, `RandomizerAP.US.gci`) in Dolphin's `SaveData` folder (GameCube)._
- **Wind Waker (Dolphin)** : [Archipelago Tutorial](https://archipelago.gg/tutorial/The%20Wind%20Waker/setup_en)
- **Wind Waker HD (Cemu)**: [Archipelago Tutorial](https://github.com/Teotia444/twwhd-apworld/blob/main/docs/setup_en.md)
- **Zelda 1**: [Archipelago Tutorial](https://archipelago.gg/tutorial/The%20Legend%20of%20Zelda/multiworld_en)
- **Zelda 2**: [GitHub Releases](https://github.com/PinkSwitch/Archipelago/releases/tag/Zelda2ap1.1)
- **Oracle of Ages**: [Setup Guide](https://github.com/josephanimate2021/ArchipelagoOoA/blob/ooa_dev/worlds/tloz_ooa/docs/ooa_setup_en.md)
- **Oracle of Seasons**: [Setup Guide](https://github.com/Dinopony/ArchipelagoOoS/blob/oos/worlds/tloz_oos/docs/oos_setup_en.md)
- **Link's Awakening DX**: [Archipelago Tutorial](https://archipelago.gg/tutorial/#Links%20Awakening%20DX)
- **Link's Awakening DX Beta**: [GitHub Releases](https://github.com/threeandthreee/Archipelago/releases)
- **A Link Between Worlds**: [Setup Guide](https://github.com/randomsalience/albw-archipelago/blob/main/docs/setup_en.md)
  - _Important (Azahar): Select `File > Open Azahar Folder`. Create a `load` folder inside, and a `mods` folder inside that. Also, in `Emulation > Configure > General > Debug`, ensure `Enable RPC Server` is enabled._
- **A Link to the Past**: [Archipelago Tutorial](https://archipelago.gg/tutorial/#A%20Link%20to%20the%20Past)
- **A Link to the Past OWR**: [GitHub Repo](https://github.com/aurabot24/Archipelago-ALttPR)

- **Minish Cap**: [Setup Guide](https://github.com/eternalcode0/Archipelago/blob/feat/new-game-minish-cap/worlds/tmc/docs/setup_en.md)
- **Phantom Hourglass**: [Setup Guide](https://github.com/carrotinator/Archipelago/blob/main/worlds/tloz_ph/docs/setup.md)
- **Spirit Tracks**: [Setup Guide](https://github.com/DayKat/spirit-tracks/blob/main/worlds/tloz_st/docs/setup.md)
- **Zelda's Adventure (za-gdx)**: [GitHub Repo](https://github.com/nebbii/za-gdx)
  - **Required First Launch**: Before launching it via the Hub, you must perform the initial launch manually in the game's folder to extract and convert the game assets using the following command (replace with the path to your MAME/RetroArch `chdman.exe`):
    ```bash
    ./gradlew.bat lwjgl3:run -Pchdman=/path/to/your/chdman.exe
    ```
  - **Hub Launching**: Once this conversion step is completed, the Hub will launch the game simply using:
    ```bash
    ./gradlew.bat lwjgl3:run
    ```


#### 3️⃣ Zelda Hub Configuration

Run `python python_src/ui_main_v2.py` and configure the following tabs via the **⚙️ Install Paths** button:

- **Slots Tab**: Enter the slot names (defined in your YAMLs) for each game.
- **Archipelago Tab**: Enter the server address (e.g., `archipelago.gg:12345`) and password if necessary.
- **Emulators Tab**: Enter the paths to your emulators (`BizHawk.exe`, `Dolphin.exe`, `Cemu.exe`, etc.) as well as the path to your **Archipelago** installation.

#### 4️⃣ ROM Preparation (Extraction & Patch)

_ROMs are not provided with the Hub. You must own the original versions of the games._

1.  **Preparation**: Unzip the world folder (Zip) generated on Archipelago.
2.  **Extractor**: Open the extraction tool in `Extractor/ZeldaHubPatcher.exe`.
3.  **Paths**: In the extractor, configure:
    - The path to your PatchFile folder.
    - The folder containing your patch files (`.apml`, `.apzs`, etc.).
4.  **Extraction**: Run the **Run Patch Process**.

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
- `python_src/assets/images/`: Game box arts displayed on the Dashboard.
- `config.json`: Stores all your settings, paths, and preferences.

---
