#!/usr/bin/env python3
import os
import re
import sys
import subprocess
import argparse
import datetime

# Configuration
FILES_TO_UPDATE = {
    "grub_settings.py": r'APP_VERSION = "({version})"',
    "grub_settings_pkg/constants.py": r'APP_VERSION = "({version})"',
    "packaging/deb/DEBIAN/control": r'Version: ({version})',
    "README.md": [
        r'version-({version})',
        r'grub-settings_({version})_all.deb'
    ]
}

FLATPAK_META = "flatpak/io.github.taylan.grubsettings.metainfo.xml"

def run_command(cmd, shell=True):
    try:
        result = subprocess.run(cmd, shell=shell, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(e.stderr)
        sys.exit(1)

def get_current_version():
    with open("grub_settings.py", "r") as f:
        content = f.read()
        match = re.search(r'APP_VERSION = "([^"]+)"', content)
        if match:
            return match.group(1)
    print("Error: Could not detect current version from grub_settings.py")
    sys.exit(1)

def bump_version(current_version, part):
    # Handle versions like "0.1.1.1" or "0.1.0"
    parts = list(map(int, current_version.split('.')))

    # Ensure at least 3 parts (major.minor.patch)
    while len(parts) < 3:
        parts.append(0)

    if part == "major":
        parts[0] += 1
        parts[1] = 0
        parts[2] = 0
        parts = parts[:3] # Reset potential 4th part
    elif part == "minor":
        parts[1] += 1
        parts[2] = 0
        parts = parts[:3]
    elif part == "patch":
        parts[2] += 1
        parts = parts[:3]

    return ".".join(map(str, parts))

def get_git_changes():
    try:
        try:
            last_tag = run_command("git describe --tags --abbrev=0")
        except:
            # Fallback: try to get the latest tag even if not reachable
            try:
                last_tag = run_command("git tag --sort=-v:refname | head -n 1")
                if not last_tag:
                    raise Exception("No tags found")
            except:
                return "- Initial release or no tags found."

        log = run_command(f'git log {last_tag}..HEAD --pretty=format:"- %s"')
        return log if log else "- No changes detected since last tag."
    except Exception as e:
        print(f"Warning determining changes: {e}")
        return "- Changes detection failed."

def update_file_content(filepath, current_ver, new_ver, patterns):
    if not os.path.exists(filepath):
        print(f"Warning: File {filepath} not found. Skipping.")
        return

    with open(filepath, "r") as f:
        content = f.read()

    new_content = content
    pattern_list = patterns if isinstance(patterns, list) else [patterns]

    for pattern in pattern_list:
        # Regex find the full string with current version, replace with full string with new version
        regex_pattern = pattern.format(version=re.escape(current_ver))

        # Clean pattern for replacement string generation
        clean_pattern = pattern.replace("(", "").replace(")", "").replace("\\", "")
        target_string = clean_pattern.format(version=new_ver)

        new_content = re.sub(regex_pattern, target_string, new_content)

    # Special handling for README badge which might be 0.1.0--beta vs 0.1.1.1
    # If explicit replace failed because versions didn't match (sync issue), force regex on Version Badge
    if filepath == "README.md":
         new_content = re.sub(r'version-[\d\.]+(-beta)?-', f'version-{new_ver}-', new_content)
         new_content = re.sub(r'grub-settings_[\d\.]+_all.deb', f'grub-settings_{new_ver}_all.deb', new_content)

    if content != new_content:
        with open(filepath, "w") as f:
            f.write(new_content)
        print(f"Updated {filepath}")
    else:
        print(f"No changes made to {filepath} (Version string {current_ver} not found?)")

def update_flatpak_meta(new_ver):
    filepath = FLATPAK_META
    if not os.path.exists(filepath):
        return

    with open(filepath, "r") as f:
        lines = f.readlines()

    today = datetime.date.today().isoformat()
    new_release_tag = f'    <release version="{new_ver}" date="{today}">\n    </release>\n'

    new_lines = []
    inserted = False
    for line in lines:
        new_lines.append(line)
        if '<releases>' in line and not inserted:
            new_lines.append(new_release_tag)
            inserted = True

    with open(filepath, "w") as f:
        f.writelines(new_lines)
    print(f"Updated {filepath}")

def update_readme_changelog(new_ver, changes):
    filepath = "README.md"
    if not os.path.exists(filepath):
        return

    with open(filepath, "r") as f:
        content = f.read()

    header = "## 🆕 Latest Changes"
    entry = f"\n### v{new_ver}\n{changes}\n"

    if header in content:
        # Insert after header
        content = content.replace(header, f"{header}{entry}")
    else:
        # Insert header after the badges or description
        # Looking for the first separator ---
        if "---" in content:
            content = content.replace("---", f"---\n\n{header}{entry}", 1)
        else:
            content += f"\n\n{header}{entry}"

    with open(filepath, "w") as f:
        f.write(content)
    print(f"Updated Changelog in {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Automate GRUB Settings Release")
    parser.add_argument("part", choices=["major", "minor", "patch"], help="Version part to bump")
    parser.add_argument("--dry-run", action="store_true", help="Don't touch files or git")
    args = parser.parse_args()

    current_ver = get_current_version()
    new_ver = bump_version(current_ver, args.part)
    changes = get_git_changes()

    print(f"🚀 Preparing Release: v{current_ver} -> v{new_ver}")
    print("\n📝 Changes:")
    print(changes)
    print("-" * 30)

    if args.dry_run:
        print("Dry run complete. No files changed.")
        return

    # Update Code Files
    for filepath, patterns in FILES_TO_UPDATE.items():
        update_file_content(filepath, current_ver, new_ver, patterns)

    # Update Metadata
    update_flatpak_meta(new_ver)
    update_readme_changelog(new_ver, changes)

    # Git Operations
    print("\n📦 Git Operations...")
    run_command("git add .")
    run_command(f'git commit -m "chore: release v{new_ver}"')
    run_command(f'git tag v{new_ver}')

    print(f"\n✅ Release v{new_ver} created successfully!")
    print("👉 Run the following command to publish:")
    print("git push && git push --tags")

if __name__ == "__main__":
    main()
