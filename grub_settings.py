#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GRUB Ayarları - Ubuntu için gelişmiş GRUB yapılandırma aracı
Her ayar için detaylı açıklamalar içerir

Version: 1.1
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GdkPixbuf, GLib, Gdk
import subprocess
import os
import sys
import logging
import shlex
import gettext
import locale
import json
from pathlib import Path

# ... (logging setup is here) ...

# ... (get_path function is here) ...

def get_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    path = os.path.join(base_path, relative_path)
    if os.path.exists(path):
        return path
        
    if IS_FLATPAK:
        flatpak_path = os.path.join("/app/share/grub-settings", relative_path)
        if os.path.exists(flatpak_path):
            return flatpak_path
            
    return path

def restart_app(app):
    """Uygulamayı yeniden başlat"""
    logger.info("Restarting application...")
    try:
        app.quit()
        # Küçük bir gecikme
        import time
        time.sleep(0.5)
        
        if getattr(sys, 'frozen', False):
            # PyInstaller ile derlenmiş
            # sys.executable, çalıştırılabilir dosyanın kendisidir
            # sys.argv[1:] argümanları korur
            os.execl(sys.executable, sys.executable, *sys.argv[1:])
        else:
            # Normal Python script
            python = sys.executable
            os.execl(python, python, *sys.argv)
    except Exception as e:
        logger.error(f"Restart failed: {e}")

class ConfigManager:
    """Uygulama ayarlarını yöneten sınıf"""
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "grub-settings"
        self.config_file = self.config_dir / "settings.json"
        self.config = self._load_config()

    def _load_config(self):
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Config yüklenemedi: {e}")
            return {}

    def save_config(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logging.error(f"Config kaydedilemedi: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

# Global Config
config_manager = ConfigManager()

# i18n Initialization
try:
    locales_dir = get_path("locales")
    saved_lang = config_manager.get("language", None)
    
    if saved_lang:
        # Load user preference
        lang_code = "tr" if "tr" in saved_lang else "en"
        t = gettext.translation('grub-settings', localedir=locales_dir, languages=[lang_code])
    else:
        # Auto-detect
        t = gettext.translation('grub-settings', localedir=locales_dir, fallback=True)
        
    t.install() # Installs _()
except Exception as e:
    logging.warning(f"i18n setup failed: {e}")
    import builtins
    builtins._ = lambda x: x

# Logging yapılandırması
log_dir = Path.home() / ".cache" / "grub-settings"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "app.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

APP_VERSION = "1.2.2"
import shutil

class PoliteAuthDialog(Gtk.Window):
    """Kibar ve şirin şifre isteme penceresi (Custom Window)"""
    def __init__(self, parent=None):
        try:
            super().__init__()
            logger.info("DEBUG: PoliteAuthDialog initializing...")
            
            self.set_title(_("Permission Required 🌸"))
            self.set_default_size(350, 300)
            self.set_resizable(False)
            self.set_modal(True)
            
            if parent:
                try:
                    self.set_transient_for(parent)
                    logger.info("DEBUG: Parent set successfully")
                except Exception as e:
                    logger.error(f"DEBUG: Failed to set parent: {e}")
            
            self._callback = None
    
            # Main Box
            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
            main_box.set_margin_top(24)
            main_box.set_margin_bottom(24)
            main_box.set_margin_start(24)
            main_box.set_margin_end(24)
            
            # Icon
            icon_label = Gtk.Label()
            icon_label.set_markup("<span size='40000'>🔐</span>")
            main_box.append(icon_label)
            
            # Title
            title = Gtk.Label(label=_("Permission Required"))
            title.add_css_class("title-2")
            main_box.append(title)
            
            # Body
            body_text = _("I need administrator permission to perform this action.\nCould you please enter your password? 🥺")
            body = Gtk.Label(label=body_text)
            body.set_justify(Gtk.Justification.CENTER)
            body.set_wrap(True)
            main_box.append(body)
            
            # Entry
            self.password_entry = Gtk.PasswordEntry()
            self.password_entry.set_property("placeholder-text", _("Sudo password"))
            self.password_entry.connect("activate", self.on_ok_clicked)
            self.password_entry.set_margin_top(8)
            self.password_entry.set_margin_bottom(8)
            main_box.append(self.password_entry)
            
            # Buttons
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            btn_box.set_halign(Gtk.Align.CENTER)
            btn_box.set_margin_top(8)
            
            cancel_btn = Gtk.Button(label=_("Cancel"))
            cancel_btn.connect("clicked", self.on_cancel_clicked)
            
            ok_btn = Gtk.Button(label=_("OK"))
            ok_btn.add_css_class("suggested-action")
            ok_btn.connect("clicked", self.on_ok_clicked)
            
            btn_box.append(cancel_btn)
            btn_box.append(ok_btn)
            main_box.append(btn_box)
            
            self.set_child(main_box)
            logger.info("DEBUG: PoliteAuthDialog initialized successfully")
            
        except Exception as e:
            logger.error(f"CRITICAL: PoliteAuthDialog init failed: {e}", exc_info=True)

    def set_callback(self, callback):
        self._callback = callback

    def on_ok_clicked(self, btn):
        if self._callback:
            self._callback(self, "ok")
            
    def on_cancel_clicked(self, btn):
        if self._callback:
            self._callback(self, "cancel")
            
    def get_password(self):
        return self.password_entry.get_text()


class GrubPaths:
    """Dağıtımına göre GRUB yollarını ve komutlarını belirle"""
    
    def __init__(self):
        self.distro_info = self._parse_os_release()
        self.grub_file = "/etc/default/grub"
        self.grub_cfg = self._detect_grub_cfg()
        self.efi_path = self._detect_efi_path()
        self.update_cmd = self._detect_update_command()
        
        logger.info(f"Dağıtım: {self.distro_info.get('ID', 'unknown')} ({self.distro_info.get('PRETTY_NAME', 'Unknown Linux')})")
        logger.info(f"GRUB Config: {self.grub_cfg}")
        logger.info(f"EFI Path: {self.efi_path}")
        logger.info(f"Update Command: {self.update_cmd}")

    def _parse_os_release(self):
        """Standard /etc/os-release parsing"""
        info = {}
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    for line in f:
                        if '=' in line:
                            k, v = line.strip().split('=', 1)
                            info[k] = v.strip('"')
        except Exception as e:
            logger.warning(f"OS release okunamadı: {e}")
        return info

    def _detect_grub_cfg(self):
        # Bilinen yolları kontrol et
        candidates = [
            "/boot/grub/grub.cfg",      # Debian, Ubuntu, Arch, Linux Mint
            "/boot/grub2/grub.cfg",     # Fedora, RHEL, SUSE, OpenMandriva
            "/boot/efi/EFI/fedora/grub.cfg", # Fedora some configs
            "/boot/efi/EFI/redhat/grub.cfg", # RHEL some configs
        ]
        
        # 1. Dosya var mı kontrol et
        for path in candidates:
            if os.path.exists(path):
                return path
                
        # 2. Bulunamadıysa varsayılanı döndür (Debian standardı)
        return "/boot/grub/grub.cfg"

    def _detect_efi_path(self):
        candidates = ["/boot/efi", "/efi", "/boot"]
        for path in candidates:
            if os.path.exists(os.path.join(path, "EFI")):
                return path
        return "/boot/efi" # Varsayılan

    def _detect_update_command(self):
        # Dağıtım bazlı tahmin
        distro_id = self.distro_info.get('ID', '').lower()
        distro_like = self.distro_info.get('ID_LIKE', '').lower()
        
        # 1. update-grub (Debian/Ubuntu türevleri)
        if shutil.which("update-grub"):
            return "update-grub"
            
        # 2. grub-mkconfig / grub2-mkconfig
        # Fedora/RHEL/SUSE genellikle grub2-mkconfig kullanır
        if 'fedora' in distro_id or 'rhel' in distro_id or 'suse' in distro_id or \
           'fedora' in distro_like or 'rhel' in distro_like or 'suse' in distro_like:
            if shutil.which("grub2-mkconfig"):
                return f"grub2-mkconfig -o {self.grub_cfg}"
        
        # Arch ve diğerleri genellikle grub-mkconfig kullanır
        if shutil.which("grub-mkconfig"):
            return f"grub-mkconfig -o {self.grub_cfg}"
            
        # Fallback: grub2-mkconfig varsa kullan (bazı custom distrolar)
        if shutil.which("grub2-mkconfig"):
            return f"grub2-mkconfig -o {self.grub_cfg}"
            
        return "update-grub" # En kötü durum fallback

# Global instance
PATHS = GrubPaths()
GRUB_FILE = PATHS.grub_file
GRUB_CFG_FILE = PATHS.grub_cfg


import re

def get_grub_menu_entries():
    """GRUB menü girdilerini oku ve liste olarak döndür"""
    entries = []
    try:
        # grub.cfg dosyasını okumaya çalış
        result = subprocess.run(
            ["pkexec", "cat", GRUB_CFG_FILE],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            content = result.stdout
            # menuentry 'Ubuntu' veya menuentry "Windows Boot Manager" formatlarını bul
            pattern = r"menuentry\s+['\"]([^'\"]+)['\"]"
            matches = re.findall(pattern, content)
            # Sadece ana menü girdilerini al (submenu içindekiler hariç)
            for match in matches:
                # Recovery ve eski kernel'ları filtrele (isteğe bağlı)
                if match not in entries:
                    entries.append(match)
    except subprocess.TimeoutExpired:
        logger.warning("GRUB menü okuma zaman aşımına uğradı")
    except Exception as e:
        logger.warning(f"GRUB menü okunamadı: {e}")
    
    # Eğer okuma başarısız olursa varsayılan liste
    if not entries:
        entries = ["0 - İlk Seçenek", "1 - İkinci Seçenek", "2 - Üçüncü Seçenek"]
    
    return entries

# Detaylı açıklamalar
# Detaylı açıklamalar
HELP_TEXTS = {
    "timeout": _("""<b>What is Menu Timeout?</b>

When your computer starts, the GRUB menu appears and waits for this duration.
During this time, you can choose which operating system to start.

<b>Recommendations:</b>
• <b>0 seconds:</b> Menu hidden, boots default system immediately
• <b>3-5 seconds:</b> Quick boot, gives time to choose if needed
• <b>10+ seconds:</b> Plenty of time to choose comfortably

<i>💡 Tip: 0-3 seconds is enough if you only use one operating system.</i>"""),

    "timeout_style": _("""<b>Menu Visibility Style</b>

<b>Show Menu:</b>
The GRUB menu appears every time the computer starts.
Recommended for multi-boot users.

<b>Hidden (Show with Shift):</b>
The menu is normally hidden. You can show it by holding down the Shift key.
Ideal for single-boot users who want a fast boot.

<b>Countdown:</b>
Only a countdown is shown, the full menu is not visible.
For those who want a minimalist look."""),

    "background": _("""<b>GRUB Background Image</b>

You can add a custom image to the background of the GRUB menu.

<b>Supported formats:</b> PNG, JPEG, TGA

<b>Recommended size:</b> Same as your screen resolution
(e.g., 1920x1080)

<i>💡 Tip: Darker images improve the readability of menu text.</i>"""),

    "resolution": _("""<b>GRUB Screen Resolution</b>

Determines the resolution at which the GRUB menu appears.

<b>auto:</b> The best resolution supported by your graphics card
<b>1920x1080:</b> Full HD - For modern screens
<b>1280x720:</b> HD - More compatible for older systems

<i>💡 Tip: If using a background image, select the same resolution as your image.</i>"""),

    "default_os": _("""<b>Default Operating System</b>

Determines which system starts automatically when the timeout expires.

<b>Order Number:</b>
• 0 = First system in the list (usually Ubuntu)
• 1 = Second system (usually Windows or older kernel)
• 2 = Third system... etc.

<i>💡 Tip: Check your order in the GRUB menu to determine the number.</i>"""),

    "os_prober": _("""<b>Operating System Detection (OS-Prober)</b>

When enabled, other operating systems on your computer
(Windows, other Linux distros, etc.) are automatically
added to the GRUB menu.

<b>On:</b> Other OSs appear in the menu
<b>Off:</b> Only this Linux system appears

<i>💡 Tip: Must be enabled if using Dual-boot (Windows + Linux)!</i>"""),

    "quiet": _("""<b>Quiet Mode (quiet)</b>

Determines whether kernel messages are shown during boot.

<b>On:</b> Technical messages hidden, clean boot screen
<b>Off:</b> All system messages shown (for debugging)

<i>💡 Tip: Leave on for normal use. Turn off to diagnose boot issues.</i>"""),

    "splash": _("""<b>Boot Animation (splash)</b>

Determines whether to show the Plymouth boot animation.
This is the screen where the Ubuntu logo spins or a progress bar is shown.

<b>On:</b> Beautiful animated boot screen
<b>Off:</b> Text-based boot on black screen

<i>💡 Tip: Leave on for a visual boot experience.</i>"""),

    "recovery": _("""<b>Recovery Mode Menu</b>

Whether to show recovery options under "Advanced options"
in the GRUB menu.

<b>On:</b> Troubleshooting options appear in the menu
<b>Off:</b> Menu looks cleaner

<i>💡 Tip: Recommended to keep on for emergencies!</i>"""),

    "savedefault": _("""<b>Remember Last Selection</b>

When enabled, the last operating system you booted
will be selected by default on the next boot."""),

    "submenu": _("""<b>Disable Submenus</b>

Old kernels and recovery modes are usually grouped under
"Advanced options" submenu.

<b>Submenu On:</b> Compact menu, access via submenu
<b>Submenu Off:</b> All options listed in main menu

<i>💡 Tip: You can disable this if you frequently access old kernels.</i>""")
}


class GrubConfig:
    """GRUB yapılandırma dosyasını okuma ve yazma"""
    
    def __init__(self):
        self.config = {}
        self.raw_content = ""
        self.load()
    
    def load(self):
        """GRUB ayarlarını oku"""
        try:
            if not os.path.exists(GRUB_FILE):
                logger.error(f"GRUB dosyası bulunamadı: {GRUB_FILE}")
                return False
            
            with open(GRUB_FILE, 'r', encoding='utf-8') as f:
                self.raw_content = f.read()
            
            self.config.clear()
            for line in self.raw_content.splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    self.config[key] = value
            
            logger.info(f"GRUB konfigürasyonu yüklendi: {len(self.config)} ayar")
            return True
        except PermissionError:
            logger.error("GRUB dosyasını okumak için yetki yok")
            return False
        except Exception as e:
            logger.error(f"GRUB dosyası okunamadı: {e}")
            return False
    
    def get(self, key, default=""):
        """Bir ayar değerini al"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Bir ayar değerini ayarla"""
        self.config[key] = str(value)
        logger.debug(f"Ayar değiştirildi: {key} = {value}")
    
    def remove(self, key):
        """Bir ayarı kaldır"""
        if key in self.config:
            del self.config[key]
            logger.debug(f"Ayar kaldırıldı: {key}")
    
    def generate_config(self):
        lines = []
        processed_keys = set()
        
        for line in self.raw_content.splitlines():
            stripped = line.strip()
            
            if not stripped or stripped.startswith('#'):
                if stripped.startswith('#') and '=' in stripped:
                    comment_content = stripped[1:].strip()
                    if '=' in comment_content:
                        key = comment_content.split('=', 1)[0].strip()
                        if key in self.config and key not in processed_keys:
                            value = self.config[key]
                            if ' ' in str(value) or any(c in str(value) for c in ['$', '`', '"']):
                                lines.append(f'{key}="{value}"')
                            else:
                                lines.append(f'{key}={value}')
                            processed_keys.add(key)
                            continue
                lines.append(line)
                continue
            
            if '=' in stripped:
                key = stripped.split('=', 1)[0]
                if key in self.config:
                    value = self.config[key]
                    if ' ' in str(value) or any(c in str(value) for c in ['$', '`', '"']):
                        lines.append(f'{key}="{value}"')
                    else:
                        lines.append(f'{key}={value}')
                    processed_keys.add(key)
                else:
                    lines.append(line)
            else:
                lines.append(line)
        
        for key, value in self.config.items():
            if key not in processed_keys:
                if ' ' in str(value) or any(c in str(value) for c in ['$', '`', '"']):
                    lines.append(f'{key}="{value}"')
                else:
                    lines.append(f'{key}={value}')
        
        return '\n'.join(lines)


def create_help_button(help_key, parent_window):
    """Yardım butonu oluştur"""
    btn = Gtk.Button()
    btn.set_icon_name("dialog-question-symbolic")
    btn.add_css_class("flat")
    btn.add_css_class("circular")
    btn.set_valign(Gtk.Align.CENTER)
    btn.set_tooltip_text("Bu ayar hakkında bilgi al")
    
    def show_help(button):
        dialog = Adw.MessageDialog.new(parent_window)
        dialog.set_heading("ℹ️ Bilgi")
        dialog.set_body_use_markup(True)
        dialog.set_body(HELP_TEXTS.get(help_key, "Açıklama bulunamadı."))
        dialog.add_response("ok", "Anladım")
        dialog.present()
    
    btn.connect("clicked", show_help)
    return btn


class TimingPage(Gtk.Box):
    """Zamanlama ayarları sayfası"""
    
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.app = app
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        # Scrollable content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        
        # Başlık
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_icon = Gtk.Label(label="⏱️")
        title_icon.add_css_class("title-1")
        title = Gtk.Label(label=_("Timing Settings"))
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        header_box.append(title_icon)
        header_box.append(title)
        content.append(header_box)
        
        # Açıklama
        desc = Gtk.Label(label=_("Adjust how long the GRUB menu appears when the computer starts."))
        desc.add_css_class("dim-label")
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)
        content.append(desc)
        
        # Timeout Group
        timeout_group = Adw.PreferencesGroup()
        timeout_group.set_title(_("⏰ Timeout Duration"))
        timeout_group.set_description(_("Time to display GRUB menu (in seconds)"))
        
        # Timeout slider row
        timeout_row = Adw.ActionRow()
        timeout_row.set_title(_("Duration"))
        timeout_row.set_subtitle(_("0 = Menu hidden, boots immediately"))
        timeout_row.add_prefix(create_help_button("timeout", app.win))
        
        slider_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        slider_box.set_valign(Gtk.Align.CENTER)
        
        self.timeout_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 30, 1)
        self.timeout_scale.set_size_request(200, -1)
        self.timeout_scale.add_mark(0, Gtk.PositionType.BOTTOM, "0")
        self.timeout_scale.add_mark(5, Gtk.PositionType.BOTTOM, "5")
        self.timeout_scale.add_mark(10, Gtk.PositionType.BOTTOM, "10")
        self.timeout_scale.add_mark(30, Gtk.PositionType.BOTTOM, "30")
        
        current_timeout = 0
        try:
            current_timeout = int(app.grub_config.get("GRUB_TIMEOUT", "0"))
        except (ValueError, TypeError):
            pass
        self.timeout_scale.set_value(min(current_timeout, 30))
        
        self.timeout_label = Gtk.Label()
        self.timeout_label.set_width_chars(8)
        self.timeout_label.add_css_class("title-3")
        self.update_timeout_label(current_timeout)
        
        self.timeout_scale.connect("value-changed", self.on_timeout_changed)
        
        slider_box.append(self.timeout_scale)
        slider_box.append(self.timeout_label)
        timeout_row.add_suffix(slider_box)
        
        timeout_group.add(timeout_row)
        content.append(timeout_group)
        
        # Menü Stili Group
        style_group = Adw.PreferencesGroup()
        style_group.set_title(_("👁️ Menu Visibility"))
        style_group.set_description(_("Choose how the GRUB menu is displayed"))
        
        current_style = app.grub_config.get("GRUB_TIMEOUT_STYLE", "menu")
        
        # Menu visible
        style_row1 = Adw.ActionRow()
        style_row1.set_title(_("Show Menu"))
        style_row1.set_subtitle(_("GRUB menu is fully visible on every boot"))
        style_row1.add_prefix(create_help_button("timeout_style", app.win))
        self.style_menu = Gtk.CheckButton()
        self.style_menu.set_active(current_style == "menu")
        style_row1.add_suffix(self.style_menu)
        style_row1.set_activatable_widget(self.style_menu)
        
        # Hidden
        style_row2 = Adw.ActionRow()
        style_row2.set_title(_("Hidden"))
        style_row2.set_subtitle(_("Show by holding down the Shift key"))
        self.style_hidden = Gtk.CheckButton()
        self.style_hidden.set_group(self.style_menu)
        self.style_hidden.set_active(current_style == "hidden")
        style_row2.add_suffix(self.style_hidden)
        style_row2.set_activatable_widget(self.style_hidden)
        
        # Countdown
        style_row3 = Adw.ActionRow()
        style_row3.set_title(_("Countdown"))
        style_row3.set_subtitle(_("Only the remaining time is shown"))
        self.style_countdown = Gtk.CheckButton()
        self.style_countdown.set_group(self.style_menu)
        self.style_countdown.set_active(current_style == "countdown")
        style_row3.add_suffix(self.style_countdown)
        style_row3.set_activatable_widget(self.style_countdown)
        
        style_group.add(style_row1)
        style_group.add(style_row2)
        style_group.add(style_row3)
        content.append(style_group)
        
        scrolled.set_child(content)
        self.append(scrolled)
    
    def update_timeout_label(self, value):
        if value == 0:
            self.timeout_label.set_label(_("Off"))
        else:
            self.timeout_label.set_label(f"{int(value)} s")
    
    def on_timeout_changed(self, scale):
        value = int(scale.get_value())
        self.update_timeout_label(value)
        self.app.mark_changed()
    
    def get_values(self):
        style = "menu"
        if self.style_hidden.get_active():
            style = "hidden"
        elif self.style_countdown.get_active():
            style = "countdown"
        
        values = {
            "GRUB_TIMEOUT": str(int(self.timeout_scale.get_value())),
            "GRUB_TIMEOUT_STYLE": style
        }
        
        return values


class AdvancedPage(Gtk.Box):
    """Advanced settings page"""
    
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.app = app
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        
        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_icon = Gtk.Label(label="🔧")
        title_icon.add_css_class("title-1")
        title = Gtk.Label(label=_("Advanced Settings"))
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        header_box.append(title_icon)
        header_box.append(title)
        content.append(header_box)
        
        desc = Gtk.Label(label=_("Customize kernel parameters and boot behavior."))
        desc.add_css_class("dim-label")
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)
        content.append(desc)
        
        # Warning
        warning_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        warning_box.add_css_class("card")
        warning_box.add_css_class("warning-card")
        warning_box.set_margin_bottom(8)
        warning_icon = Gtk.Label(label="⚠️")
        warning_label = Gtk.Label(label=_("Settings in this section may affect system boot. Be careful!"))
        warning_label.set_wrap(True)
        warning_box.append(warning_icon)
        warning_box.append(warning_label)
        content.append(warning_box)
        
        current_params = app.grub_config.get("GRUB_CMDLINE_LINUX_DEFAULT", "quiet splash")
        
        # Boot Display Group
        display_group = Adw.PreferencesGroup()
        display_group.set_title(_("🖥️ Boot Display"))
        display_group.set_description(_("What to show on screen during boot"))
        
        self.quiet_switch = Adw.SwitchRow()
        self.quiet_switch.set_title(_("Quiet Boot (quiet)"))
        self.quiet_switch.set_subtitle(_("Hide technical messages, clean boot"))
        self.quiet_switch.add_prefix(create_help_button("quiet", app.win))
        self.quiet_switch.set_active("quiet" in current_params)
        self.quiet_switch.connect("notify::active", lambda *a: app.mark_changed())
        
        self.splash_switch = Adw.SwitchRow()
        self.splash_switch.set_title(_("Boot Animation (splash)"))
        self.splash_switch.set_subtitle(_("Beautiful boot screen with logo"))
        self.splash_switch.add_prefix(create_help_button("splash", app.win))
        self.splash_switch.set_active("splash" in current_params)
        self.splash_switch.connect("notify::active", lambda *a: app.mark_changed())
        
        display_group.add(self.quiet_switch)
        display_group.add(self.splash_switch)
        content.append(display_group)
        
        # Recovery Group
        recovery_group = Adw.PreferencesGroup()
        recovery_group.set_title(_("🛠️ Recovery Options"))
        recovery_group.set_description(_("Troubleshooting and recovery mode"))
        
        self.recovery_switch = Adw.SwitchRow()
        self.recovery_switch.set_title(_("Show Recovery Mode"))
        self.recovery_switch.set_subtitle(_("Show recovery options in GRUB"))
        self.recovery_switch.add_prefix(create_help_button("recovery", app.win))
        
        current_recovery = app.grub_config.get("GRUB_DISABLE_RECOVERY", "")
        self.recovery_switch.set_active(current_recovery.lower() != "true")
        self.recovery_switch.connect("notify::active", lambda *a: app.mark_changed())
        
        recovery_group.add(self.recovery_switch)
        
        recovery_tip = Adw.ActionRow()
        recovery_tip.set_title(_("💡 Tip"))
        recovery_tip.set_subtitle(_("Recovery mode can be a lifesaver if system fails to boot!"))
        recovery_group.add(recovery_tip)
        
        content.append(recovery_group)
        
        # Custom Parameters
        custom_group = Adw.PreferencesGroup()
        custom_group.set_title(_("⌨️ Custom Kernel Parameters"))
        custom_group.set_description(_("For advanced users"))
        
        self.custom_entry = Adw.EntryRow()
        self.custom_entry.set_title(_("Kernel Parameters"))
        
        # Get custom params (exclude quiet and splash)
        custom_params = [p for p in current_params.split() if p not in ["quiet", "splash"]]
        self.custom_entry.set_text(" ".join(custom_params))
        self.custom_entry.connect("changed", lambda *a: app.mark_changed())
        
        custom_group.add(self.custom_entry)
        
        custom_info = Adw.ActionRow()
        custom_info.set_title(_("Example parameters"))
        
        # Remember Last Selection
        remember_group = Adw.PreferencesGroup()
        remember_group.set_title(_("💾 Remember Last Selection"))
        remember_group.set_description(_("Default to the last booted system"))
        
        self.savedefault_switch = Adw.SwitchRow()
        self.savedefault_switch.set_title(_("Remember Last Selection"))
        self.savedefault_switch.set_subtitle(_("The last used OS will be selected on next boot"))
        self.savedefault_switch.add_prefix(create_help_button("savedefault", app.win))
        
        current_default = app.grub_config.get("GRUB_DEFAULT", "0")
        self.savedefault_switch.set_active(current_default == "saved")
        self.savedefault_switch.connect("notify::active", lambda *a: app.mark_changed())
        
        remember_group.add(self.savedefault_switch)
        content.append(remember_group)
        
        scrolled.set_child(content)
        self.append(scrolled)
    
    def update_timeout_label(self, value):
        if value == 0:
            self.timeout_label.set_label("Kapalı")
        else:
            self.timeout_label.set_label(f"{int(value)} saniye")
    
    def on_timeout_changed(self, scale):
        value = int(scale.get_value())
        self.update_timeout_label(value)
        self.app.mark_changed()
    
    def get_values(self):
        style = "menu"
        if self.style_hidden.get_active():
            style = "hidden"
        elif self.style_countdown.get_active():
            style = "countdown"
        
        values = {
            "GRUB_TIMEOUT": str(int(self.timeout_scale.get_value())),
            "GRUB_TIMEOUT_STYLE": style
        }
        
        if self.savedefault_switch.get_active():
            values["GRUB_DEFAULT"] = "saved"
            values["GRUB_SAVEDEFAULT"] = "true"
        
        return values


class AppearancePage(Gtk.Box):
    """Görünüm ayarları sayfası"""
    
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.app = app
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        self.selected_background = None
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        
        # Başlık
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_icon = Gtk.Label(label="🎨")
        title_icon.add_css_class("title-1")
        title = Gtk.Label(label=_("Appearance Settings"))
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        header_box.append(title_icon)
        header_box.append(title)
        content.append(header_box)
        
        desc = Gtk.Label(label=_("Customize the visual appearance of the GRUB menu."))
        desc.add_css_class("dim-label")
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)
        content.append(desc)
        
        # Background Group
        bg_group = Adw.PreferencesGroup()
        bg_group.set_title(_("🖼️ Background Image"))
        bg_group.set_description(_("Select a custom background image for the GRUB menu"))
        
        # Info row
        info_row = Adw.ActionRow()
        info_row.set_title(_("Supported Formats"))
        info_row.set_subtitle(_("PNG, JPEG, TGA - Should match your screen resolution"))
        info_row.add_prefix(create_help_button("background", app.win))
        bg_group.add(info_row)
        
        # Preview frame
        preview_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        preview_container.set_margin_top(12)
        preview_container.set_margin_bottom(12)
        
        self.preview_frame = Gtk.Frame()
        self.preview_frame.set_size_request(-1, 180)
        self.preview_frame.add_css_class("card")
        
        self.preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.preview_box.set_valign(Gtk.Align.CENTER)
        self.preview_box.set_halign(Gtk.Align.CENTER)
        
        self.preview_image = Gtk.Picture()
        self.preview_image.set_size_request(300, 169)
        self.preview_image.set_content_fit(Gtk.ContentFit.CONTAIN)
        
        self.no_image_label = Gtk.Label(label=_("🖼️ No background image selected\nClick the button below to select an image"))
        self.no_image_label.add_css_class("dim-label")
        self.no_image_label.set_justify(Gtk.Justification.CENTER)
        
        self.preview_box.append(self.no_image_label)
        self.preview_frame.set_child(self.preview_box)
        preview_container.append(self.preview_frame)
        
        # Check existing
        current_bg = app.grub_config.get("GRUB_BACKGROUND", "")
        if current_bg and os.path.exists(current_bg):
            self.set_preview_image(current_bg, mark_as_changed=False)
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.CENTER)
        
        select_btn = Gtk.Button()
        select_btn_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        select_btn_content.append(Gtk.Label(label="📁"))
        select_btn_content.append(Gtk.Label(label=_("Select Image")))
        select_btn.set_child(select_btn_content)
        select_btn.add_css_class("suggested-action")
        select_btn.add_css_class("pill")
        select_btn.connect("clicked", self.on_select_image)
        
        remove_btn = Gtk.Button()
        remove_btn_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        remove_btn_content.append(Gtk.Label(label="🗑️"))
        remove_btn_content.append(Gtk.Label(label=_("Remove")))
        remove_btn.set_child(remove_btn_content)
        remove_btn.add_css_class("destructive-action")
        remove_btn.add_css_class("pill")
        remove_btn.connect("clicked", self.on_remove_image)
        
        button_box.append(select_btn)
        button_box.append(remove_btn)
        preview_container.append(button_box)
        
        bg_group.add(preview_container)
        content.append(bg_group)
        
        # Resolution Group
        res_group = Adw.PreferencesGroup()
        res_group.set_title(_("📺 Screen Resolution"))
        res_group.set_description(_("Resolution to display the GRUB menu"))
        
        res_row = Adw.ComboRow()
        res_row.set_title(_("Screen Resolution"))
        res_row.set_subtitle(_("Select a value supported by your graphics card"))
        res_row.add_prefix(create_help_button("resolution", app.win))
        
        # ... logic for resolution model ...
        
        # ============ LANGUAGE SELECTION (Moved Here) ============
        lang_group = Adw.PreferencesGroup()
        lang_group.set_title(_("Language Settings"))
        lang_group.set_description(_("Select application language"))
        
        # Language Selection
        lang_row = Adw.ComboRow()
        lang_row.set_title(_("Application Language"))
        lang_row.set_subtitle(_("Changes require restart"))
        lang_row.set_icon_name("preferences-desktop-locale-symbolic")
        
        lang_model = Gtk.StringList()
        lang_model.append("System Default 🌍")
        lang_model.append("English (en) 🇬🇧")
        lang_model.append("Türkçe (tr) 🇹🇷")
        lang_row.set_model(lang_model)
        
        # Determine current language
        current_lang = config_manager.get("language", "default")
        if "tr" in current_lang:
            lang_row.set_selected(2)
        elif "en" in current_lang:
            lang_row.set_selected(1)
        else:
            lang_row.set_selected(0)
            
        lang_row.connect("notify::selected", self.on_language_changed)
        lang_group.add(lang_row)
        
        content.append(lang_group)

        # Resolution Group - continuing
        resolutions = ["auto - Automatic", "1920x1080 - Full HD", "1680x1050", "1600x900", 
                       "1440x900", "1366x768 - HD", "1280x1024", "1280x720 - HD", 
                       "1024x768", "800x600"]
        res_model = Gtk.StringList.new(resolutions)
        res_row.set_model(res_model)
        
        current_res = app.grub_config.get("GRUB_GFXMODE", "auto")
        for i, r in enumerate(resolutions):
            if current_res in r:
                res_row.set_selected(i)
                break
        
        self.res_row = res_row
        self.resolutions = resolutions
        res_group.add(res_row)
        content.append(res_group)
        
        # Theme colors (bonus feature)
        theme_group = Adw.PreferencesGroup()
        theme_group.set_title(_("🎨 Menu Colors"))
        theme_group.set_description(_("Customize GRUB menu colors (coming soon)"))
        
        theme_info = Adw.ActionRow()
        theme_info.set_title(_("Theme Customization"))
        theme_info.set_subtitle(_("This feature will be added in a future version"))
        theme_info.set_sensitive(False)
        theme_group.add(theme_info)
        content.append(theme_group)
        
        scrolled.set_child(content)
        self.append(scrolled)
    
    def on_language_changed(self, row, pspec):
        selected_idx = row.get_selected()
        new_lang = "default"
        if selected_idx == 1:
            new_lang = "en"
        elif selected_idx == 2:
            new_lang = "tr"
            
        current = config_manager.get("language", "default")
        
        # Checking if change is needed
        if new_lang != current:
            config_manager.set("language", new_lang)
            logger.info(f"Language changed to {new_lang}")
            
            # Kibar restart diyaloğu
            dialog = PoliteAuthDialog(self.app.win) 
            dialog.set_title(_("Restart Required 🔄"))
            
            # İçeriği manuel değiştir
            main_box = dialog.get_child()
            
            # Icon
            main_box.get_first_child().set_markup("<span size='40000'>🔄</span>")
            
            # Title
            title_lbl = main_box.get_first_child().get_next_sibling()
            title_lbl.set_label(_("Language Changed"))
            
            # Body
            body_lbl = title_lbl.get_next_sibling()
            body_lbl.set_label(_("To apply the new language, I need to make a tiny restart.\nIs that okay correctly? 🥺"))
            
            # Entry (gizle)
            entry = body_lbl.get_next_sibling()
            entry.set_visible(False)
            
            # Buttons
            btn_box = entry.get_next_sibling()
            # Cancel
            btn_box.get_first_child().set_label(_("Later"))
            # OK
            ok_btn = btn_box.get_last_child()
            ok_btn.set_label(_("Restart Now"))
            
            def on_response(d, resp):
                if resp == "ok":
                    d.close()
                    restart_app(self.app)
                else:
                    d.close()
                    
            dialog.set_callback(on_response)
            dialog.present()

    def set_preview_image(self, path, mark_as_changed=True):
        """Set preview image. mark_as_changed=False used when loading existing setting."""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 300, 169, True)
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.preview_image.set_paintable(texture)
            
            if self.no_image_label.get_parent():
                self.preview_box.remove(self.no_image_label)
            if self.preview_image.get_parent() is None:
                self.preview_box.append(self.preview_image)
            
            self.selected_background = path
            if mark_as_changed:
                self.app.mark_changed()
        except Exception as e:
            logger.warning(f"Could not load image: {e}")
    
    def on_select_image(self, button):
        dialog = Gtk.FileDialog.new()
        dialog.set_title(_("Select Background Image"))
        
        filter_images = Gtk.FileFilter()
        filter_images.set_name(_("Image Files (PNG, JPEG, TGA)"))
        filter_images.add_mime_type("image/png")
        filter_images.add_mime_type("image/jpeg")
        filter_images.add_mime_type("image/x-tga")
        filter_images.add_pattern("*.tga")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_images)
        dialog.set_filters(filters)
        
        dialog.open(self.app.win, None, self.on_file_selected)
    
    def on_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                self.set_preview_image(file.get_path())
        except GLib.Error:
            # User cancelled or parsing error
            pass
    
    def on_remove_image(self, button):
        if self.preview_image.get_parent():
            self.preview_box.remove(self.preview_image)
        if self.no_image_label.get_parent() is None:
            self.preview_box.append(self.no_image_label)
        self.selected_background = None
        self.app.mark_changed()
    
    def get_values(self):
        values = {}
        
        selected = self.res_row.get_selected()
        if selected < len(self.resolutions):
            res = self.resolutions[selected].split(" - ")[0].split()[0]
            values["GRUB_GFXMODE"] = res
        
        if self.selected_background:
            # Dosya zaten /boot/grub dizinindeyse kopyalamaya gerek yok
            if self.selected_background.startswith("/boot/grub/"):
                values["GRUB_BACKGROUND"] = self.selected_background
            else:
                # Yeni dosya - hedef yolu oluştur ve kopyalama için kaynak yolu sakla
                ext = os.path.splitext(self.selected_background)[1].lower()
                if ext == ".jpeg":
                    ext = ".jpg"
                values["GRUB_BACKGROUND"] = f"/boot/grub/background{ext}"
                values["_ORIGINAL_BACKGROUND"] = self.selected_background
            
            # Resim varsa gfxterm zorunlu
            values["GRUB_TERMINAL_OUTPUT"] = "gfxterm"
        
        return values


class SystemPage(Gtk.Box):
    """Sistem ayarları sayfası"""
    
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.app = app
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        # Windows algılama bilgileri
        self.windows_detected = False
        self.windows_efi_path = None
        self.efi_uuid = None
        self.windows_in_grub = False
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        
        # Başlık
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_icon = Gtk.Label(label="💻")
        title_icon.add_css_class("title-1")
        title = Gtk.Label(label=_("System Settings"))
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        header_box.append(title_icon)
        header_box.append(title)
        content.append(header_box)
        
        desc = Gtk.Label(label=_("Configure operating system selection and dual-boot settings."))
        desc.add_css_class("dim-label")
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)
        content.append(desc)
        
        # ============ WINDOWS MANAGEMENT SECTION ============
        self.windows_group = Adw.PreferencesGroup()
        self.windows_group.set_title(_("🪟 Windows Management"))
        self.windows_group.set_description(_("Add Windows Boot Manager to the GRUB menu"))
        
        # Windows status row
        self.windows_status_row = Adw.ActionRow()
        self.windows_status_row.set_title(_("Windows Status"))
        self.windows_status_row.set_subtitle(_("Detecting..."))
        
        # Windows add/remove button
        self.windows_action_btn = Gtk.Button()
        self.windows_action_btn.set_valign(Gtk.Align.CENTER)
        self.windows_action_btn.add_css_class("suggested-action")
        self.windows_action_btn.add_css_class("pill")
        self.windows_action_btn.connect("clicked", self.on_windows_action)
        self.windows_status_row.add_suffix(self.windows_action_btn)
        
        self.windows_group.add(self.windows_status_row)
        
        # Info row
        self.windows_info_row = Adw.ActionRow()
        self.windows_info_row.set_title(_("💡 Info"))
        self.windows_info_row.set_subtitle(_("If OS-Prober cannot detect Windows, you can add it manually."))
        self.windows_group.add(self.windows_info_row)
        
        content.append(self.windows_group)
        
        # Start detection (background)
        GLib.idle_add(self.detect_windows)

        # ============ DEFAULT OS SECTION ============
        # Default OS Group
        default_group = Adw.PreferencesGroup()
        default_group.set_title(_("🎯 Default Operating System"))
        default_group.set_description(_("Which system should start when the timeout expires?"))
        
        # Use placeholders initially
        self.menu_entries = [_("0 - First Option"), _("1 - Second Option"), _("2 - Third Option")]
        
        self.default_combo = Adw.ComboRow()
        self.default_combo.set_title(_("Default System"))
        self.default_combo.set_subtitle(_("Click refresh to load the menu"))
        self.default_combo.add_prefix(create_help_button("default_os", app.win))
        
        # Refresh button
        refresh_btn = Gtk.Button()
        refresh_btn.set_icon_name("view-refresh-symbolic")
        refresh_btn.set_valign(Gtk.Align.CENTER)
        refresh_btn.set_tooltip_text(_("Load GRUB menu (requires root privileges)"))
        refresh_btn.connect("clicked", self.on_refresh_menu)
        self.default_combo.add_suffix(refresh_btn)
        
        # Add items to dropdown
        menu_model = Gtk.StringList.new(self.menu_entries)
        self.default_combo.set_model(menu_model)
        
        # Select current setting
        current_default = app.grub_config.get("GRUB_DEFAULT", "0")
        self.saved_default = current_default
        try:
            if current_default != "saved":
                default_index = int(current_default)
                if 0 <= default_index < len(self.menu_entries):
                    self.default_combo.set_selected(default_index)
        except (ValueError, TypeError):
            pass
        
        self.default_combo.connect("notify::selected", lambda *a: app.mark_changed())
        
        default_group.add(self.default_combo)
        content.append(default_group)
        
        # OS Prober Group
        prober_group = Adw.PreferencesGroup()
        prober_group.set_title(_("🔍 OS Detection"))
        prober_group.set_description(_("Add other operating systems to the GRUB menu"))
        
        self.prober_switch = Adw.SwitchRow()
        self.prober_switch.set_title(_("Show Other Operating Systems (OS Prober)"))
        self.prober_switch.set_subtitle(_("Automatically detects Windows and other Linux distros."))
        self.prober_switch.add_prefix(create_help_button("os_prober", app.win))
        
        current_prober = app.grub_config.get("GRUB_DISABLE_OS_PROBER", "true")
        self.prober_switch.set_active(current_prober.lower() == "false")
        self.prober_switch.connect("notify::active", lambda *a: app.mark_changed())
        
        prober_group.add(self.prober_switch)
        
        # Warning for OS prober
        prober_warning = Adw.ActionRow()
        prober_warning.set_title(_("⚠️ Dual-boot Users"))
        prober_warning.set_subtitle(_("This must be enabled if you have Windows or another OS!"))
        prober_warning.add_css_class("warning")
        prober_group.add(prober_warning)
        
        content.append(prober_group)
        
        # Submenu Group
        submenu_group = Adw.PreferencesGroup()
        submenu_group.set_title(_("📂 Menu Organization"))
        submenu_group.set_description(_("Display of old kernels and recovery options"))
        
        self.submenu_switch = Adw.SwitchRow()
        self.submenu_switch.set_title(_("Use Submenus"))
        self.submenu_switch.set_subtitle(_("Group old kernels and recovery options in a submenu"))
        self.submenu_switch.add_prefix(create_help_button("submenu", app.win))
        
        current_submenu = app.grub_config.get("GRUB_DISABLE_SUBMENU", "")
        self.submenu_switch.set_active(current_submenu.lower() != "true")
        self.submenu_switch.connect("notify::active", lambda *a: app.mark_changed())
        
        submenu_group.add(self.submenu_switch)
        content.append(submenu_group)
        
        scrolled.set_child(content)
        self.append(scrolled)
    
    def on_language_changed(self, row, pspec):
        selected_idx = row.get_selected()
        new_lang = "default"
        if selected_idx == 1:
            new_lang = "en"
        elif selected_idx == 2:
            new_lang = "tr"
            
        current = config_manager.get("language", "default")
        # "tr" in "default" is false. "en" in "default" is false.
        # But if current is "tr", and new is "tr", we don't change.
        # Logic in init was:
        # current_lang = config_manager.get("language", "default")
        # if "tr" in current_lang: index 2
        
        # Checking if change is needed
        if new_lang != current:
            config_manager.set("language", new_lang)
            logger.info(f"Language changed to {new_lang}")
            
            # Kibar restart diyaloğu
            dialog = PoliteAuthDialog(self.app.win) 
            dialog.set_title(_("Restart Required 🔄"))
            
            # İçeriği manuel değiştir (biraz hacky ama sınıfı yeniden yapmaktan kolay)
            # Child yapısını biliyoruz: main_box -> children
            main_box = dialog.get_child()
            # 0: icon, 1: title, 2: body, 3: entry, 4: buttons
            
            # Icon
            main_box.get_first_child().set_markup("<span size='40000'>🔄</span>")
            
            # Title
            title_lbl = main_box.get_first_child().get_next_sibling()
            title_lbl.set_label(_("Language Changed"))
            
            # Body
            body_lbl = title_lbl.get_next_sibling()
            body_lbl.set_label(_("To apply the new language, I need to make a tiny restart.\nIs that okay correctly? 🥺"))
            
            # Entry (gizle)
            entry = body_lbl.get_next_sibling()
            entry.set_visible(False)
            
            # Buttons
            btn_box = entry.get_next_sibling()
            # Cancel
            btn_box.get_first_child().set_label(_("Later"))
            # OK
            ok_btn = btn_box.get_last_child()
            ok_btn.set_label(_("Restart Now"))
            
            def on_response(d, resp):
                if resp == "ok":
                    d.close()
                    restart_app(self.app)
                else:
                    d.close()
                    
            dialog.set_callback(on_response)
            dialog.present()

    def detect_windows(self):
        """Windows EFI dosyalarını ve GRUB durumunu algıla"""
        try:
            # Windows EFI dosyasını kontrol et
            windows_efi = os.path.join(PATHS.efi_path, "EFI/Microsoft/Boot/bootmgfw.efi")
            if os.path.exists(windows_efi):
                self.windows_detected = True
                self.windows_efi_path = windows_efi
                
                # EFI partition UUID'sini al
                try:
                    result = subprocess.run(
                        ["findmnt", "-n", "-o", "UUID", PATHS.efi_path],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        self.efi_uuid = result.stdout.strip()
                except Exception as e:
                    logger.warning(f"EFI UUID alınamadı: {e}")
            
            # GRUB'da Windows var mı kontrol et
            custom_script = "/etc/grub.d/40_custom_windows"
            if os.path.exists(custom_script):
                self.windows_in_grub = True
            else:
                # grub.cfg'de de kontrol et
                try:
                    result = subprocess.run(
                        ["pkexec", "grep", "-l", "Windows", GRUB_CFG_FILE],
                        capture_output=True, text=True, timeout=10
                    )
                    self.windows_in_grub = result.returncode == 0
                except Exception:
                    pass
            
            # UI'ı güncelle
            self.update_windows_ui()
            
        except Exception as e:
            logger.error(f"Windows algılama hatası: {e}")
            self.windows_status_row.set_subtitle("❌ Algılama hatası")
        
        return False  # GLib.idle_add için bir kez çalışsın
    
    def update_windows_ui(self):
        """Windows bölümü UI'ını güncelle"""
        if self.windows_detected:
            if self.windows_in_grub:
                self.windows_status_row.set_title("✅ Windows Algılandı ve Menüde")
                self.windows_status_row.set_subtitle(f"EFI: {self.windows_efi_path}")
                self.windows_action_btn.set_label("🗑️ Menüden Kaldır")
                self.windows_action_btn.remove_css_class("suggested-action")
                self.windows_action_btn.add_css_class("destructive-action")
                self.windows_info_row.set_subtitle("Windows şu an GRUB menüsünde görünüyor")
            else:
                self.windows_status_row.set_title("🪟 Windows Algılandı (Menüde Değil)")
                self.windows_status_row.set_subtitle(f"EFI: {self.windows_efi_path}")
                self.windows_action_btn.set_label("➕ Menüye Ekle")
                self.windows_action_btn.remove_css_class("destructive-action")
                self.windows_action_btn.add_css_class("suggested-action")
                self.windows_info_row.set_subtitle("Windows'u GRUB menüsüne eklemek için butona tıklayın")
        else:
            self.windows_status_row.set_title("❌ Windows Bulunamadı")
            self.windows_status_row.set_subtitle(f"{PATHS.efi_path} bölümünde Windows boot dosyası yok")
            self.windows_action_btn.set_label("🔍 Yeniden Tara")
            self.windows_action_btn.remove_css_class("destructive-action")
            self.windows_action_btn.remove_css_class("suggested-action")
            self.windows_info_row.set_subtitle("Windows boot yöneticisi bulunamadı")
    
    def on_windows_action(self, button):
        """Windows ekleme/kaldırma işlemi"""
        if not self.windows_detected:
            # Yeniden tara
            self.windows_status_row.set_subtitle("🔄 Taranıyor...")
            GLib.idle_add(self.detect_windows)
            return
        
        if self.windows_in_grub:
            # Menüden kaldır
            self.remove_windows_from_grub()
        else:
            # Menüye ekle
            self.add_windows_to_grub()
    
    def add_windows_to_grub(self):
        """Windows'u GRUB menüsüne ekle"""
        if not self.efi_uuid:
            # UUID yoksa manuel al
            dialog = Adw.MessageDialog.new(self.app.win)
            dialog.set_heading("❌ EFI UUID Bulunamadı")
            dialog.set_body("EFI partition UUID'si alınamadı. Lütfen manuel olarak deneyin.")
            dialog.add_response("ok", "Tamam")
            dialog.present()
            return
        
        # GRUB script içeriği
        script_content = f'''#!/bin/sh
exec tail -n +3 $0
# Windows Boot Manager - GRUB Ayarları tarafından eklendi

menuentry "Windows Boot Manager" --class windows --class os {{
    insmod part_gpt
    insmod fat
    search --no-floppy --fs-uuid --set=root {self.efi_uuid}
    chainloader /EFI/Microsoft/Boot/bootmgfw.efi
}}
'''
        
        # Onay dialogu
        confirm = Adw.MessageDialog.new(self.app.win)
        confirm.set_heading("🪟 Windows'u GRUB'a Ekle")
        confirm.set_body(f"Windows Boot Manager GRUB menüsüne eklenecek.\n\nEFI UUID: {self.efi_uuid}\n\nBu işlem root yetkisi gerektirir.")
        confirm.add_response("cancel", "İptal")
        confirm.add_response("add", "Ekle")
        confirm.set_response_appearance("add", Adw.ResponseAppearance.SUGGESTED)
        confirm.connect("response", self.on_add_windows_response, script_content)
        confirm.present()
    
    def on_add_windows_response(self, dialog, response, script_content):
        dialog.close()
        if response != "add":
            return
            
        self.app.require_auth(lambda: self.perform_add_windows(script_content))

    def perform_add_windows(self, script_content):
        # Script'i geçici dosyaya yaz
        temp_file = "/tmp/40_custom_windows"
        with open(temp_file, 'w') as f:
            f.write(script_content)
        
        # Script (pkexec yok artık, sudo ile çalışacak)
        cmd = f'''
            cp {shlex.quote(temp_file)} /etc/grub.d/40_custom_windows && 
            chmod +x /etc/grub.d/40_custom_windows && 
            echo '✅ Windows script oluşturuldu' &&
            echo '' &&
            echo '🔄 GRUB güncelleniyor...' &&
            {PATHS.update_cmd} 2>&1 &&
            echo '' &&
            echo '✅ İşlem tamamlandı!'
        '''
        
        def on_done(success):
            if success:
                success_dialog = Adw.MessageDialog.new(self.app.win)
                success_dialog.set_heading("✅ Başarılı")
                success_dialog.set_body("Windows GRUB menüsüne eklendi.")
                success_dialog.add_response("ok", "Tamam")
                success_dialog.present()
                self.detect_windows()
        
        self.app.show_terminal_dialog_custom(cmd, "Windows Ekleniyor", on_done)
    
    def remove_windows_from_grub(self):
        """Windows'u GRUB menüsünden kaldır"""
        confirm = Adw.MessageDialog.new(self.app.win)
        confirm.set_heading("🗑️ Windows'u Menüden Kaldır")
        confirm.set_body("Windows Boot Manager GRUB menüsünden kaldırılacak.\n\nWindows yine de UEFI menüsünden başlatılabilir.")
        confirm.add_response("cancel", "İptal")
        confirm.add_response("remove", "Kaldır")
        confirm.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
        confirm.connect("response", self.on_remove_windows_response)
        confirm.present()
    
    def on_remove_windows_response(self, dialog, response):
        dialog.close()
        if response != "remove":
            return
            
        self.app.require_auth(self.perform_remove_windows)

    def perform_remove_windows(self):
        # Script (pkexec yok)
        cmd = f'''
            rm -f /etc/grub.d/40_custom_windows && 
            echo '✅ Windows script silindi' &&
            echo '' &&
            echo '🔄 GRUB güncelleniyor...' &&
            {PATHS.update_cmd} 2>&1 &&
            echo '' &&
            echo '✅ İşlem tamamlandı!'
        '''
        
        def on_done(success):
            if success:
                success_dialog = Adw.MessageDialog.new(self.app.win)
                success_dialog.set_heading("✅ Başarılı")
                success_dialog.set_body("Windows GRUB menüsünden kaldırıldı.")
                success_dialog.add_response("ok", "Tamam")
                success_dialog.present()
                self.detect_windows()
        
        self.app.show_terminal_dialog_custom(cmd, "Windows Kaldırılıyor", on_done)
    
    def on_refresh_menu(self, button):
        """GRUB menü girdilerini yükle"""
        # Menü girdilerini al
        entries = get_grub_menu_entries()
        if entries and entries[0] != "0 - İlk Seçenek":
            self.menu_entries = entries
            menu_model = Gtk.StringList.new(self.menu_entries)
            self.default_combo.set_model(menu_model)
            self.default_combo.set_subtitle("GRUB menüsünden başlatılacak sistem")
            
            # Mevcut ayarı seç
            try:
                if self.saved_default != "saved":
                    default_index = int(self.saved_default)
                    if 0 <= default_index < len(self.menu_entries):
                        self.default_combo.set_selected(default_index)
            except (ValueError, TypeError):
                pass
    
    def get_values(self):
        values = {}
        
        values["GRUB_DEFAULT"] = str(self.default_combo.get_selected())
        values["GRUB_DISABLE_OS_PROBER"] = "false" if self.prober_switch.get_active() else "true"
        
        if not self.submenu_switch.get_active():
            values["GRUB_DISABLE_SUBMENU"] = "true"
        
        return values


class AdvancedPage(Gtk.Box):
    """Gelişmiş ayarlar sayfası"""
    
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.app = app
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        
        # Başlık
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_icon = Gtk.Label(label="🔧")
        title_icon.add_css_class("title-1")
        title = Gtk.Label(label=_("Advanced Settings"))
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        header_box.append(title_icon)
        header_box.append(title)
        content.append(header_box)
        
        desc = Gtk.Label(label=_("Customize kernel parameters and boot behavior."))
        desc.add_css_class("dim-label")
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)
        content.append(desc)
        
        # Warning
        warning_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        warning_box.add_css_class("card")
        warning_box.add_css_class("warning-card")
        warning_box.set_margin_bottom(8)
        warning_icon = Gtk.Label(label="⚠️")
        warning_label = Gtk.Label(label=_("Settings in this section may affect system boot. Be careful!"))
        warning_label.set_wrap(True)
        warning_box.append(warning_icon)
        warning_box.append(warning_label)
        content.append(warning_box)
        
        current_params = app.grub_config.get("GRUB_CMDLINE_LINUX_DEFAULT", "quiet splash")
        
        # Boot Display Group
        display_group = Adw.PreferencesGroup()
        display_group.set_title("🖥️ Açılış Görünümü")
        display_group.set_description("Sistem başlarken ekranda ne gösterileceği")
        
        self.quiet_switch = Adw.SwitchRow()
        self.quiet_switch.set_title(_("Quiet Boot (quiet)"))
        self.quiet_switch.set_subtitle("Teknik mesajları gizle, temiz açılış")
        self.quiet_switch.add_prefix(create_help_button("quiet", app.win))
        self.quiet_switch.set_active("quiet" in current_params)
        self.quiet_switch.connect("notify::active", lambda *a: app.mark_changed())
        
        self.splash_switch = Adw.SwitchRow()
        self.splash_switch.set_title("Açılış Animasyonu (splash)")
        self.splash_switch.set_subtitle("Ubuntu logolu güzel açılış ekranı")
        self.splash_switch.add_prefix(create_help_button("splash", app.win))
        self.splash_switch.set_active("splash" in current_params)
        self.splash_switch.connect("notify::active", lambda *a: app.mark_changed())
        
        display_group.add(self.quiet_switch)
        display_group.add(self.splash_switch)
        content.append(display_group)
        
        # Recovery Group
        recovery_group = Adw.PreferencesGroup()
        recovery_group.set_title("🛠️ Kurtarma Seçenekleri")
        recovery_group.set_description("Sorun giderme ve kurtarma modu")
        
        self.recovery_switch = Adw.SwitchRow()
        self.recovery_switch.set_title(_("Show Recovery Mode"))
        self.recovery_switch.set_subtitle("GRUB'da recovery seçeneklerini göster")
        self.recovery_switch.add_prefix(create_help_button("recovery", app.win))
        
        current_recovery = app.grub_config.get("GRUB_DISABLE_RECOVERY", "")
        self.recovery_switch.set_active(current_recovery.lower() != "true")
        self.recovery_switch.connect("notify::active", lambda *a: app.mark_changed())
        
        recovery_group.add(self.recovery_switch)
        
        recovery_tip = Adw.ActionRow()
        recovery_tip.set_title("💡 İpucu")
        recovery_tip.set_subtitle("Sistem açılmazsa recovery modu hayat kurtarıcı olabilir!")
        recovery_group.add(recovery_tip)
        
        content.append(recovery_group)
        
        # Custom Parameters
        custom_group = Adw.PreferencesGroup()
        custom_group.set_title("⌨️ Özel Kernel Parametreleri")
        custom_group.set_description("İleri düzey kullanıcılar için")
        
        self.custom_entry = Adw.EntryRow()
        self.custom_entry.set_title(_("Kernel Parameters"))
        
        # Get custom params (exclude quiet and splash)
        custom_params = [p for p in current_params.split() if p not in ["quiet", "splash"]]
        self.custom_entry.set_text(" ".join(custom_params))
        self.custom_entry.connect("changed", lambda *a: app.mark_changed())
        
        custom_group.add(self.custom_entry)
        
        custom_info = Adw.ActionRow()
        custom_info.set_title("Örnek parametreler")
        custom_info.set_subtitle("nvidia-drm.modeset=1, nomodeset, acpi=off")
        custom_group.add(custom_info)
        
        content.append(custom_group)
        
        scrolled.set_child(content)
        self.append(scrolled)
    
    def get_values(self):
        params = []
        
        if self.quiet_switch.get_active():
            params.append("quiet")
        if self.splash_switch.get_active():
            params.append("splash")
        
        custom = self.custom_entry.get_text().strip()
        if custom:
            params.extend(custom.split())
        
        values = {
            "GRUB_CMDLINE_LINUX_DEFAULT": " ".join(params)
        }
        
        if not self.recovery_switch.get_active():
            values["GRUB_DISABLE_RECOVERY"] = "true"
        
        return values


class SettingsPage(Gtk.Box):
    """Application settings page - language and theme"""
    
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.app = app
        self._initializing = True  # Flag to prevent handlers during init
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        
        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_icon = Gtk.Label(label="⚙️")
        title_icon.add_css_class("title-1")
        title = Gtk.Label(label=_("Application Settings"))
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        header_box.append(title_icon)
        header_box.append(title)
        content.append(header_box)
        
        desc = Gtk.Label(label=_("Customize application preferences."))
        desc.add_css_class("dim-label")
        desc.set_halign(Gtk.Align.START)
        content.append(desc)
        
        # ============ LANGUAGE SELECTION ============
        lang_group = Adw.PreferencesGroup()
        lang_group.set_title(_("🌐 Language"))
        lang_group.set_description(_("Select application language"))
        
        # Load available languages from JSON
        self.languages = self._load_languages()
        
        lang_row = Adw.ComboRow()
        lang_row.set_title(_("Application Language"))
        lang_row.set_subtitle(_("Changes require restart"))
        lang_row.set_icon_name("preferences-desktop-locale-symbolic")
        
        lang_model = Gtk.StringList()
        current_lang = config_manager.get("language", "en")
        selected_idx = 0
        
        for i, lang in enumerate(self.languages):
            display_name = f"{lang['flag']} {lang['native']} ({lang['name']})"
            lang_model.append(display_name)
            if lang['code'] == current_lang:
                selected_idx = i
        
        lang_row.set_model(lang_model)
        lang_row.set_selected(selected_idx)
        lang_row.connect("notify::selected", self.on_language_changed)
        
        lang_group.add(lang_row)
        content.append(lang_group)
        
        # ============ THEME SELECTION ============
        theme_group = Adw.PreferencesGroup()
        theme_group.set_title(_("🎨 Theme"))
        theme_group.set_description(_("Choose application color scheme"))
        
        theme_row = Adw.ComboRow()
        theme_row.set_title(_("Color Scheme"))
        theme_row.set_icon_name("preferences-desktop-appearance-symbolic")
        
        theme_model = Gtk.StringList()
        themes = [
            (_("System"), "system"),
            (_("Light"), "light"),
            (_("Dark"), "dark")
        ]
        
        current_theme = config_manager.get("theme", "system")
        theme_idx = 0
        
        for i, (name, code) in enumerate(themes):
            theme_model.append(name)
            if code == current_theme:
                theme_idx = i
        
        theme_row.set_model(theme_model)
        theme_row.set_selected(theme_idx)
        theme_row.connect("notify::selected", self.on_theme_changed)
        self.theme_codes = ["system", "light", "dark"]
        
        theme_group.add(theme_row)
        content.append(theme_group)
        
        scrolled.set_child(content)
        self.append(scrolled)
        
        # Mark initialization complete
        self._initializing = False
    
    def _load_languages(self):
        """Load available languages from languages.json"""
        try:
            lang_file = get_path("locales/languages.json")
            with open(lang_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("available", [{"code": "en", "name": "English", "native": "English", "flag": "🇬🇧"}])
        except Exception as e:
            logger.warning(f"Could not load languages.json: {e}")
            return [{"code": "en", "name": "English", "native": "English", "flag": "🇬🇧"}]
    
    def on_language_changed(self, row, pspec):
        if self._initializing:
            return
        selected_idx = row.get_selected()
        if selected_idx < len(self.languages):
            new_lang = self.languages[selected_idx]['code']
            current = config_manager.get("language", "en")
            
            if new_lang != current:
                config_manager.set("language", new_lang)
                logger.info(f"Language changed to {new_lang}")
                
                # Show restart dialog
                dialog = Adw.MessageDialog.new(self.app.win)
                dialog.set_heading(_("Restart Required 🔄"))
                dialog.set_body(_("To apply the new language, I need to make a tiny restart.\nIs that okay? 🥺"))
                dialog.add_response("later", _("Later"))
                dialog.add_response("restart", _("Restart Now"))
                dialog.set_response_appearance("restart", Adw.ResponseAppearance.SUGGESTED)
                dialog.connect("response", self.on_restart_response)
                dialog.present()
    
    def on_restart_response(self, dialog, response):
        dialog.close()
        if response == "restart":
            restart_app(self.app)
    
    def on_theme_changed(self, row, pspec):
        if self._initializing:
            return
        selected_idx = row.get_selected()
        if selected_idx < len(self.theme_codes):
            new_theme = self.theme_codes[selected_idx]
            current = config_manager.get("theme", "system")
            
            if new_theme != current:
                config_manager.set("theme", new_theme)
                logger.info(f"Theme changed to {new_theme}")
                
                # Apply theme immediately
                style_manager = Adw.StyleManager.get_default()
                if new_theme == "light":
                    style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
                elif new_theme == "dark":
                    style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
                else:
                    style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)


class GrubSettingsApp(Adw.Application):
    """Ana uygulama sınıfı"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault('application_id', 'io.github.taylan.grubsettings')
        super().__init__(**kwargs)
        self.grub_config = GrubConfig()
        self.grub_config.load()
        
        self.cached_password = None  # Sudo şifresi için önbellek
        
        self.has_changes = False
        self.win = None
    
    def do_activate(self):
        # Apply saved theme preference
        saved_theme = config_manager.get("theme", "system")
        style_manager = Adw.StyleManager.get_default()
        if saved_theme == "light":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif saved_theme == "dark":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
        
        self.win = Adw.ApplicationWindow(application=self)
        self.win.set_title(_("GRUB Settings"))
        self.win.set_default_size(900, 700)
        self.win.set_size_request(700, 500)
        
        # Ana box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header
        header = Adw.HeaderBar()
        
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_icon = Gtk.Label(label="⚙️")
        title_label = Gtk.Label(label=f"GRUB Settings v{APP_VERSION} (Portable)")
        title_label.add_css_class("title")
        title_box.append(title_icon)
        title_box.append(title_label)
        header.set_title_widget(title_box)
        
        # Reload button
        reload_btn = Gtk.Button()
        reload_btn.set_icon_name("view-refresh-symbolic")
        reload_btn.set_tooltip_text(_("Reload Settings"))
        reload_btn.connect("clicked", self.on_reload)
        header.pack_start(reload_btn)
        
        # About button
        about_btn = Gtk.Button()
        about_btn.set_icon_name("help-about-symbolic")
        about_btn.set_tooltip_text(_("About"))
        about_btn.connect("clicked", self.on_about)
        header.pack_start(about_btn)
        
        # Apply button
        self.apply_btn = Gtk.Button()
        apply_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        apply_box.append(Gtk.Label(label="💾"))
        apply_box.append(Gtk.Label(label=_("Apply Changes")))
        self.apply_btn.set_child(apply_box)
        self.apply_btn.add_css_class("suggested-action")
        self.apply_btn.connect("clicked", self.on_apply)
        self.apply_btn.set_sensitive(False)
        header.pack_end(self.apply_btn)
        
        main_box.append(header)
        
        # Ana içerik kutusu - yatay bölünmüş
        content_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        content_paned.set_vexpand(True)
        content_paned.set_shrink_start_child(False)
        content_paned.set_shrink_end_child(False)
        content_paned.set_resize_start_child(False)
        
        # Sidebar
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_box.set_size_request(220, -1)
        sidebar_box.add_css_class("sidebar")
        
        # Sidebar başlık
        sidebar_title = Gtk.Label(label=_("Categories"))
        sidebar_title.add_css_class("title-4")
        sidebar_title.set_margin_top(16)
        sidebar_title.set_margin_bottom(12)
        sidebar_title.set_margin_start(16)
        sidebar_title.set_halign(Gtk.Align.START)
        sidebar_box.append(sidebar_title)
        
        self.menu_list = Gtk.ListBox()
        self.menu_list.add_css_class("navigation-sidebar")
        self.menu_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.menu_list.connect("row-selected", self.on_menu_selected)
        
        menu_items = [
            ("⏱️", _("Timing"), _("Menu timeout and visibility settings")),
            ("🎨", _("Appearance"), _("Background image and resolution")),
            ("💻", _("System"), _("Default OS and dual-boot")),
            ("🔧", _("Advanced"), _("Kernel parameters and recovery")),
            ("⚙️", _("Settings"), _("Language and theme preferences"))
        ]
        
        for icon, title, subtitle in menu_items:
            row = Adw.ActionRow()
            row.set_title(f"{icon}  {title}")
            row.set_subtitle(subtitle)
            self.menu_list.append(row)
        
        scrolled_sidebar = Gtk.ScrolledWindow()
        scrolled_sidebar.set_child(self.menu_list)
        scrolled_sidebar.set_vexpand(True)
        sidebar_box.append(scrolled_sidebar)
        
        # Version info
        version_label = Gtk.Label(label=f"v{APP_VERSION}")
        version_label.add_css_class("dim-label")
        version_label.set_margin_top(8)
        version_label.set_margin_bottom(12)
        sidebar_box.append(version_label)
        
        content_paned.set_start_child(sidebar_box)
        
        # İçerik alanı
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(200)
        
        self.timing_page = TimingPage(self)
        self.appearance_page = AppearancePage(self)
        self.system_page = SystemPage(self)
        self.advanced_page = AdvancedPage(self)
        self.settings_page = SettingsPage(self)
        
        self.stack.add_named(self.timing_page, "timing")
        self.stack.add_named(self.appearance_page, "appearance")
        self.stack.add_named(self.system_page, "system")
        self.stack.add_named(self.advanced_page, "advanced")
        self.stack.add_named(self.settings_page, "settings")
        
        content_paned.set_end_child(self.stack)
        
        main_box.append(content_paned)
        
        # Status bar
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_bar.set_margin_start(16)
        status_bar.set_margin_end(16)
        status_bar.set_margin_top(8)
        status_bar.set_margin_bottom(8)
        
        status_icon = Gtk.Label(label="ℹ️")
        status_text = Gtk.Label(label=_("Click the ❓ button next to each setting for detailed explanation."))
        status_text.add_css_class("dim-label")
        status_text.set_wrap(True)
        status_text.set_xalign(0)
        status_text.set_hexpand(True)
        
        status_bar.append(status_icon)
        status_bar.append(status_text)
        
        main_box.append(Gtk.Separator())
        main_box.append(status_bar)
        
        self.win.set_content(main_box)
        
        self.menu_list.select_row(self.menu_list.get_row_at_index(0))
        
        self.load_css()
        self.win.present()
    
    def load_css(self):
        """Gelişmiş CSS stillerini yükle"""
        css_provider = Gtk.CssProvider()
        css = """
        /* Sidebar navigasyon */
        .navigation-sidebar row {
            padding: 14px 16px;
            margin: 4px 8px;
            border-radius: 12px;
            transition: all 200ms ease;
        }
        
        .navigation-sidebar row:hover {
            background: alpha(@accent_bg_color, 0.3);
        }
        
        .navigation-sidebar row:selected {
            background: @accent_bg_color;
            color: @accent_fg_color;
        }
        
        /* Başlıklar */
        .title-1 {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.5px;
        }
        
        .title-3 {
            font-size: 16px;
            font-weight: 600;
            color: @accent_color;
        }
        
        .title-4 {
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: alpha(@theme_fg_color, 0.6);
        }
        
        /* Sidebar */
        .sidebar {
            background: alpha(@card_bg_color, 0.4);
            border-right: 1px solid alpha(@borders, 0.3);
        }
        
        /* Kartlar ve kutular */
        .card {
            background: alpha(@card_bg_color, 0.9);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 2px 8px alpha(black, 0.1);
        }
        
        /* Uyarı kartı */
        .warning-card {
            background: linear-gradient(135deg, alpha(@warning_bg_color, 0.15), alpha(@warning_bg_color, 0.25));
            border: 1px solid alpha(@warning_color, 0.4);
            padding: 14px 18px;
            border-radius: 12px;
        }
        
        /* Haplik butonlar */
        .pill {
            border-radius: 999px;
            padding: 10px 24px;
            font-weight: 500;
        }
        
        /* Önizleme çerçevesi */
        .preview-frame {
            background: alpha(@card_bg_color, 0.5);
            border: 2px dashed alpha(@borders, 0.5);
            border-radius: 16px;
        }
        
        /* Grup başlıkları */
        preferencesgroup > box > label.title {
            font-weight: 700;
        }
        
        /* Switch stilleri */
        switch {
            border-radius: 999px;
        }
        
        /* Scale/slider */
        scale trough {
            border-radius: 8px;
        }
        
        scale highlight {
            border-radius: 8px;
        }
        
        /* Header bar */
        headerbar {
            padding: 6px 8px;
        }
        
        /* Durum çubuğu */
        .status-bar {
            background: alpha(@card_bg_color, 0.5);
            border-top: 1px solid alpha(@borders, 0.3);
        }
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            self.win.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def on_menu_selected(self, listbox, row):
        if row is None:
            return
        pages = ["timing", "appearance", "system", "advanced", "settings"]
        index = row.get_index()
        if index < len(pages):
            self.stack.set_visible_child_name(pages[index])
    
    def mark_changed(self):
        self.has_changes = True
        self.apply_btn.set_sensitive(True)
    
    def on_reload(self, button):
        self.grub_config.load()
        dialog = Adw.MessageDialog.new(self.win)
        dialog.set_heading("🔄 Yeniden Yüklendi")
        dialog.set_body("GRUB ayarları diskten yeniden okundu.\nDeğişiklikleri görmek için uygulamayı yeniden başlatın.")
        dialog.add_response("ok", "Tamam")
        dialog.present()
    
    def on_about(self, button):
        dialog = Adw.AboutDialog()
        dialog.set_application_name("GRUB Ayarları")
        dialog.set_version(APP_VERSION)
        dialog.set_developer_name("Linux Aracı")
        dialog.set_comments("Ubuntu için kolay GRUB yapılandırma aracı.\n\nHer ayarın yanındaki yardım butonuna tıklayarak\ndetaylı açıklama alabilirsiniz.")
        dialog.set_license_type(Gtk.License.GPL_3_0)
        dialog.present(self.win)
    
    def on_apply(self, button):
        # Show confirmation
        confirm = Adw.MessageDialog.new(self.win)
        confirm.set_heading("⚠️ Değişiklikleri Uygula")
        confirm.set_body("GRUB yapılandırması güncellenecek.\n\nBu işlem root yetkisi gerektirir ve\nmevcut ayarlarınız yedeklenecektir.")
        confirm.add_response("cancel", "İptal")
        confirm.add_response("apply", "Uygula")
        confirm.set_response_appearance("apply", Adw.ResponseAppearance.SUGGESTED)
        confirm.connect("response", self.on_confirm_response)
        confirm.present()
    
    def require_auth(self, callback):
        """Yetki iste ve callback çalıştır"""
        if self.cached_password:
            callback()
            return

        def show_dialog():
            try:
                logger.info("DEBUG: show_dialog started")
                # GC'den korumak için instance'ı sakla
                logger.info("DEBUG: Creating PoliteAuthDialog...")
                self.auth_dialog_instance = PoliteAuthDialog(self.win)
                logger.info("DEBUG: PoliteAuthDialog created")
                
                def on_resp(d, r):
                    logger.info(f"DEBUG: Auth dialog response: {r}")
                    if r == "ok":
                        self.cached_password = d.get_password()
                        d.close()
                        callback()
                    else:
                        d.close()
                    self.auth_dialog_instance = None
                
                self.auth_dialog_instance.set_callback(on_resp)
                logger.info("DEBUG: Presenting dialog...")
                self.auth_dialog_instance.present()
                logger.info("DEBUG: Dialog presented")
                return False
            except Exception as e:
                logger.error(f"CRITICAL: Failed to show auth dialog: {e}", exc_info=True)
                return False
            
        GLib.timeout_add(200, show_dialog)

    def on_confirm_response(self, dialog, response):
        dialog.close()
        if response != "apply":
            return
        
        self.require_auth(self.perform_update_action)

    def perform_update_action(self):
        """Gerçek güncelleme işlemi"""
        # Collect values
        all_values = {}
        
        timing_values = self.timing_page.get_values()
        appearance_values = self.appearance_page.get_values()
        system_values = self.system_page.get_values()
        advanced_values = self.advanced_page.get_values()
        
        # DEBUG: Log collected values
        logger.info(f"DEBUG timing_values: {timing_values}")
        logger.info(f"DEBUG system_values: {system_values}")
        logger.info(f"DEBUG appearance_values: {list(appearance_values.keys())}")
        logger.info(f"DEBUG advanced_values: {advanced_values}")
        
        # Handle save default setting
        if timing_values.get("GRUB_DEFAULT") == "saved":
            all_values["GRUB_DEFAULT"] = "saved"
            all_values["GRUB_SAVEDEFAULT"] = "true"
            # system_values'dan GRUB_DEFAULT hariç diğerlerini ekle (OS_PROBER vb.)
            for k, v in system_values.items():
                if k != "GRUB_DEFAULT":
                    all_values[k] = v
        else:
            all_values.update(system_values)
        
        all_values.update({k: v for k, v in timing_values.items() if k not in ["GRUB_DEFAULT", "GRUB_SAVEDEFAULT"]})
        all_values.update(appearance_values)
        all_values.update(advanced_values)
        
        # _ORIGINAL_BACKGROUND içsel değişken, config'e yazılmamalı
        bg_original = all_values.pop("_ORIGINAL_BACKGROUND", "")
        
        for key, value in all_values.items():
            self.grub_config.set(key, value)
        
        new_config = self.grub_config.generate_config()
        
        temp_file = "/tmp/grub_settings_new"
        with open(temp_file, 'w') as f:
            f.write(new_config)
        
        # Arkaplan resmi kopyalama komutu
        bg_commands = ""
        if bg_original and os.path.exists(bg_original):
            ext = os.path.splitext(bg_original)[1].lower()
            if ext == ".jpeg":
                ext = ".jpg"
            bg_dest = f"/boot/grub/background{ext}"
            bg_src_quoted = shlex.quote(bg_original)
            bg_dest_quoted = shlex.quote(bg_dest)
            bg_commands = f"cp {bg_src_quoted} {bg_dest_quoted} && chmod 644 {bg_dest_quoted} && "
        
        # Terminal çıktı penceresini göster
        self.show_terminal_dialog(temp_file, bg_commands)
    
    def show_terminal_dialog(self, temp_file, bg_commands):
        """Terminal çıktısını gösteren dialog"""
        # Dialog oluştur
        self.term_dialog = Adw.Window()
        self.term_dialog.set_title("🔄 GRUB Güncelleniyor...")
        self.term_dialog.set_default_size(600, 400)
        self.term_dialog.set_modal(True)
        self.term_dialog.set_transient_for(self.win)
        self.term_dialog.set_hide_on_close(True)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        header.set_show_start_title_buttons(False)
        
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        spinner = Gtk.Spinner()
        spinner.start()
        self.term_spinner = spinner
        title_label = Gtk.Label(label="GRUB Güncelleniyor...")
        self.term_title = title_label
        title_box.append(spinner)
        title_box.append(title_label)
        header.set_title_widget(title_box)
        
        main_box.append(header)
        
        # Terminal alanı
        term_frame = Gtk.Frame()
        term_frame.set_margin_start(16)
        term_frame.set_margin_end(16)
        term_frame.set_margin_top(16)
        term_frame.set_margin_bottom(16)
        term_frame.add_css_class("terminal-frame")
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.term_textview = Gtk.TextView()
        self.term_textview.set_editable(False)
        self.term_textview.set_cursor_visible(False)
        self.term_textview.set_monospace(True)
        self.term_textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.term_textview.set_left_margin(12)
        self.term_textview.set_right_margin(12)
        self.term_textview.set_top_margin(12)
        self.term_textview.set_bottom_margin(12)
        self.term_textview.add_css_class("terminal-text")
        
        self.term_buffer = self.term_textview.get_buffer()
        self.term_buffer.set_text(f"$ {PATHS.update_cmd}\n\n")
        
        scrolled.set_child(self.term_textview)
        term_frame.set_child(scrolled)
        main_box.append(term_frame)
        
        # Durum çubuğu
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        status_box.set_margin_start(16)
        status_box.set_margin_end(16)
        status_box.set_margin_bottom(16)
        status_box.set_halign(Gtk.Align.CENTER)
        
        self.status_icon = Gtk.Label(label="⏳")
        self.status_label = Gtk.Label(label="GRUB güncelleniyor, lütfen bekleyin...")
        self.status_label.add_css_class("dim-label")
        
        status_box.append(self.status_icon)
        status_box.append(self.status_label)
        main_box.append(status_box)
        
        self.term_dialog.set_content(main_box)
        
        # CSS ekle
        css_provider = Gtk.CssProvider()
        css = """
        * {
            font-family: "DejaVu Sans", Sans;
        }
        .terminal-frame {
            background: #1e1e1e;
            border-radius: 12px;
        }
        .terminal-text {
            background: #1e1e1e;
            color: #00ff00;
            font-family: monospace;
            font-size: 12px;
        }
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            self.term_dialog.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        self.term_dialog.present()
        
        # Komutu çalıştır (Script içeriği)
        script_content = f"""
            echo '📁 Mevcut ayarlar yedekleniyor...'
            cp {shlex.quote(GRUB_FILE)} {shlex.quote(GRUB_FILE)}.backup
            echo '✓ Yedekleme tamamlandı'
            echo ''
            {f"echo '🖼️ Arkaplan resmi /boot/grub dizinine kopyalanıyor...' && {bg_commands}echo '✓ Arkaplan kopyalandı ve izinler ayarlandı' && echo ''" if bg_commands else ""}
            echo '📝 Yeni ayarlar yazılıyor...'
            cp {shlex.quote(temp_file)} {shlex.quote(GRUB_FILE)}
            echo '✓ Ayarlar güncellendi'
            echo ''
            echo '🔄 GRUB güncelleniyor...'
            echo '─────────────────────────────────'
            {PATHS.update_cmd} 2>&1
            echo '─────────────────────────────────'
            echo ''
            echo '✅ İşlem tamamlandı!'
        """
        
        # Sudo komutu
        full_cmd = get_sudo_command() + [script_content]
        
        # Async subprocess başlat
        def run_command():
            try:
                process = subprocess.Popen(
                    full_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # Şifreyi gönder
                if self.cached_password:
                    try:
                        process.stdin.write(self.cached_password + "\n")
                        process.stdin.flush()
                    except BrokenPipeError:
                        pass
                
                def read_output():
                    try:
                        line = process.stdout.readline()
                        if line:
                            GLib.idle_add(self.append_terminal_line, line)
                            return True
                        else:
                            # Process finished
                            process.wait()
                            GLib.idle_add(self.on_command_finished, process.returncode)
                            return False
                    except Exception as e:
                        logger.debug(f"Çıktı okuma tamamlandı veya hata: {e}")
                        return False
                
                GLib.timeout_add(50, read_output)
                
            except Exception as e:
                GLib.idle_add(self.append_terminal_line, f"\n❌ Hata: {str(e)}\n")
                GLib.idle_add(self.on_command_finished, 1)
        
        # Biraz gecikme ile başlat
        GLib.timeout_add(500, lambda: (run_command(), False)[1])
    
    def append_terminal_line(self, line):
        """Terminal çıktısına satır ekle"""
        end_iter = self.term_buffer.get_end_iter()
        self.term_buffer.insert(end_iter, line)
        
        # Auto-scroll
        mark = self.term_buffer.create_mark(None, self.term_buffer.get_end_iter(), False)
        self.term_textview.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
    
    def on_command_finished(self, return_code):
        """Komut tamamlandığında"""
        self.term_spinner.stop()
        
        if return_code == 0:
            self.term_title.set_label("✅ Güncelleme Tamamlandı")
            self.status_icon.set_label("✅")
            self.status_label.set_label("GRUB başarıyla güncellendi! Pencere 3 saniye içinde kapanacak...")
            self.has_changes = False
            self.apply_btn.set_sensitive(False)
            
            # 3 saniye sonra kapat
            GLib.timeout_add(3000, self.close_terminal_dialog)
        else:
            self.term_title.set_label("❌ Güncelleme Başarısız")
            self.status_icon.set_label("❌")
            self.status_label.set_label("Bir hata oluştu. Pencereyi manuel kapatabilirsiniz.")
            
            # Kapat butonu göster
            close_btn = Gtk.Button(label="Kapat")
            close_btn.add_css_class("destructive-action")
            close_btn.connect("clicked", lambda b: self.term_dialog.close())
            
            header = self.term_dialog.get_content().get_first_child()
            header.pack_end(close_btn)
            header.set_show_end_title_buttons(True)
    
    def close_terminal_dialog(self):
        """Terminal dialogunu kapat"""
        if self.term_dialog:
            self.term_dialog.close()
            self.term_dialog = None
        return False
    
    def show_terminal_dialog_custom(self, script_content, title, callback=None):
        """Özel komut çalıştıran terminal dialog"""
        # Dialog oluştur
        self.term_dialog = Adw.Window()
        self.term_dialog.set_title(title)
        self.term_dialog.set_default_size(600, 400)
        self.term_dialog.set_modal(True)
        self.term_dialog.set_transient_for(self.win)
        self.term_dialog.set_hide_on_close(True)
        
        self.custom_callback = callback
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False) # Kapatmayı devre dışı bırak
        header.set_show_start_title_buttons(False)
        
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        spinner = Gtk.Spinner()
        spinner.start()
        self.term_spinner = spinner
        title_label = Gtk.Label(label=title)
        self.term_title = title_label
        title_box.append(spinner)
        title_box.append(title_label)
        header.set_title_widget(title_box)
        main_box.append(header)
        
        # Terminal frame
        term_frame = Gtk.Frame()
        term_frame.add_css_class("terminal-frame")
        term_frame.set_margin_start(16); term_frame.set_margin_end(16)
        term_frame.set_margin_top(16); term_frame.set_margin_bottom(16)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.term_textview = Gtk.TextView()
        self.term_textview.set_editable(False)
        self.term_textview.set_cursor_visible(False)
        self.term_textview.set_monospace(True)
        self.term_textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.term_textview.set_left_margin(12); self.term_textview.set_right_margin(12)
        self.term_textview.set_top_margin(12); self.term_textview.set_bottom_margin(12)
        self.term_textview.add_css_class("terminal-text")
        
        self.term_buffer = self.term_textview.get_buffer()
        self.term_buffer.set_text(f"$ {title}\n\n")
        
        scrolled.set_child(self.term_textview)
        term_frame.set_child(scrolled)
        main_box.append(term_frame)
        
        # Status
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        status_box.set_halign(Gtk.Align.CENTER)
        status_box.set_margin_start(16)
        status_box.set_margin_end(16)
        status_box.set_margin_bottom(16)
        self.status_icon = Gtk.Label(label="⏳")
        self.status_label = Gtk.Label(label="İşlem yapılıyor...")
        self.status_label.add_css_class("dim-label")
        status_box.append(self.status_icon)
        status_box.append(self.status_label)
        main_box.append(status_box)
        
        self.term_dialog.set_content(main_box)
        
        # CSS (Font fix)
        css_provider = Gtk.CssProvider()
        css = """
        * { font-family: "DejaVu Sans", Sans; }
        .terminal-frame { background: #1e1e1e; border-radius: 12px; }
        .terminal-text { background: #1e1e1e; color: #00ff00; font-family: "DejaVu Sans Mono", Monospace; font-size: 12px; }
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(self.term_dialog.get_display(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        self.term_dialog.present()
        
        # Sudo komutu
        full_cmd = get_sudo_command() + [script_content]
        
        def run_command():
            try:
                process = subprocess.Popen(
                    full_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # Şifreyi gönder
                if self.cached_password:
                    try:
                        process.stdin.write(self.cached_password + "\n")
                        process.stdin.flush()
                    except BrokenPipeError:
                        pass
                
                def read_output():
                    try:
                        line = process.stdout.readline()
                        if line:
                            GLib.idle_add(self.append_terminal_line, line)
                            return True
                        else:
                            process.wait()
                            GLib.idle_add(self.on_custom_command_finished, process.returncode)
                            return False
                    except Exception as e:
                        logger.debug(f"Çıktı okuma tamamlandı veya hata: {e}")
                        return False
                
                GLib.timeout_add(50, read_output)
            except Exception as e:
                GLib.idle_add(self.append_terminal_line, f"\n❌ Hata: {str(e)}\n")
                GLib.idle_add(self.on_custom_command_finished, 1)
        
        GLib.timeout_add(500, lambda: (run_command(), False)[1])
    
    def on_custom_command_finished(self, return_code):
        """Özel komut tamamlandığında"""
        self.term_spinner.stop()
        
        success = return_code == 0
        
        if success:
            self.term_title.set_label("✅ İşlem Tamamlandı")
            self.status_icon.set_label("✅")
            self.status_label.set_label("Başarıyla tamamlandı! Pencere 3 saniye içinde kapanacak...")
            
            # 3 saniye sonra kapat
            GLib.timeout_add(3000, self.close_terminal_dialog)
        else:
            self.term_title.set_label("❌ İşlem Başarısız")
            self.status_icon.set_label("❌")
            self.status_label.set_label("Bir hata oluştu. Pencereyi manuel kapatabilirsiniz.")
            
            # Kapat butonu göster
            close_btn = Gtk.Button(label="Kapat")
            close_btn.add_css_class("destructive-action")
            close_btn.connect("clicked", lambda b: self.term_dialog.close())
            
            header = self.term_dialog.get_content().get_first_child()
            header.pack_end(close_btn)
            header.set_show_end_title_buttons(True)
        
        # Callback varsa çağır
        if self.custom_callback:
            self.custom_callback(success)



def global_exception_handler(exctype, value, traceback_obj):
    import traceback
    import os
    from datetime import datetime
    
    crash_file = os.path.expanduser("~/grub_settings_crash.txt")
    with open(crash_file, "w") as f:
        f.write(f"Crash Time: {datetime.now()}\n")
        traceback.print_exception(exctype, value, traceback_obj, file=f)
    print(f"CRITICAL ERROR (Uncaught): {value}")
    try:
        logging.critical(f"Uncaught exception: {value}", exc_info=(exctype, value, traceback_obj))
    except:
        pass

if __name__ == "__main__":
    sys.excepthook = global_exception_handler
    
    try:
        app = GrubSettingsApp(application_id="io.github.taylan.grubsettings")
        app.run(sys.argv)
    except Exception as e:
        # This catches startup errors before the main loop takes over fully,
        # or if run() raises.
        global_exception_handler(type(e), e, e.__traceback__)
