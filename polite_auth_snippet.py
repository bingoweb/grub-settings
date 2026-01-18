class PoliteAuthDialog(Adw.MessageDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.set_heading("İzin Gerekli 🌸")
        self.set_body(
            "Bu işlemi yapabilmek için yönetici iznine ihtiyacım var.\nRica etsem şifrenizi girer misiniz? 🥺"
        )
        self.add_response("cancel", "Vazgeç")
        self.add_response("ok", "Tamam")
        self.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)

        # Password entry
        self.password_entry = Gtk.PasswordEntry()
        self.password_entry.set_placeholder_text("Sudo şifresi")
        self.password_entry.set_margin_top(12)
        self.password_entry.set_margin_bottom(12)
        self.password_entry.set_activates_default(True)
        # self.password_entry.connect("activate", lambda w: self.response("ok")) # activates_default yeterli

        # Container
        pass_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        pass_box.set_spacing(12)

        # Cute icon/image
        icon = Gtk.Label(label="🔐")
        icon.add_css_class("title-1")
        pass_box.append(icon)
        pass_box.append(self.password_entry)

        self.set_extra_child(pass_box)

    def get_password(self):
        return self.password_entry.get_text()
