# Grub Settings ⚙️

![Grub Settings Icon](assets/icon.png)

**A modern, user-friendly, and polite GRUB customizer for Linux.**

Grub Settings is a GUI tool designed to make managing your GRUB bootloader configuration safe, easy, and aesthetically pleasing. It abstracts away the complexity of editing `/etc/default/grub` manually.

## 🌟 Features

*   **Change Default OS:** Easily select which operating system boots by default.
*   **Timeout Control:** Adjust the countdown timer or hide the menu entirely.
*   **Appearance Customization:**
    *   Set custom background images.
    *   Change resolutions.
    *   Font support (DejaVu Sans included).
*   **OS Management:**
    *   Add/Remove Windows entries manually if OS Prober fails.
    *   Toggle OS Prober.
*   **Polite Authentication 🔐:**
    *   Starts without asking for passwords immediately.
    *   Prompts for `sudo` password only when you click "Apply" or change system files.
    *   Uses a custom, desktop-agnostic "Polite Dialog" that works on GNOME, KDE, XFCE, and Tiling WMs.
    *   Caches your session so you aren't asked repeatedly.
*   **Safe & Secure:**
    *   Backs up configuration before changes.
    *   Uses standard system tools (`update-grub`, `grub-mkconfig`).
    *   Does not run as root continuously.

## 🚀 Installation

### Option 1: Standalone (Portable)
Download the latest binary from the [Releases](https://github.com/taylan/grub-settings/releases) page.
1. Download `grub-settings`.
2. Make it executable:
   ```bash
   chmod +x grub-settings
   ```
3. Run it!
   ```bash
   ./grub-settings
   ```

### Option 2: Flatpak (Recommended)
Once published on Flathub, you can install it via:
```bash
flatpak install flathub io.github.taylan.grubsettings
```

## 🛠️ Building from Source

### Prerequisites
*   Python 3.8+
*   GTK4 and LibAdwaita
*   `sudo` access

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/taylan/grub-settings.git
   cd grub-settings
   ```
2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install pygobject pyinstaller
   ```
4. Run the app:
   ```bash
   python3 grub_settings.py
   ```

### Creating a Portable Executable
To build the single-file distribution:
```bash
pyinstaller --onefile --clean --name "grub-settings" --add-data "assets:assets" grub_settings.py
```
The output will be in the `dist/` folder.

## 📦 Flathub Submission

This repository includes all necessary files for Flathub submission in the `flatpak/` directory:
*   `io.github.taylan.grubsettings.yml` (Manifest)
*   `io.github.taylan.grubsettings.metainfo.xml` (AppStream Data)
*   `io.github.taylan.grubsettings.desktop` (Desktop Entry)

To test the Flatpak build locally:
```bash
flatpak-builder --user --install build-dir flatpak/io.github.taylan.grubsettings.yml --force-clean
```

## 📄 License
This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author
**Taylan Soylu** - [taylansoylu@gmail.com](mailto:taylansoylu@gmail.com)
