import sys
sys.path.append('/home/taylan/Masaüstü/test3')
from grub_settings import GrubPaths

paths = GrubPaths()
print(f"Distro: {paths.distro_id}")
print(f"Config: {paths.grub_cfg}")
print(f"EFI: {paths.efi_path}")
print(f"Update Cmd: {paths.update_cmd}")

if paths.distro_id == 'unknown':
    print("WARNING: Distro not detected correctly")
else:
    print("SUCCESS: Distro detected")
