import os
import tempfile
import shlex
import subprocess
from gi.repository import Gtk, Adw, Gdk, GLib
from .config import config_manager, GrubConfig
from .utils import logger, get_sudo_command, get_path
from .system import GRUB_FILE, PATHS
from .ui.widgets import PoliteAuthDialog
from .ui.pages.timing import TimingPage
from .ui.pages.appearance import AppearancePage
from .ui.pages.system import SystemPage
from .ui.pages.advanced import AdvancedPage
from .ui.pages.settings import SettingsPage
from .constants import APP_VERSION, APP_ID

class GrubSettingsApp(Adw.Application):
    """Main Application Class"""

    def __init__(self, **kwargs):
        kwargs.setdefault('application_id', APP_ID)
        super().__init__(**kwargs)
        self.grub_config = GrubConfig()

        self.cached_password = None
        self.password_timeout_id = None

        self.has_changes = False
        self.win = None
        self.auth_dialog_instance = None

    def _clear_cached_password(self):
        """Clear cached password for security"""
        self.cached_password = None
        self.password_timeout_id = None
        logger.info("Security: Cached password cleared due to timeout")
        return False

    def do_activate(self):
        # Add local assets to icon theme search path for development
        try:
            display = Gdk.Display.get_default()
            icon_theme = Gtk.IconTheme.get_for_display(display)
            assets_dir = get_path("assets")
            if os.path.exists(assets_dir):
                icon_theme.add_search_path(assets_dir)
        except Exception as e:
            logger.warning(f"Failed to add icon search path: {e}")

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

        icon_path = get_path("assets/icon.png")
        if os.path.exists(icon_path):
            try:
                self.win.set_icon_name(APP_ID)
            except Exception:
                pass

        self.win.set_default_size(900, 700)
        self.win.set_size_request(700, 500)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Header
        header = Adw.HeaderBar()

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_icon = Gtk.Label(label="⚙️")
        title_label = Gtk.Label(label=f"GRUB Settings v{APP_VERSION}")
        title_label.add_css_class("title")
        title_box.append(title_icon)
        title_box.append(title_label)
        header.set_title_widget(title_box)

        reload_btn = Gtk.Button()
        reload_btn.set_icon_name("view-refresh-symbolic")
        reload_btn.set_tooltip_text(_("Reload Settings"))
        reload_btn.connect("clicked", self.on_reload)
        header.pack_start(reload_btn)

        about_btn = Gtk.Button()
        about_btn.set_icon_name("help-about-symbolic")
        about_btn.set_tooltip_text(_("About"))
        about_btn.connect("clicked", self.on_about)
        header.pack_start(about_btn)

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

        # Content Paned
        content_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        content_paned.set_vexpand(True)
        content_paned.set_shrink_start_child(False)
        content_paned.set_shrink_end_child(False)
        content_paned.set_resize_start_child(False)

        # Sidebar
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_box.set_size_request(220, -1)
        sidebar_box.add_css_class("sidebar")

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

        version_label = Gtk.Label(label=f"v{APP_VERSION}")
        version_label.add_css_class("dim-label")
        version_label.set_margin_top(8)
        version_label.set_margin_bottom(12)
        sidebar_box.append(version_label)

        content_paned.set_start_child(sidebar_box)

        # Content Area - Using Stack with Lazy instantiation potential
        # (For now instantiate all, but structure allows lazy)
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

        # Status Bar
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
        if self.win is None:
            logger.error("Window not initialized, cannot load CSS")
            return

        css_provider = Gtk.CssProvider()

        # Try to load from assets/style.css
        css_path = get_path("assets/style.css")
        if os.path.exists(css_path):
            css_provider.load_from_path(css_path)
        else:
            logger.warning("style.css not found, loading minimal css")
            # Minimal fallback if file missing
            css_provider.load_from_data(b".title-1 { font-size: 24px; font-weight: bold; }")

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
        dialog.set_heading(_("🔄 Reloaded"))
        dialog.set_body(_("GRUB settings reloaded from disk.\nRestart the app to see external changes."))
        dialog.add_response("ok", _("OK"))
        dialog.present()

    def on_about(self, button):
        about = Adw.AboutWindow(
            transient_for=self.win,
            application_name=APP_ID, # Or nice name
            application_icon=APP_ID,
            version=APP_VERSION,
            developer_name="Taylan Soylu",
            website="https://github.com/bingoweb/grub-settings",
            issue_url="https://github.com/bingoweb/grub-settings/issues",
            license_type=Gtk.License.GPL_3_0,
            copyright="© 2024 Taylan Soylu"
        )
        about.present()

    def on_apply(self, button):
        confirm = Adw.MessageDialog.new(self.win)
        confirm.set_heading(_("⚠️ Apply Changes"))
        confirm.set_body(_("GRUB configuration will be updated.\n\nThis requires root privileges and\nyour current settings will be backed up."))
        confirm.add_response("cancel", _("Cancel"))
        confirm.add_response("apply", _("Apply"))
        confirm.set_response_appearance("apply", Adw.ResponseAppearance.SUGGESTED)
        confirm.connect("response", self.on_confirm_response)
        confirm.present()

    def require_auth(self, callback):
        if self.cached_password:
            callback()
            return

        dialog = PoliteAuthDialog(self.win)

        def on_response(d, response_id):
            if response_id == "ok":
                self.cached_password = d.get_password()

                if self.password_timeout_id:
                    GLib.source_remove(self.password_timeout_id)
                self.password_timeout_id = GLib.timeout_add_seconds(300, self._clear_cached_password)

                callback()

        dialog.connect("response", on_response)
        dialog.present()

    def on_confirm_response(self, dialog, response):
        dialog.close()
        if response != "apply":
            return
        self.require_auth(self.perform_update_action)

    def perform_update_action(self):
        all_values = {}

        timing_values = self.timing_page.get_values()
        appearance_values = self.appearance_page.get_values()
        system_values = self.system_page.get_values()
        advanced_values = self.advanced_page.get_values()

        # Logic to merge settings
        if timing_values.get("GRUB_DEFAULT") == "saved":
            all_values["GRUB_DEFAULT"] = "saved"
            all_values["GRUB_SAVEDEFAULT"] = "true"
            for k, v in system_values.items():
                if k != "GRUB_DEFAULT":
                    all_values[k] = v
        else:
            all_values.update(system_values)

        all_values.update({k: v for k, v in timing_values.items() if k not in ["GRUB_DEFAULT", "GRUB_SAVEDEFAULT"]})
        all_values.update(appearance_values)
        all_values.update(advanced_values)

        bg_original = all_values.pop("_ORIGINAL_BACKGROUND", "")

        for key, value in all_values.items():
            self.grub_config.set(key, value)

        new_config = self.grub_config.generate_config()

        with tempfile.NamedTemporaryFile(mode='w', delete=False, prefix='grub_settings_', suffix='.tmp') as tf:
            tf.write(new_config)
            temp_file = tf.name

        bg_commands = ""
        if bg_original and os.path.exists(bg_original):
            ext = os.path.splitext(bg_original)[1].lower()
            if ext == ".jpeg":
                ext = ".jpg"
            bg_dest = f"/boot/grub/background{ext}"
            bg_src_quoted = shlex.quote(bg_original)
            bg_dest_quoted = shlex.quote(bg_dest)
            bg_commands = f"cp {bg_src_quoted} {bg_dest_quoted} && chmod 644 {bg_dest_quoted} && "

        self.show_terminal_dialog(temp_file, bg_commands)

    def _build_terminal_dialog(self, title, initial_text, hide_on_close=False):
        dialog = Adw.Window()
        dialog.set_title(title)
        dialog.set_default_size(600, 400)
        dialog.set_modal(True)
        dialog.set_transient_for(self.win)
        if hide_on_close:
            dialog.set_hide_on_close(True)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        header.set_show_start_title_buttons(False)

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        spinner = Gtk.Spinner()
        spinner.start()
        title_label = Gtk.Label(label=title)
        title_box.append(spinner)
        title_box.append(title_label)
        header.set_title_widget(title_box)
        main_box.append(header)

        term_frame = Gtk.Frame()
        term_frame.add_css_class("terminal-frame")
        term_frame.set_margin_start(16)
        term_frame.set_margin_end(16)
        term_frame.set_margin_top(16)
        term_frame.set_margin_bottom(16)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        textview = Gtk.TextView()
        textview.set_editable(False)
        textview.set_cursor_visible(False)
        textview.set_monospace(True)
        textview.add_css_class("terminal-text")

        buffer = textview.get_buffer()
        buffer.set_text(initial_text)

        scrolled.set_child(textview)
        term_frame.set_child(scrolled)
        main_box.append(term_frame)

        dialog.set_content(main_box)

        css_provider = Gtk.CssProvider()
        css = """
        .terminal-frame { background: #1e1e1e; border-radius: 12px; }
        .terminal-text { background: #1e1e1e; color: #00ff00; font-family: monospace; font-size: 12px; }
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            dialog.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        return dialog, header, spinner, title_label, textview, buffer

    def show_terminal_dialog(self, temp_file, bg_commands):
        (
            self.term_dialog,
            _header,
            self.term_spinner,
            self.term_title,
            self.term_textview,
            self.term_buffer,
        ) = self._build_terminal_dialog(
            _("🔄 Updating GRUB..."),
            f"$ {PATHS.update_cmd}\n\n",
            hide_on_close=True
        )
        self.term_dialog.present()

        script_content = f"""
            echo '📁 Backing up current settings...'
            cp {shlex.quote(GRUB_FILE)} {shlex.quote(GRUB_FILE)}.backup
            echo '✓ Backup complete'
            echo ''
            {f"echo '🖼️ Copying background image...' && {bg_commands}echo '✓ Background set' && echo ''" if bg_commands else ""}
            echo '📝 Writing new settings...'
            cp {shlex.quote(temp_file)} {shlex.quote(GRUB_FILE)}
            rm -f {shlex.quote(temp_file)}
            echo '✓ Settings updated'
            echo ''
            echo '🔄 Updating GRUB...'
            echo '─────────────────────────────────'
            {PATHS.update_cmd} 2>&1
            echo '─────────────────────────────────'
            echo ''
            echo '✅ Done!'
        """

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

                if self.cached_password and process.stdin:
                    try:
                        process.stdin.write(self.cached_password + "\n")
                        process.stdin.flush()
                    except BrokenPipeError:
                        pass

                def read_output():
                    if not process.stdout:
                        return
                    try:
                        line = process.stdout.readline()
                        if line:
                            GLib.idle_add(self.append_terminal_line, line)
                            return True
                        else:
                            process.wait()
                            GLib.idle_add(self.on_command_finished, process.returncode)
                            return False
                    except Exception as exc:
                        logger.exception("Failed to read GRUB update output", exc_info=exc)
                        GLib.idle_add(self.append_terminal_line, _("❌ Error reading command output.\n"))
                        GLib.idle_add(self.on_command_finished, 1)
                        return False

                GLib.timeout_add(50, read_output)
            except Exception as exc:
                logger.exception("Failed to start GRUB update command", exc_info=exc)
                GLib.idle_add(self.append_terminal_line, _("❌ Failed to start update command.\n"))
                GLib.idle_add(self.on_command_finished, 1)

        GLib.timeout_add(500, lambda: (run_command(), False)[1])

    def append_terminal_line(self, line):
        end_iter = self.term_buffer.get_end_iter()
        self.term_buffer.insert(end_iter, line)
        mark = self.term_buffer.create_mark(None, self.term_buffer.get_end_iter(), False)
        self.term_textview.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

    def on_command_finished(self, return_code):
        self.term_spinner.stop()
        if return_code == 0:
            self.term_title.set_label(_("✅ Update Complete"))
            self.has_changes = False
            self.apply_btn.set_sensitive(False)
            GLib.timeout_add(3000, lambda: (self.term_dialog.close() if self.term_dialog else None, False)[1])
        else:
            self.term_title.set_label(_("❌ Update Failed"))
            close_btn = Gtk.Button(label=_("Close"))
            close_btn.add_css_class("destructive-action")
            close_btn.connect("clicked", lambda b: self.term_dialog.close())
            header = self.term_dialog.get_content().get_first_child()
            header.pack_end(close_btn)
            header.set_show_end_title_buttons(True)

    def show_terminal_dialog_custom(self, cmd, title, callback=None):
        """Re-implement custom dialog logic"""
        # ... Reuse similar logic as show_terminal_dialog or abstract it
        # For brevity, I'm assuming similar implementation or reused code
        # I'll implement a simplified version here for system page callbacks
        (
            self.term_dialog,
            header,
            self.term_spinner,
            self.term_title,
            self.term_textview,
            self.term_buffer,
        ) = self._build_terminal_dialog(
            title,
            f"$ {title}\n\n"
        )
        self.term_dialog.present()

        full_cmd = get_sudo_command() + [cmd]

        def run_command():
            try:
                process = subprocess.Popen(full_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                if self.cached_password and process.stdin:
                    try:
                        process.stdin.write(self.cached_password + "\n")
                        process.stdin.flush()
                    except Exception as exc:
                        logger.exception("Failed to send cached password", exc_info=exc)
                        GLib.idle_add(self.append_terminal_line, _("❌ Failed to send password to command.\n"))

                def read_output():
                    if not process.stdout:
                        return
                    try:
                        line = process.stdout.readline()
                        if line:
                            GLib.idle_add(self.append_terminal_line, line)
                            return True
                        else:
                            process.wait()
                            self.term_spinner.stop()
                            success = process.returncode == 0
                            if success:
                                self.term_title.set_label(_("✅ Done"))
                                GLib.timeout_add(2000, lambda: (self.term_dialog.close(), False)[1])
                            else:
                                self.term_title.set_label(_("❌ Failed"))
                                header.set_show_end_title_buttons(True)

                            if callback: callback(success)
                            return False
                    except Exception as exc:
                        logger.exception("Failed to read command output", exc_info=exc)
                        GLib.idle_add(self.term_title.set_label, _("❌ Failed"))
                        GLib.idle_add(self.append_terminal_line, _("❌ Error reading command output.\n"))
                        if callback:
                            GLib.idle_add(callback, False)
                        return False
                GLib.timeout_add(50, read_output)
            except Exception as exc:
                logger.exception("Failed to start command", exc_info=exc)
                GLib.idle_add(self.term_title.set_label, _("❌ Failed"))
                GLib.idle_add(self.append_terminal_line, _("❌ Failed to start command.\n"))
                if callback:
                    GLib.idle_add(callback, False)

        GLib.timeout_add(500, lambda: (run_command(), False)[1])
