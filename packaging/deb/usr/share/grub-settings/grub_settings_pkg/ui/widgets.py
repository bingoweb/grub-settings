import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from ..utils import logger

# Help text definitions
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

def create_help_button(help_key, parent_window):
    """Create a help button that shows a dialog with explanation."""
    btn = Gtk.Button()
    btn.set_icon_name("dialog-question-symbolic")
    btn.add_css_class("flat")
    btn.add_css_class("circular")
    btn.set_valign(Gtk.Align.CENTER)
    btn.set_tooltip_text(_("Get information about this setting"))

    def show_help(button):
        dialog = Adw.MessageDialog.new(parent_window)
        dialog.set_heading("ℹ️ " + _("Info"))
        dialog.set_body_use_markup(True)
        dialog.set_body(HELP_TEXTS.get(help_key, _("Description not found.")))
        dialog.add_response("ok", _("Got it"))
        dialog.present()

    btn.connect("clicked", show_help)
    return btn

class PoliteAuthDialog(Gtk.Window):
    """Polite password request dialog."""
    def __init__(self, parent=None):
        try:
            super().__init__()
            logger.info("DEBUG: PoliteAuthDialog initializing...")

            self.set_title(_("Permission Required 🌸"))
            self.set_default_size(350, 300)
            self.set_resizable(False)
            self.set_modal(True)

            if parent:
                self.set_transient_for(parent)

            self._callback = None

            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
            main_box.set_margin_top(24)
            main_box.set_margin_bottom(24)
            main_box.set_margin_start(24)
            main_box.set_margin_end(24)

            icon_label = Gtk.Label()
            icon_label.set_markup("<span size='40000'>🔐</span>")
            main_box.append(icon_label)

            title = Gtk.Label(label=_("Permission Required"))
            title.add_css_class("title-2")
            main_box.append(title)

            body_text = _("I need administrator permission to perform this action.\nCould you please enter your password? 🥺")
            body = Gtk.Label(label=body_text)
            body.set_justify(Gtk.Justification.CENTER)
            body.set_wrap(True)
            main_box.append(body)

            self.password_entry = Gtk.PasswordEntry()
            self.password_entry.set_property("placeholder-text", _("Sudo password"))
            self.password_entry.connect("activate", self.on_ok_clicked)
            self.password_entry.set_margin_top(8)
            self.password_entry.set_margin_bottom(8)
            main_box.append(self.password_entry)

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
