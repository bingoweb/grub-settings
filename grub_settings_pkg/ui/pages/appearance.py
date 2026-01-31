import os
from gi.repository import Gtk, Adw, GdkPixbuf, Gdk, Gio, GLib
from ..widgets import create_help_button, PoliteAuthDialog
from ...utils import logger, restart_app
from ...config import config_manager

class AppearancePage(Gtk.Box):
    """Appearance settings page"""

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

        info_row = Adw.ActionRow()
        info_row.set_title(_("Supported Formats"))
        info_row.set_subtitle(_("PNG, JPEG, TGA - Should match your screen resolution"))
        info_row.add_prefix(create_help_button("background", app.win, _("Background Image")))
        bg_group.add(info_row)

        preview_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        preview_container.set_margin_top(12)
        preview_container.set_margin_bottom(12)

        self.preview_frame = Gtk.Frame()
        self.preview_frame.set_size_request(-1, 180)
        self.preview_frame.add_css_class("card")

        self.preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.preview_image = Gtk.Picture()
        self.preview_image.set_size_request(300, 169)
        self.preview_image.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.preview_image.set_halign(Gtk.Align.CENTER)
        self.preview_image.set_valign(Gtk.Align.CENTER)

        # Empty State
        self.empty_state = Gtk.Button()
        self.empty_state.add_css_class("flat")
        self.empty_state.set_vexpand(True)
        self.empty_state.set_hexpand(True)
        self.empty_state.set_tooltip_text(_("Click to select a background image"))
        self.empty_state.connect("clicked", self.on_select_image)
        try:
            self.empty_state.update_property([Gtk.AccessibleProperty.LABEL], [_("Select Background Image")])
        except AttributeError:
            pass

        empty_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        empty_content.set_valign(Gtk.Align.CENTER)
        empty_content.set_halign(Gtk.Align.CENTER)

        empty_icon = Gtk.Image.new_from_icon_name("image-x-generic-symbolic")
        empty_icon.set_pixel_size(64)
        empty_icon.add_css_class("dim-label")

        empty_title = Gtk.Label(label=_("No Background Image"))
        empty_title.add_css_class("title-4")

        empty_subtitle = Gtk.Label(label=_("Click 'Select Image' to add a custom background"))
        empty_subtitle.add_css_class("dim-label")

        empty_content.append(empty_icon)
        empty_content.append(empty_title)
        empty_content.append(empty_subtitle)

        self.empty_state.set_child(empty_content)
        self.preview_box.append(self.empty_state)
        self.preview_frame.set_child(self.preview_box)
        preview_container.append(self.preview_frame)

        # Check existing
        current_bg = app.grub_config.get("GRUB_BACKGROUND", "")
        if current_bg and os.path.exists(current_bg):
            self.set_preview_image(current_bg, mark_as_changed=False)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.CENTER)

        select_btn = Gtk.Button()
        select_btn_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        select_btn_content.append(Gtk.Label(label="📁"))
        select_btn_content.append(Gtk.Label(label=_("Select Image")))
        select_btn.set_child(select_btn_content)
        select_btn.add_css_class("suggested-action")
        select_btn.add_css_class("pill")
        select_btn.set_tooltip_text(_("Choose a new background image from your files"))
        try:
            select_btn.update_property([Gtk.AccessibleProperty.LABEL], [_("Select Image")])
        except AttributeError:
            pass
        select_btn.connect("clicked", self.on_select_image)

        remove_btn = Gtk.Button()
        remove_btn_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        remove_btn_content.append(Gtk.Label(label="🗑️"))
        remove_btn_content.append(Gtk.Label(label=_("Remove")))
        remove_btn.set_child(remove_btn_content)
        remove_btn.add_css_class("destructive-action")
        remove_btn.add_css_class("pill")
        remove_btn.set_tooltip_text(_("Remove the current background image"))
        try:
            remove_btn.update_property([Gtk.AccessibleProperty.LABEL], [_("Remove Image")])
        except AttributeError:
            pass
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
        res_row.add_prefix(create_help_button("resolution", app.win, _("Screen Resolution")))

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

    def set_preview_image(self, path, mark_as_changed=True):
        """Set preview image. mark_as_changed=False used when loading existing setting."""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 300, 169, True)
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.preview_image.set_paintable(texture)
            try:
                self.preview_image.update_property([Gtk.AccessibleProperty.LABEL], [_("Preview of selected background image")])
            except AttributeError:
                pass

            if self.empty_state.get_parent():
                self.preview_box.remove(self.empty_state)
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
        if self.empty_state.get_parent() is None:
            self.preview_box.append(self.empty_state)
        self.selected_background = None
        self.app.mark_changed()

    def get_values(self):
        values = {}

        selected = self.res_row.get_selected()
        if selected < len(self.resolutions):
            res = self.resolutions[selected].split(" - ")[0].split()[0]
            values["GRUB_GFXMODE"] = res

        if self.selected_background:
            if self.selected_background.startswith("/boot/grub/"):
                values["GRUB_BACKGROUND"] = self.selected_background
            else:
                ext = os.path.splitext(self.selected_background)[1].lower()
                if ext == ".jpeg":
                    ext = ".jpg"
                values["GRUB_BACKGROUND"] = f"/boot/grub/background{ext}"
                values["_ORIGINAL_BACKGROUND"] = self.selected_background

            values["GRUB_TERMINAL_OUTPUT"] = "gfxterm"

        return values
