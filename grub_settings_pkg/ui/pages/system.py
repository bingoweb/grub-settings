import os
import threading
import subprocess
import shlex
import tempfile
from gi.repository import Gtk, Adw, GLib
from ..widgets import create_help_button
from ...utils import logger
from ...system import PATHS, GRUB_CFG_FILE

class SystemPage(Gtk.Box):
    """System settings page"""

    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.app = app
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)

        # Windows detection info
        self.windows_detected = False
        self.windows_efi_path = None
        self.efi_uuid = None
        self.windows_in_grub = False

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)

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

        self.windows_status_row = Adw.ActionRow()
        self.windows_status_row.set_title(_("Windows Status"))
        self.windows_status_row.set_subtitle(_("Detecting..."))

        self.windows_action_btn = Gtk.Button()
        self.windows_action_btn.set_valign(Gtk.Align.CENTER)
        self.windows_action_btn.add_css_class("suggested-action")
        self.windows_action_btn.add_css_class("pill")
        self.windows_action_btn.connect("clicked", self.on_windows_action)
        self.windows_status_row.add_suffix(self.windows_action_btn)

        self.windows_group.add(self.windows_status_row)

        self.windows_info_row = Adw.ActionRow()
        self.windows_info_row.set_title(_("💡 Info"))
        self.windows_info_row.set_subtitle(_("If OS-Prober cannot detect Windows, you can add it manually."))
        self.windows_group.add(self.windows_info_row)

        content.append(self.windows_group)

        # Start detection (background)
        GLib.idle_add(self.detect_windows)

        # ============ DEFAULT OS SECTION ============
        default_group = Adw.PreferencesGroup()
        default_group.set_title(_("🎯 Default Operating System"))
        default_group.set_description(_("Which system should start when the timeout expires?"))

        self.menu_entries = [_("0 - First Option"), _("1 - Second Option"), _("2 - Third Option")]

        self.default_combo = Adw.ComboRow()
        self.default_combo.set_title(_("Default System"))
        self.default_combo.set_subtitle(_("Click refresh to load the menu"))
        self.default_combo.add_prefix(create_help_button("default_os", app.win, _("Default System")))

        self.refresh_btn = Gtk.Button()
        self.refresh_btn.set_icon_name("view-refresh-symbolic")
        self.refresh_btn.set_valign(Gtk.Align.CENTER)
        self.refresh_btn.set_tooltip_text(_("Load GRUB menu (requires root privileges)"))
        try:
            self.refresh_btn.update_property([Gtk.AccessibleProperty.LABEL], [_("Refresh Boot Options")])
        except AttributeError:
            pass
        self.refresh_btn.connect("clicked", self.on_refresh_menu)
        self.default_combo.add_suffix(self.refresh_btn)

        menu_model = Gtk.StringList.new(self.menu_entries)
        self.default_combo.set_model(menu_model)

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
        self.prober_switch.add_prefix(create_help_button("os_prober", app.win, _("OS Detection")))

        current_prober = app.grub_config.get("GRUB_DISABLE_OS_PROBER", "true")
        self.prober_switch.set_active(current_prober.lower() == "false")
        self.prober_switch.connect("notify::active", lambda *a: app.mark_changed())

        prober_group.add(self.prober_switch)

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
        self.submenu_switch.add_prefix(create_help_button("submenu", app.win, _("Submenus")))

        current_submenu = app.grub_config.get("GRUB_DISABLE_SUBMENU", "")
        self.submenu_switch.set_active(current_submenu.lower() != "true")
        self.submenu_switch.connect("notify::active", lambda *a: app.mark_changed())

        submenu_group.add(self.submenu_switch)
        content.append(submenu_group)

        scrolled.set_child(content)
        self.append(scrolled)

    def detect_windows(self):
        """Detect Windows EFI and GRUB status (Background Thread)"""
        self.windows_status_row.set_subtitle(_("⏳ Scanning system..."))

        # UX: Loading state
        self.windows_action_btn.set_sensitive(False)
        spinner = Gtk.Spinner()
        spinner.start()
        self.windows_action_btn.set_child(spinner)

        thread = threading.Thread(target=self._detect_windows_worker)
        thread.daemon = True
        thread.start()
        return False

    def _detect_windows_worker(self):
        try:
            # Check Windows EFI file
            windows_efi = os.path.join(PATHS.efi_path, "EFI/Microsoft/Boot/bootmgfw.efi")
            if os.path.exists(windows_efi):
                self.windows_detected = True
                self.windows_efi_path = windows_efi

                # Get EFI partition UUID
                try:
                    result = subprocess.run(
                        ["findmnt", "-n", "-o", "UUID", PATHS.efi_path],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        self.efi_uuid = result.stdout.strip()
                except Exception as e:
                    logger.warning(f"Failed to get EFI UUID: {e}")

            # Check if Windows is in GRUB
            custom_script = "/etc/grub.d/40_custom_windows"
            if os.path.exists(custom_script):
                self.windows_in_grub = True
            else:
                # Check grub.cfg
                try:
                    result = subprocess.run(
                        ["pkexec", "grep", "-l", "Windows", GRUB_CFG_FILE],
                        capture_output=True, text=True, timeout=10
                    )
                    self.windows_in_grub = result.returncode == 0
                except Exception:
                    pass

            GLib.idle_add(self.update_windows_ui)

        except Exception as e:
            logger.error(f"Windows detection error: {e}")
            GLib.idle_add(self._on_detection_error)

    def _on_detection_error(self):
        self.windows_status_row.set_subtitle(_("❌ Detection error"))
        self.windows_action_btn.set_sensitive(True)
        self.windows_action_btn.set_label(_("Retry"))
        self.windows_action_btn.remove_css_class("destructive-action")
        self.windows_action_btn.add_css_class("suggested-action")

    def update_windows_ui(self):
        self.windows_action_btn.set_sensitive(True)
        if self.windows_detected:
            if self.windows_in_grub:
                self.windows_status_row.set_title(_("✅ Windows Detected and in Menu"))
                self.windows_status_row.set_subtitle(f"EFI: {self.windows_efi_path}")
                self.windows_action_btn.set_label(_("🗑️ Remove from Menu"))
                self.windows_action_btn.remove_css_class("suggested-action")
                self.windows_action_btn.add_css_class("destructive-action")
                self.windows_info_row.set_subtitle(_("Windows is currently visible in GRUB menu"))
            else:
                self.windows_status_row.set_title(_("🪟 Windows Detected (Not in Menu)"))
                self.windows_status_row.set_subtitle(f"EFI: {self.windows_efi_path}")
                self.windows_action_btn.set_label(_("➕ Add to Menu"))
                self.windows_action_btn.remove_css_class("destructive-action")
                self.windows_action_btn.add_css_class("suggested-action")
                self.windows_info_row.set_subtitle(_("Click button to add Windows to GRUB menu"))
        else:
            self.windows_status_row.set_title(_("❌ Windows Not Found"))
            self.windows_status_row.set_subtitle(f"{PATHS.efi_path} - " + _("No Windows boot file found"))
            self.windows_action_btn.set_label(_("🔍 Rescan"))
            self.windows_action_btn.remove_css_class("destructive-action")
            self.windows_action_btn.remove_css_class("suggested-action")
            self.windows_info_row.set_subtitle(_("Windows boot manager not found"))

    def on_windows_action(self, button):
        if not self.windows_detected:
            self.windows_status_row.set_subtitle(_("🔄 Scanning..."))
            GLib.idle_add(self.detect_windows)
            return

        if self.windows_in_grub:
            self.remove_windows_from_grub()
        else:
            self.add_windows_to_grub()

    def add_windows_to_grub(self):
        if not self.efi_uuid:
            dialog = Adw.MessageDialog.new(self.app.win)
            dialog.set_heading(_("❌ EFI UUID Not Found"))
            dialog.set_body(_("Could not retrieve EFI partition UUID. Please try manually."))
            dialog.add_response("ok", _("OK"))
            dialog.set_default_response("ok")
            dialog.set_close_response("ok")
            dialog.present()
            return

        script_content = f'''#!/bin/sh
exec tail -n +3 $0
# Windows Boot Manager - Added by GRUB Settings

menuentry "Windows Boot Manager" --class windows --class os {{
    insmod part_gpt
    insmod fat
    search --no-floppy --fs-uuid --set=root {self.efi_uuid}
    chainloader /EFI/Microsoft/Boot/bootmgfw.efi
}}
'''

        confirm = Adw.MessageDialog.new(self.app.win)
        confirm.set_heading(_("🪟 Add Windows to GRUB"))
        confirm.set_body(f"{_('Windows Boot Manager will be added to GRUB menu.')}\n\nEFI UUID: {self.efi_uuid}\n\n{_('This action requires root privileges.')}")
        confirm.add_response("cancel", _("Cancel"))
        confirm.add_response("add", _("Add"))
        confirm.set_response_appearance("add", Adw.ResponseAppearance.SUGGESTED)
        confirm.set_default_response("add")
        confirm.set_close_response("cancel")
        confirm.connect("response", self.on_add_windows_response, script_content)
        confirm.present()

    def on_add_windows_response(self, dialog, response, script_content):
        dialog.close()
        if response != "add":
            return

        self.app.require_auth(lambda: self.perform_add_windows(script_content))

    def perform_add_windows(self, script_content):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, prefix='grub_windows_', suffix='.sh') as tf:
            tf.write(script_content)
            temp_file = tf.name

        cmd = f'''
            cp {shlex.quote(temp_file)} /etc/grub.d/40_custom_windows &&
            chmod +x /etc/grub.d/40_custom_windows &&
            rm -f {shlex.quote(temp_file)} &&
            echo '✅ Windows script created' &&
            echo '' &&
            echo '🔄 Updating GRUB...' &&
            {PATHS.update_cmd} 2>&1 &&
            echo '' &&
            echo '✅ Done!'
        '''

        def on_done(success):
            if success:
                success_dialog = Adw.MessageDialog.new(self.app.win)
                success_dialog.set_heading(_("✅ Success"))
                success_dialog.set_body(_("Windows added to GRUB menu."))
                success_dialog.add_response("ok", _("OK"))
                success_dialog.set_default_response("ok")
                success_dialog.set_close_response("ok")
                success_dialog.present()
                self.detect_windows()

        self.app.show_terminal_dialog_custom(cmd, _("Adding Windows"), on_done)

    def remove_windows_from_grub(self):
        confirm = Adw.MessageDialog.new(self.app.win)
        confirm.set_heading(_("🗑️ Remove Windows from Menu"))
        confirm.set_body(_("Windows Boot Manager will be removed from GRUB menu.\n\nWindows can still be booted from UEFI menu."))
        confirm.add_response("cancel", _("Cancel"))
        confirm.add_response("remove", _("Remove"))
        confirm.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
        confirm.set_default_response("cancel")
        confirm.set_close_response("cancel")
        confirm.connect("response", self.on_remove_windows_response)
        confirm.present()

    def on_remove_windows_response(self, dialog, response):
        dialog.close()
        if response != "remove":
            return

        self.app.require_auth(self.perform_remove_windows)

    def perform_remove_windows(self):
        cmd = f'''
            rm -f /etc/grub.d/40_custom_windows &&
            echo '✅ Windows script deleted' &&
            echo '' &&
            echo '🔄 Updating GRUB...' &&
            {PATHS.update_cmd} 2>&1 &&
            echo '' &&
            echo '✅ Done!'
        '''

        def on_done(success):
            if success:
                success_dialog = Adw.MessageDialog.new(self.app.win)
                success_dialog.set_heading(_("✅ Success"))
                success_dialog.set_body(_("Windows removed from GRUB menu."))
                success_dialog.add_response("ok", _("OK"))
                success_dialog.set_default_response("ok")
                success_dialog.set_close_response("ok")
                success_dialog.present()
                self.detect_windows()

        self.app.show_terminal_dialog_custom(cmd, _("Removing Windows"), on_done)

    def on_refresh_menu(self, button):
        # UX: Add loading state to button
        self.refresh_btn.set_sensitive(False)

        # Add spinner
        spinner = Gtk.Spinner()
        spinner.start()
        self.refresh_btn.set_child(spinner)

        # Run in background
        thread = threading.Thread(target=self._refresh_menu_worker)
        thread.daemon = True
        thread.start()

    def _refresh_menu_worker(self):
        entries = []
        try:
            entries = self.get_grub_menu_entries()
        except Exception as e:
            logger.error(f"Critical error in refresh worker: {e}")
        finally:
            GLib.idle_add(self._on_refresh_menu_complete, entries)

    def _on_refresh_menu_complete(self, entries):
        # Restore button state
        self.refresh_btn.set_child(None)
        self.refresh_btn.set_icon_name("view-refresh-symbolic")
        self.refresh_btn.set_sensitive(True)

        if entries and entries[0] != "0 - First Option":
            self.menu_entries = entries
            menu_model = Gtk.StringList.new(self.menu_entries)
            self.default_combo.set_model(menu_model)
            self.default_combo.set_subtitle(_("System to boot from GRUB menu"))

            try:
                if self.saved_default != "saved":
                    default_index = int(self.saved_default)
                    if 0 <= default_index < len(self.menu_entries):
                        self.default_combo.set_selected(default_index)
            except (ValueError, TypeError):
                pass

        return False

    def get_grub_menu_entries(self):
        import re
        entries = []
        try:
            result = subprocess.run(
                ["pkexec", "cat", GRUB_CFG_FILE],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                content = result.stdout
                pattern = r"menuentry\s+['\"]([^'\"]+)['\"]"
                matches = re.findall(pattern, content)
                for match in matches:
                    if match not in entries:
                        entries.append(match)
        except subprocess.TimeoutExpired:
            logger.warning("GRUB menu read timed out")
        except Exception as e:
            logger.warning(f"Failed to read GRUB menu: {e}")

        if not entries:
            entries = [_("0 - First Option"), _("1 - Second Option"), _("2 - Third Option")]

        return entries

    def get_values(self):
        values = {}

        values["GRUB_DEFAULT"] = str(self.default_combo.get_selected())
        values["GRUB_DISABLE_OS_PROBER"] = "false" if self.prober_switch.get_active() else "true"

        if not self.submenu_switch.get_active():
            values["GRUB_DISABLE_SUBMENU"] = "true"

        return values
