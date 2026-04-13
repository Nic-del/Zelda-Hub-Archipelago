import os

# pack_path = r"C:\Users\linksweld\Documents\zelda-multi-launcher-hub\App\Poptracker\packs\Webtracker-SS"
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pack_path = os.path.join(base_dir, "App", "Poptracker", "packs", "Webtracker-SS")
is_web_folder = os.path.isdir(pack_path) and (os.path.exists(os.path.join(pack_path, "index.html")) or os.path.exists(os.path.join(pack_path, "dist")))

print(f"{pack_path=}")
print(f"{os.path.isdir(pack_path)=}")
print(f"{os.path.exists(os.path.join(pack_path, 'index.html'))=}")
print(f"{os.path.exists(os.path.join(pack_path, 'dist'))=}")
print(f"{is_web_folder=}")
