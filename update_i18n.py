#!/usr/bin/env python3
import os
import subprocess
import re

# English -> Turkish Dictionary
# Based on original source code strings
TR_TRANSLATIONS = {
    # PoliteAuthDialog
    "Permission Required 🌸": "İzin Gerekli 🌸",
    "Permission Required": "İzin Gerekli",
    "I need administrator permission to perform this action.\\nCould you please enter your password? 🥺": "Bu işlemi yapabilmek için yönetici iznine ihtiyacım var.\\nRica etsem şifrenizi girer misiniz? 🥺",
    "Sudo password": "Sudo şifresi",
    "Cancel": "Vazgeç",
    "OK": "Tamam",

    # Main Window
    "GRUB Settings": "GRUB Ayarları",
    "Reload Settings": "Ayarları Yeniden Yükle",
    "About": "Hakkında",
    "Apply Changes": "Değişiklikleri Uygula",
    "Categories": "Kategoriler",
    "Click the ❓ button next to each setting for detailed explanation.": "Her ayarın yanındaki ❓ butonuna tıklayarak detaylı açıklama alabilirsiniz.",

    # Navigation
    "Timing": "Zamanlama",
    "Menu timeout and visibility settings": "Menü süresi ve görünürlük ayarları",
    "Appearance": "Görünüm",
    "Background image and resolution": "Arkaplan resmi ve çözünürlük",
    "System": "Sistem",
    "Default OS and dual-boot": "Varsayılan OS ve dual-boot",
    "Advanced": "Gelişmiş",
    "Kernel parameters and recovery": "Kernel parametreleri ve kurtarma",

    # Settings Pages
    "Timing Settings": "Zamanlama Ayarları",
    "Adjust how long the GRUB menu appears when the computer starts.": "Bilgisayar açıldığında GRUB menüsünün ne kadar süre görüneceğini ayarlayın.",
    "Show Menu": "Her Zaman Göster",
    "GRUB menu is fully visible on every boot": "GRUB menüsü her açılışta tam olarak görünür",
    "Hidden": "Gizli",
    "Show by holding down the Shift key": "Shift tuşuna basılı tutarak gösterin",
    "Countdown": "Geri Sayım",
    "Only the remaining time is shown": "Sadece kalan süre gösterilir",
    "Timeout (seconds)": "Süre (saniye)",

    "Appearance Settings": "Görünüm Ayarları",
    "Customize the visual appearance of the GRUB menu.": "GRUB menüsünün görsel özelliklerini özelleştirin.",
    "🖼️ No background image selected\\nClick the button below to select an image": "🖼️ Arkaplan resmi seçilmedi\\nAşağıdaki butona tıklayarak resim seçin",
    "Select Image": "Resim Seç",
    "Remove": "Kaldır",
    "Screen Resolution": "Ekran Çözünürlüğü",
    "Default": "Varsayılan",

    "System Settings": "Sistem Ayarları",
    "Configure operating system selection and dual-boot settings.": "İşletim sistemi seçimi ve dual-boot ayarlarını yapılandırın.",
    "Show Other Operating Systems (OS Prober)": "Diğer İşletim Sistemlerini Göster (OS Prober)",
    "Automatically detects Windows and other Linux distros.": "Windows ve diğer Linux dağıtımlarını otomatik bulur.",
    "Add Windows Boot Manager": "Windows Boot Manager Ekle",
    
    "Advanced Settings": "Gelişmiş Ayarlar",
    "Customize kernel parameters and boot behavior.": "Kernel parametreleri ve açılış davranışını özelleştirin.",
    "Settings in this section may affect system boot. Be careful!": "Bu bölümdeki ayarlar sisteminizin açılışını etkileyebilir. Dikkatli olun!",
    "Kernel Parameters": "Çekirdek (Kernel) Parametreleri",
    "Quiet Boot (quiet)": "Sessiz Açılış (quiet)",
    "Show Recovery Mode": "Kurtarma Modunu Göster",

    # Language Settings
    "Language Settings": "Dil Ayarları",
    "Select application language": "Uygulama dilini seçin",
    "Application Language": "Uygulama Dili",
    "Changes require restart": "Değişiklikler yeniden başlatma gerektirir",
    "Restart Required 🔄": "Yeniden Başlatma Gerekli 🔄",
    "Language Changed": "Dil Değiştirildi",
    "To apply the new language, I need to make a tiny restart.\\nIs that okay correctly? 🥺": "Yeni dili uygulayabilmem için ufak bir yeniden başlatma yapmam gerekiyor.\\nBuna izin verir misiniz? 🥺",
    "Later": "Daha Sonra",
    "Restart Now": "Şimdi Başlat"
}
# Note: "Show Menu" key appears twice in my context logic above (one for style, one for dropdown). 
# Need to be careful. The style one was "Her Zaman Göster". The dropdown one "Menüyü Göster".
# In .pot they are the same msgid "Show Menu". 
# So I have to choose ONE translation. "Menüyü Göster" is generic enough.
# Let's override:
TR_TRANSLATIONS["Show Menu"] = "Menüyü Göster"

def run(cmd):
    print(f"Running: {cmd}")
    subprocess.check_call(cmd, shell=True)

def populate_po(po_file, translations):
    """
    Very naive PO parser/filler.
    Reads line by line. If finds msgid "...", looks up map, writes msgstr.
    """
    print(f"Populating {po_file}...")
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    current_msgid = None
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if line.startswith('msgid "'):
            # Extract msgid
            match = re.search(r'msgid "(.*)"', line)
            if match:
                current_msgid = match.group(1)
                # Handle multiline msgid ?? For now assume single line or we check next lines?
                # This script is simple.
        
        if line.startswith('msgstr "') and current_msgid:
            # We found the msgstr for the current msgid
            # Check translation
            # We need to unescape newlines in dictionary keys to match
            if current_msgid in translations:
                trans = translations[current_msgid]
                new_line = f'msgstr "{trans}"\n'
                new_lines.append(new_line)
                current_msgid = None
                i += 1
                continue
            
            # Try escaping newlines in key
            key_esc = current_msgid.replace('\\n', '\n') 
            # Actually parsing PO is harder. 
            # Let's perform simple string exact match on what we put in TR_TRANSLATIONS keys
            # My TR_TRANSLATIONS have '\\n' literal which matches PO format properly
            
            # Simple fallback
        
        new_lines.append(line)
        i += 1
        
    with open(po_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)


def main():
    # 1. Update POT
    print("Extracting strings...")
    run("xgettext -d grub-settings -o locales/grub-settings.pot -L Python --from-code=UTF-8 grub_settings.py")
    
    # 2. Init TR
    tr_po = "locales/tr/LC_MESSAGES/grub-settings.po"
    if not os.path.exists(tr_po):
        print("Initializing Turkish PO...")
        run(f"msginit -l tr_TR -i locales/grub-settings.pot -o {tr_po} --no-translator")
    else:
        print("Merging Turkish PO...")
        run(f"msgmerge -U {tr_po} locales/grub-settings.pot")
        
    # 3. Init EN
    en_po = "locales/en/LC_MESSAGES/grub-settings.po"
    if not os.path.exists(en_po):
        print("Initializing English PO...")
        run(f"msginit -l en_US -i locales/grub-settings.pot -o {en_po} --no-translator")
    else:
        run(f"msgmerge -U {en_po} locales/grub-settings.pot")
        
    # 4. Populate TR
    populate_po(tr_po, TR_TRANSLATIONS)
    
    # 5. Compile
    print("Compiling MO files...")
    run(f"msgfmt {tr_po} -o locales/tr/LC_MESSAGES/grub-settings.mo")
    run(f"msgfmt {en_po} -o locales/en/LC_MESSAGES/grub-settings.mo")
    
    print("Done! 🎉")

if __name__ == "__main__":
    main()
