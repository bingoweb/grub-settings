import json
from gi.repository import Gtk, Adw
from ...utils import logger, get_path, restart_app
from ...config import config_manager

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

                style_manager = Adw.StyleManager.get_default()
                if new_theme == "light":
                    style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
                elif new_theme == "dark":
                    style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
                else:
                    style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
