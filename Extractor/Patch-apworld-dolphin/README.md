# APWorld Patcher Pro

Cette application permet de patcher facilement vos fichiers `.apworld` pour les rendre compatibles avec le **Dolphin Memory Engine Fork** .

## Fonctionnalités
1.  **Conversion automatique** : Change l'extension de `.apworld` en `.zip`.
2.  **Patching Intelligent** : Recherche les fichiers clients (`TPClient.py`, `TWWClient.py`, `SSClient.py`) à l'intérieur de l'archive.
3.  **Mise à jour de l'import** : Remplace `import dolphin_memory_engine` par `import dolphin_memory_engine_fork as dolphin_memory_engine`.
4.  **Interface Moderne** : Design soigné et sombre avec retour visuel en temps réel.

## Utilisation
1.  Assurez-vous d'avoir Python installé.
2.  Installez les dépendances si nécessaire :
    ```bash
    pip install pywebview
    ```
3.  Lancez l'application :
    ```bash
    python app.py
    ```
4.  Sélectionnez le dossier contenant vos fichiers `.apworld` et cliquez sur **Lancer le Patching**. 
