from pathlib import Path
import os
import json
from datetime import datetime

ALLOWED_FLAGS = {
    "DFIntCSGLevelOfDetailSwitchingDistance",
    "DFIntCSGLevelOfDetailSwitchingDistanceL12",
    "DFIntCSGLevelOfDetailSwitchingDistanceL23",
    "DFIntCSGLevelOfDetailSwitchingDistanceL34",
    "FFlagHandleAltEnterFullscreenManually",
    "DFFlagTextureQualityOverrideEnabled",
    "DFIntTextureQualityOverride",
    "FIntDebugForceMSAASamples",
    "DFFlagDisableDPIScale",
    "FFlagDebugGraphicsPreferD3D11",
    "FFlagDebugSkyGray",
    "DFFlagDebugPauseVoxelizer",
    "DFIntDebugFRMQualityLevelOverride",
    "FIntFRMMaxGrassDistance",
    "FIntFRMMinGrassDistance",
    "FFlagDebugGraphicsPreferVulkan",
    "FFlagDebugGraphicsPreferOpenGL",
    "FIntGrassMovementReducedMotionFactor",
    "DFIntTaskSchedulerTargetFps",
    "FIntTaskSchedulerAutoThreadLimit",
}

def get_launcher_path(launcher: str) -> Path:
    local_appdata = Path(os.getenv("LOCALAPPDATA"))
    if launcher == "Bloxstrap":
        return local_appdata / "Bloxstrap"
    elif launcher == "Fishstrap" or launcher == "FishTrapper":
        return local_appdata / "Fishstrap"
    elif launcher == "Roblox":
        return local_appdata / "Roblox"
    else:
        raise ValueError(f"Unknown launcher: {launcher}")

def find_latest_version(launcher: str = "Bloxstrap") -> Path:
    local_appdata = Path(os.getenv("LOCALAPPDATA"))
    if launcher == "Bloxstrap":
        versions_path = local_appdata / "Bloxstrap" / "Roblox" / "Versions"
    elif launcher == "Fishstrap" or launcher == "FishTrapper":
        versions_path = local_appdata / "Fishstrap" / "Versions"
    elif launcher == "Roblox":
        versions_path = local_appdata / "Roblox" / "Versions"
    else:
        raise ValueError(f"Unknown launcher: {launcher}")

    if not versions_path.exists():
        raise FileNotFoundError(f"Versions folder not found: {versions_path}")

    version_folders = [f for f in versions_path.iterdir() if f.is_dir()]
    if not version_folders:
        raise FileNotFoundError(f"No Roblox versions found in: {versions_path}")

    return max(version_folders, key=lambda f: f.stat().st_mtime)

def get_client_settings_path(launcher: str = "Bloxstrap") -> Path:
    version = find_latest_version(launcher)
    client_settings = version / "ClientSettings"
    client_settings.mkdir(parents=True, exist_ok=True)
    return client_settings / "ClientAppSettings.json"

def read_flags(launcher: str = "Bloxstrap") -> dict:
    config_path = get_client_settings_path(launcher)
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {}

def validate_flags(flags: dict) -> tuple[dict, list]:
    valid_flags = {}
    invalid_flags = []
    for key in flags:
        if key in ALLOWED_FLAGS:
            valid_flags[key] = flags[key]
        else:
            invalid_flags.append(key)
    return valid_flags, invalid_flags

def write_flags(flags: dict, launcher: str = "Bloxstrap", backup: bool = True, validate: bool = True) -> Path:
    if validate:
        valid_flags, invalid_flags = validate_flags(flags)
        if invalid_flags:
            print(f"Warning: The following flags are NOT allowed by Roblox and will be ignored:")
            for f in invalid_flags:
                print(f"  - {f}")
            print(f"Allowed flags: {', '.join(sorted(ALLOWED_FLAGS))}")
            flags = valid_flags
    
    if not flags:
        raise ValueError("No valid flags to write after filtering")
    
    config_path = get_client_settings_path(launcher)
    
    if backup and config_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = config_path.parent / f"ClientAppSettings_backup_{timestamp}.json"
        backup_path.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(flags, f, indent=4)
    
    return config_path

def set_flag(key: str, value, launcher: str = "Bloxstrap") -> Path:
    flags = read_flags(launcher)
    flags[key] = value
    return write_flags(flags, launcher)

def remove_flag(key: str, launcher: str = "Bloxstrap") -> Path:
    flags = read_flags(launcher)
    if key in flags:
        del flags[key]
    return write_flags(flags, launcher)

def clear_flags(launcher: str = "Bloxstrap", validate: bool = True) -> Path:
    return write_flags({}, launcher, backup=True, validate=validate)

def get_flag(key: str, launcher: str = "Bloxstrap") -> any:
    flags = read_flags(launcher)
    return flags.get(key)

def list_flags(launcher: str = "Bloxstrap") -> dict:
    return read_flags(launcher)

def list_backups(launcher: str = "Bloxstrap") -> list:
    config_path = get_client_settings_path(launcher)
    backup_dir = config_path.parent
    if not backup_dir.exists():
        return []
    backups = list(backup_dir.glob("ClientAppSettings_backup_*.json"))
    return sorted(backups, key=lambda f: f.stat().st_mtime, reverse=True)

def restore_backup(backup_path: Path) -> Path:
    config_path = backup_path.parent / "ClientAppSettings.json"
    current_flags = json.loads(backup_path.read_text(encoding="utf-8"))
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(current_flags, f, indent=4)
    return config_path

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python flag.pyw <command> [args] [launcher]")
        print("Commands:")
        print("  list                         - List all current flags")
        print("  get <key>                    - Get a specific flag")
        print("  set <key> <value>            - Set a flag (value: number, true, false, or \"string\")")
        print("  remove <key>                 - Remove a flag")
        print("  clear                        - Clear all flags")
        print("  apply                        - Show config path")
        print("  preset <file>                - Apply preset from JSON file")
        print("  allowed                      - List all allowed flags")
        print("  backups                      - List available backups")
        print("  restore                      - Restore most recent backup")
        print("  restore <index>              - Restore backup by index (0 = most recent)")
        print("Options:")
        print("  --force                      - Skip allowlist validation")
        print("Launcher: Bloxstrap (default), Fishstrap, Roblox")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    launcher = "Bloxstrap"
    force = "--force" in sys.argv
    
    if "--force" in sys.argv:
        sys.argv.remove("--force")
    
    if len(sys.argv) > 2:
        potential_launcher = sys.argv[-1]
        if potential_launcher in ("Bloxstrap", "Fishstrap", "Roblox"):
            launcher = potential_launcher
    
    try:
        if command == "list":
            flags = list_flags(launcher)
            print(f"Flags for {launcher}:")
            for k, v in flags.items():
                print(f"  {k}: {v}")
        
        elif command == "get" and len(sys.argv) > 2:
            key = sys.argv[2]
            value = get_flag(key, launcher)
            print(f"{key}: {value}")
        
        elif command == "set" and len(sys.argv) > 3:
            key = sys.argv[2]
            value_str = sys.argv[3]
            if value_str.lower() == "true":
                value = True
            elif value_str.lower() == "false":
                value = False
            elif value_str.isdigit():
                value = int(value_str)
            else:
                value = value_str
            
            if not force and key not in ALLOWED_FLAGS:
                print(f"Warning: '{key}' is NOT in the allowed list.")
                print(f"Use --force to bypass this check.")
                sys.exit(1)
            
            path = set_flag(key, value, launcher)
            print(f"Set {key} = {value}")
            print(f"Written to: {path}")
        
        elif command == "remove" and len(sys.argv) > 2:
            key = sys.argv[2]
            path = remove_flag(key, launcher)
            print(f"Removed {key}")
            print(f"Written to: {path}")
        
        elif command == "clear":
            path = clear_flags(launcher, validate=not force)
            print(f"Cleared all flags")
            print(f"Written to: {path}")
        
        elif command == "apply":
            path = get_client_settings_path(launcher)
            print(f"ClientAppSettings.json path for {launcher}:")
            print(path)
        
        elif command == "allowed":
            print("Allowed flags (Roblox allowlist):")
            for flag in sorted(ALLOWED_FLAGS):
                print(f"  {flag}")
        
        elif command == "backups":
            backups = list_backups(launcher)
            if not backups:
                print(f"No backups found for {launcher}")
            else:
                print(f"Backups for {launcher}:")
                for i, backup in enumerate(backups):
                    print(f"  [{i}] {backup.name}")
        
        elif command == "restore" or command == "reverse":
            backups = list_backups(launcher)
            if not backups:
                raise FileNotFoundError(f"No backups found for {launcher}")
            
            index = 0
            if len(sys.argv) > 2 and sys.argv[2].isdigit():
                index = int(sys.argv[2])
            
            if index >= len(backups):
                raise IndexError(f"Backup index {index} out of range (max: {len(backups) - 1})")
            
            backup_path = backups[index]
            path = restore_backup(backup_path)
            print(f"Restored from: {backup_path.name}")
            print(f"Written to: {path}")
        
        elif command == "preset" and len(sys.argv) > 2:
            preset_file = Path(sys.argv[2])
            if not preset_file.exists():
                preset_file = Path(__file__).parent / sys.argv[2]
            if not preset_file.exists():
                raise FileNotFoundError(f"Preset file not found: {sys.argv[2]}")
            
            with open(preset_file, "r", encoding="utf-8") as f:
                preset_flags = json.load(f)
            
            path = write_flags(preset_flags, launcher, validate=not force)
            print(f"Applied preset from: {preset_file}")
            print(f"Written to: {path}")
            print(f"Flags applied: {len(preset_flags)}")
        
        else:
            print("Unknown command. Run without args for help.")
    except Exception as e:
        print(f"Error: {e}")
