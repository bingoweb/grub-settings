from gi.repository import Gtk, Adw
from ..widgets import create_help_button

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

        custom_params = [p for p in current_params.split() if p not in ["quiet", "splash"]]
        self.custom_entry.set_text(" ".join(custom_params))
        self.custom_entry.connect("changed", lambda *a: app.mark_changed())

        custom_group.add(self.custom_entry)

        custom_info = Adw.ActionRow()
        custom_info.set_title(_("Example parameters"))
        custom_info.set_subtitle("nvidia-drm.modeset=1, nomodeset, acpi=off")
        custom_group.add(custom_info)

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

        if self.savedefault_switch.get_active():
            values["GRUB_DEFAULT"] = "saved"
            values["GRUB_SAVEDEFAULT"] = "true"

        return values
