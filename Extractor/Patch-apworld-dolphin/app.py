import os
import zipfile
import shutil
import tempfile
import webview
import json
import threading
import sys

class PatchApp:
    def __init__(self):
        self._window = None

    def get_local_apworlds(self):
        """Scans the current directory for .apworld files on launch."""
        if getattr(sys, 'frozen', False):
            target_dir = os.path.dirname(sys.executable)
        else:
            target_dir = os.path.dirname(os.path.abspath(__file__))
            
        apworlds = [f for f in os.listdir(target_dir) 
                    if f.endswith('.apworld') and os.path.isfile(os.path.join(target_dir, f))]
        return {"directory": target_dir, "files": apworlds}

    def select_directory(self):
        """Opens a directory picker and returns all found .apworld files."""
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            target_dir = result[0] if isinstance(result, (list, tuple)) else result
            # Exclude 'output' directory if it exists within the target
            try:
                apworlds = [f for f in os.listdir(target_dir) 
                            if f.endswith('.apworld') and os.path.isfile(os.path.join(target_dir, f))]
                return {"directory": target_dir, "files": apworlds}
            except Exception as e:
                print(f"Error reading directory {target_dir}: {e}")
                return None
        return None

    def patch_files(self, directory, filenames):
        """Main patching logic."""
        results = []
        
        # Determine application root directory
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
            
        # Create output directory in the app folder
        output_dir = os.path.join(app_dir, "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Mapping games to their potential ID prefixes
        GAME_ID_MAPPING = {
            "TPClient": ("GZ2", "RZD"),
            "TWWClient": ("GZL",),
            "SSClient": ("SOU",)
        }

        for filename in filenames:
            file_path = os.path.join(directory, filename)
            final_apworld_path = os.path.join(output_dir, filename)

            try:
                modified = False
                patched_games = []
                
                with zipfile.ZipFile(file_path, 'r') as original_zip:
                    with zipfile.ZipFile(final_apworld_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                        for item in original_zip.infolist():
                            # Read original content
                            with original_zip.open(item.filename) as f:
                                data = f.read()
                            
                            # Check if this file is a target client
                            game_key = next((k for k in GAME_ID_MAPPING if k in item.filename and item.filename.endswith(".py")), None)
                            
                            if game_key:
                                try:
                                    content = data.decode('utf-8')
                                    file_modified = False
                                    
                                    # --- A. Patch Import ---
                                    old_import = "import dolphin_memory_engine"
                                    new_import = "import dolphin_memory_engine_fork as dolphin_memory_engine"
                                    if old_import in content and "dolphin_memory_engine_fork" not in content:
                                        content = content.replace(old_import, new_import)
                                        file_modified = True

                                    # --- B. Add psutil Import ---
                                    if "import psutil" not in content:
                                        content = "import psutil\n" + content
                                        file_modified = True

                                    # --- C. Patch PID Connection Logic ---
                                    if "Attempting to connect to Dolphin..." in content and "psutil.process_iter" not in content:
                                        target_prefixes = GAME_ID_MAPPING[game_key]
                                        id_check_logic = " or ".join([f'game_id.startswith("{p}")' for p in target_prefixes])
                                        
                                        connect_pattern = r'(logger\.info\("Attempting to connect to Dolphin\.\.\."\)\s+)(dolphin_memory_engine\.hook\(\)\s+if dolphin_memory_engine\.is_hooked\(\):)'
                                        
                                        replacement_logic = f"""\\1
                    dolphins = [p.info['pid'] for p in psutil.process_iter(['pid', 'name']) if p.info['name'] == 'Dolphin.exe']
                    success = False
                    if not dolphins:
                        dolphin_memory_engine.hook()
                        if dolphin_memory_engine.is_hooked():
                             game_id = await ctx.read_string(0x80000000, 3)
                             if {id_check_logic}:
                                 success = True
                             else:
                                 dolphin_memory_engine.un_hook()
                    else:
                        for pid in dolphins:
                            try:
                                dolphin_memory_engine.hook(pid)
                                if dolphin_memory_engine.is_hooked():
                                    game_id = await ctx.read_string(0x80000000, 3)
                                    if {id_check_logic}:
                                        success = True
                                        break
                                    else:
                                        dolphin_memory_engine.un_hook()
                            except Exception:
                                dolphin_memory_engine.un_hook()
                    
                    if success:"""
                                        
                                        import re
                                        
                                        target_prefixes = GAME_ID_MAPPING[game_key]
                                        id_check_logic = " or ".join([f'game_id.startswith("{p}")' for p in target_prefixes])
                                        
                                        # Capture the hook part to detect indentation
                                        connect_pattern = r'(logger\.info\("Attempting to connect to Dolphin\.\.\."\)\s+)(dolphin_memory_engine\.hook\(\)\s+if dolphin_memory_engine\.is_hooked\(\):)'
                                        
                                        def replacement_func(match):
                                            prefix = match.group(1) # logger.info(...) + newline + indentation
                                            # Get the actual indentation from the end of the prefix
                                            indent = prefix.split('\n')[-1]
                                            
                                            prefixes_bytes = ", ".join([f'b"{p}"' for p in target_prefixes])
                                            logic = f"""{prefix}# Debug: Search Dolphin processes (case-insensitive)
{indent}dolphins = [pid_info.info['pid'] for pid_info in psutil.process_iter(['pid', 'name']) 
{indent}            if pid_info.info['name'] and pid_info.info['name'].lower() in ('dolphin.exe', 'dolphinqt.exe')]
{indent}
{indent}logger.info(f"Dolphin search: found {{len(dolphins)}} process(es).")
{indent}
{indent}success = False
{indent}if not dolphins:
{indent}    logger.info("No Dolphin process found in list, trying default hook.")
{indent}    dolphin_memory_engine.hook()
{indent}    if dolphin_memory_engine.is_hooked():
{indent}        try:
{indent}            if dolphin_memory_engine.read_bytes(0x80000000, 3) in [{prefixes_bytes}]:
{indent}                logger.info(f"Default hook success! ID: {{dolphin_memory_engine.read_bytes(0x80000000, 3)}}")
{indent}                success = True
{indent}            else:
{indent}                dolphin_memory_engine.un_hook()
{indent}        except Exception:
{indent}            dolphin_memory_engine.un_hook()
{indent}else:
{indent}    for pid in dolphins:
{indent}        try:
{indent}            logger.info(f"Testing Dolphin PID {{pid}}...")
{indent}            dolphin_memory_engine.hook(pid)
{indent}            if dolphin_memory_engine.is_hooked():
{indent}                try:
{indent}                    if dolphin_memory_engine.read_bytes(0x80000000, 3) in [{prefixes_bytes}]:
{indent}                        logger.info(f"Hooked PID {{pid}} success! ID: {{dolphin_memory_engine.read_bytes(0x80000000, 3)}}")
{indent}                        success = True
{indent}                        break
{indent}                    else:
{indent}                        dolphin_memory_engine.un_hook()
{indent}                except Exception:
{indent}                    dolphin_memory_engine.un_hook()
{indent}        except Exception as e:
{indent}            logger.info(f"PID {{pid}} hook error: {{e}}")
{indent}            dolphin_memory_engine.un_hook()
{indent}
{indent}if success:"""
                                            return logic

                                        new_content, count = re.subn(connect_pattern, replacement_func, content)
                                        if count > 0:
                                            content = new_content
                                            file_modified = True
                                    
                                    if file_modified:
                                        data = content.encode('utf-8')
                                        modified = True
                                        patched_games.append(item.filename)
                                        
                                except Exception as e:
                                    print(f"Skipping binary or problematic file {item.filename}: {e}")
                            
                            # Write to new zip (original or modified)
                            new_zip.writestr(item, data)
                
                results.append({"name": filename, "status": "Patched", "games": patched_games})
                
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                results.append({"name": filename, "status": f"Error: {str(e)}", "games": []})
        
        return results



    def run(self):
        HTML = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>APWorld Patcher Pro</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
            <style>
                :root {
                    --bg-color: #020617;
                    --card-bg: rgba(30, 41, 59, 0.7);
                    --primary: #6366f1;
                    --primary-hover: #4f46e5;
                    --text: #f1f5f9;
                    --text-muted: #94a3b8;
                    --success: #10b981;
                    --error: #ef4444;
                    --border: rgba(255, 255, 255, 0.1);
                }
                * { box-sizing: border-box; }
                body {
                    font-family: 'Inter', sans-serif;
                    background-color: var(--bg-color);
                    background-image: 
                        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0, transparent 50%),
                        radial-gradient(at 100% 100%, rgba(16, 185, 129, 0.1) 0, transparent 50%);
                    color: var(--text);
                    margin: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    overflow: hidden;
                }
                .container {
                    background: var(--card-bg);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    padding: 3rem;
                    border-radius: 2rem;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8);
                    width: 90%;
                    max-width: 650px;
                    border: 1px solid var(--border);
                    text-align: center;
                    animation: fadeIn 0.6s ease-out;
                }
                @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
                
                h1 { 
                    margin: 0 0 0.5rem 0; 
                    font-size: 2.25rem;
                    font-weight: 800; 
                    letter-spacing: -0.025em;
                    background: linear-gradient(135deg, #818cf8 0%, #34d399 100%);
                    -webkit-background-clip: text; 
                    -webkit-text-fill-color: transparent; 
                }
                .subtitle { color: var(--text-muted); margin-bottom: 2.5rem; font-size: 1.1rem; }
                
                .main-action {
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                    align-items: center;
                }

                .btn {
                    background: var(--primary);
                    color: white;
                    border: none;
                    padding: 1rem 2rem;
                    border-radius: 1rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    font-size: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
                    display: inline-flex;
                    align-items: center;
                    gap: 0.75rem;
                }
                .btn:hover { 
                    background: var(--primary-hover); 
                    transform: scale(1.02);
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
                }
                .btn:active { transform: scale(0.98); }
                .btn-success { background: var(--success); }
                .btn-disabled { background: #334155; cursor: not-allowed; opacity: 0.7; }
                .btn-remove { background: rgba(239, 68, 68, 0.1); color: #ef4444; padding: 0.5rem; border-radius: 0.5rem; box-shadow: none; border: 1px solid rgba(239, 68, 68, 0.2); }
                .btn-remove:hover { background: rgba(239, 68, 68, 0.2); transform: scale(1.05); }

                .list-container {
                    margin-top: 2rem;
                    background: rgba(15, 23, 42, 0.4);
                    border-radius: 1.25rem;
                    border: 1px solid var(--border);
                    max-height: 280px;
                    overflow-y: auto;
                    padding: 1rem;
                }

                .file-card {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 1rem;
                    background: rgba(30, 41, 59, 0.5);
                    border-radius: 0.85rem;
                    margin-bottom: 0.75rem;
                    border: 1px solid rgba(255,255,255,0.05);
                    text-align: left;
                    transition: transform 0.2s;
                }
                .file-card:hover { transform: translateX(4px); background: rgba(30, 41, 59, 0.8); }
                
                .file-info { display: flex; flex-direction: column; gap: 0.25rem; overflow: hidden; }
                .file-name { font-weight: 600; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #e2e8f0; }
                .file-meta { font-size: 0.8rem; color: var(--text-muted); display: flex; gap: 0.5rem; }
                
                .badge {
                    font-size: 0.75rem;
                    padding: 0.35rem 0.75rem;
                    border-radius: 0.6rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.025em;
                }
                .badge-pending { background: rgba(59, 130, 246, 0.1); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.2); }
                .badge-success { background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); }
                .badge-error { background: rgba(239, 68, 68, 0.1); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.2); }

                .game-tag {
                    background: rgba(148, 163, 184, 0.1);
                    color: #cbd5e1;
                    padding: 0.1rem 0.6rem;
                    border-radius: 0.4rem;
                    font-size: 0.7rem;
                    font-weight: 500;
                }

                ::-webkit-scrollbar { width: 8px; }
                ::-webkit-scrollbar-track { background: transparent; }
                ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; border: 2px solid var(--bg-color); }
                
                .empty-state { padding: 3rem; color: var(--text-muted); font-style: italic; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Dolphin Patcher</h1>
                <p class="subtitle">Convertis tes .apworld en .zip et change l'import Dolphin Engine Fork.</p>
                
                <div class="main-action">
                    <div id="dir-section">
                        <button class="btn" onclick="selectDir()">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                            Ouvrir un Dossier
                        </button>
                    </div>
                </div>

                <div id="file-list-area" class="list-container">
                    <div class="empty-state">Aucun fichier sélectionné</div>
                </div>

                <div id="patch-section" style="margin-top: 2rem; display: none;">
                    <button id="patch-btn" class="btn btn-success" onclick="patchAll()">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                        Lancer le Patching
                    </button>
                </div>
            </div>

            <script>
                let currentDir = "";
                let filesToPatch = [];

                function renderFileList() {
                    if (filesToPatch.length === 0) {
                        document.getElementById('file-list-area').innerHTML = '<div class="empty-state">Aucun .apworld sélectionné.</div>';
                        document.getElementById('patch-section').style.display = 'none';
                        return;
                    }
                    
                    document.getElementById('patch-section').style.display = 'block';
                    
                    const listHtml = filesToPatch.map(f => `
                        <div class="file-card">
                            <div class="file-info" style="flex: 1; padding-right: 1rem;">
                                <div class="file-name" title="${f}">${f}</div>
                                <div class="file-meta">Attente...</div>
                            </div>
                            <div style="display: flex; gap: 0.5rem; align-items: center;">
                                <span class="badge badge-pending">À Traiter</span>
                                <button class="btn btn-remove" onclick="removeFile('${f.replace(/'/g, "\\'")}')" title="Retirer de la liste">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                                </button>
                            </div>
                        </div>
                    `).join('');
                    document.getElementById('file-list-area').innerHTML = listHtml;
                }

                function removeFile(filename) {
                    filesToPatch = filesToPatch.filter(f => f !== filename);
                    renderFileList();
                }

                window.addEventListener('pywebviewready', async function() {
                    const res = await window.pywebview.api.get_local_apworlds();
                    if (res && res.files.length > 0) {
                        currentDir = res.directory;
                        filesToPatch = res.files;
                        renderFileList();
                    }
                });

                async function selectDir() {
                    const res = await window.pywebview.api.select_directory();
                    if (!res) return;
                    
                    currentDir = res.directory;
                    filesToPatch = res.files;
                    renderFileList();
                }

                async function patchAll() {
                    const btn = document.getElementById('patch-btn');
                    btn.disabled = true;
                    btn.classList.add('btn-disabled');
                    btn.innerText = "Traitement...";

                    const results = await window.pywebview.api.patch_files(currentDir, filesToPatch);
                    
                    const listHtml = results.map(r => `
                        <div class="file-card">
                            <div class="file-info">
                                <div class="file-name">${r.name}</div>
                                <div class="file-meta">
                                    ${r.games.length > 0 
                                        ? r.games.map(g => `<span class="game-tag">${g}</span>`).join('') 
                                        : 'Aucun client modifié'}
                                </div>
                            </div>
                            <span class="badge ${r.status === 'Patched' ? 'badge-success' : 'badge-error'}">
                                ${r.status === 'Patched' ? 'Terminé' : 'Erreur'}
                            </span>
                        </div>
                    `).join('');
                    document.getElementById('file-list-area').innerHTML = listHtml;
                    
                    btn.innerText = "Patching Terminé";
                }
            </script>
        </body>
        </html>
        """
        self._window = webview.create_window('Zelda APWorld Patcher Pro', html=HTML, width=700, height=650, resizable=False)
        self._window.expose(self.select_directory, self.patch_files, self.get_local_apworlds)
        webview.start()


if __name__ == "__main__":
    app = PatchApp()
    app.run()
