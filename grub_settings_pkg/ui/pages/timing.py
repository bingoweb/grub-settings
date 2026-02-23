from gi.repository import Gtk, Adw
from ..widgets import create_help_button

class TimingPage(Gtk.Box):
    """Timing settings page"""

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

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_icon = Gtk.Label(label="⏱️")
        title_icon.add_css_class("title-1")
        title = Gtk.Label(label=_("Timing Settings"))
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        header_box.append(title_icon)
        header_box.append(title)
        content.append(header_box)

        desc = Gtk.Label(label=_("Adjust how long the GRUB menu appears when the computer starts."))
        desc.add_css_class("dim-label")
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)
        content.append(desc)

        # Timeout Group
        timeout_group = Adw.PreferencesGroup()
        timeout_group.set_title(_("⏰ Timeout Duration"))
        timeout_group.set_description(_("Time to display GRUB menu (in seconds)"))

        timeout_row = Adw.ActionRow()
        timeout_row.set_title(_("Duration"))
        timeout_row.set_subtitle(_("0 = Menu hidden, boots immediately"))
        timeout_row.add_prefix(create_help_button("timeout", app.win, _("Timeout Duration")))

        slider_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        slider_box.set_valign(Gtk.Align.CENTER)

        self.timeout_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 30, 1)
        self.timeout_scale.set_size_request(200, -1)
        self.timeout_scale.add_mark(0, Gtk.PositionType.BOTTOM, "0")
        self.timeout_scale.add_mark(5, Gtk.PositionType.BOTTOM, "5")
        self.timeout_scale.add_mark(10, Gtk.PositionType.BOTTOM, "10")
        self.timeout_scale.add_mark(30, Gtk.PositionType.BOTTOM, "30")
        try:
            self.timeout_scale.update_property([Gtk.AccessibleProperty.LABEL], [_("Timeout Duration")])
        except AttributeError:
            pass

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

        # Menu Style Group
        style_group = Adw.PreferencesGroup()
        style_group.set_title(_("👁️ Menu Visibility"))
        style_group.set_description(_("Choose how the GRUB menu is displayed"))

        current_style = app.grub_config.get("GRUB_TIMEOUT_STYLE", "menu")

        style_row1 = Adw.ActionRow()
        style_row1.set_title(_("Show Menu"))
        style_row1.set_subtitle(_("GRUB menu is fully visible on every boot"))
        style_row1.add_prefix(create_help_button("timeout_style", app.win, _("Menu Visibility")))
        self.style_menu = Gtk.CheckButton()
        self.style_menu.set_active(current_style == "menu")
        self.style_menu.connect("toggled", lambda b: app.mark_changed())
        style_row1.add_suffix(self.style_menu)
        style_row1.set_activatable_widget(self.style_menu)

        style_row2 = Adw.ActionRow()
        style_row2.set_title(_("Hidden"))
        style_row2.set_subtitle(_("Show by holding down the Shift key"))
        self.style_hidden = Gtk.CheckButton()
        self.style_hidden.set_group(self.style_menu)
        self.style_hidden.set_active(current_style == "hidden")
        self.style_hidden.connect("toggled", lambda b: app.mark_changed())
        style_row2.add_suffix(self.style_hidden)
        style_row2.set_activatable_widget(self.style_hidden)

        style_row3 = Adw.ActionRow()
        style_row3.set_title(_("Countdown"))
        style_row3.set_subtitle(_("Only the remaining time is shown"))
        self.style_countdown = Gtk.CheckButton()
        self.style_countdown.set_group(self.style_menu)
        self.style_countdown.set_active(current_style == "countdown")
        self.style_countdown.connect("toggled", lambda b: app.mark_changed())
        style_row3.add_suffix(self.style_countdown)
        style_row3.set_activatable_widget(self.style_countdown)

        # UX: Warning for Hidden/Countdown style with 0 timeout
        self.warning_row = Adw.ActionRow()
        self.warning_row.set_title(_("⚠️ Configuration Warning"))
        self.warning_row.set_subtitle(_("Timeout must be greater than 0 for this visibility style."))
        self.warning_row.add_css_class("warning")
        self.warning_row.set_visible(False)
        style_group.add(self.warning_row)

        # Connect signals for style changes
        self.style_menu.connect("toggled", self.on_style_changed)
        self.style_hidden.connect("toggled", self.on_style_changed)
        self.style_countdown.connect("toggled", self.on_style_changed)

        style_group.add(style_row1)
        style_group.add(style_row2)
        style_group.add(style_row3)
        content.append(style_group)

        # Initial validation state
        self.update_warning_state()

        scrolled.set_child(content)
        self.append(scrolled)

    def update_warning_state(self):
        style_hidden = self.style_hidden.get_active()
        style_countdown = self.style_countdown.get_active()
        timeout = int(self.timeout_scale.get_value())

        # If hidden or countdown style is selected, timeout must be > 0
        show_warning = (style_hidden or style_countdown) and timeout == 0
        self.warning_row.set_visible(show_warning)

    def on_style_changed(self, button):
        self.update_warning_state()
        if button.get_active():
            self.app.mark_changed()

    def update_timeout_label(self, value):
        if value == 0:
            self.timeout_label.set_label(_("Off"))
        else:
            self.timeout_label.set_label(f"{int(value)} s")

    def on_timeout_changed(self, scale):
        value = int(scale.get_value())
        self.update_timeout_label(value)
        self.update_warning_state()
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
