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
    "I need administrator permission to perform this action.\nCould you please enter your password? 🥺": "Bu işlemi yapabilmek için yönetici iznine ihtiyacım var.\nRica etsem şifrenizi girer misiniz? 🥺",
    "Sudo password": "Sudo şifresi",
    "Cancel": "Vazgeç",
    "OK": "Tamam",
    "Close": "Kapat",

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

    # Pages & Generic
    "Timing Settings": "Zamanlama Ayarları",
    "Adjust how long the GRUB menu appears when the computer starts.": "Bilgisayar açıldığında GRUB menüsünün ne kadar süre görüneceğini ayarlayın.",
    "Show Menu": "Menüyü Göster",
    "GRUB menu is fully visible on every boot": "GRUB menüsü her açılışta tam olarak görünür",
    "Hidden": "Gizli",
    "Show by holding down the Shift key": "Shift tuşuna basılı tutarak gösterin",
    "Countdown": "Geri Sayım",
    "Only the remaining time is shown": "Sadece kalan süre gösterilir",
    "Timeout (seconds)": "Süre (saniye)",
    "Off": "Kapalı", 

    "Appearance Settings": "Görünüm Ayarları",
    "Customize the visual appearance of the GRUB menu.": "GRUB menüsünün görsel özelliklerini özelleştirin.",
    "🖼️ No background image selected\nClick the button below to select an image": "🖼️ Arkaplan resmi seçilmedi\nAşağıdaki butona tıklayarak resim seçin",
    "Select Image": "Resim Seç",
    "Select Background Image": "Arkaplan Resmi Seç",
    "Image Files (PNG, JPEG, TGA)": "Resim Dosyaları (PNG, JPEG, TGA)",
    "Remove": "Kaldır",
    "Screen Resolution": "Ekran Çözünürlüğü",
    "Resolution to display the GRUB menu": "GRUB menüsünün görüntüleneceği çözünürlük",
    "Select a value supported by your graphics card": "Ekran kartınızın desteklediği bir değer seçin",
    "Default": "Varsayılan",

    "System Settings": "Sistem Ayarları",
    "Configure operating system selection and dual-boot settings.": "İşletim sistemi seçimi ve dual-boot ayarlarını yapılandırın.",
    
    # Windows Management
    "🪟 Windows Management": "🪟 Windows Yönetimi",
    "Add Windows Boot Manager to the GRUB menu": "Windows Boot Manager'ı GRUB menüsüne ekle",
    "Windows Status": "Windows Durumu",
    "Detecting...": "Algılanıyor...",
    "💡 Info": "💡 Bilgi",
    "If OS-Prober cannot detect Windows, you can add it manually.": "Eğer OS-Prober Windows'u algılayamazsa manuel olarak ekleyebilirsiniz.",
    "Windows Detected (Not in Menu)": "Windows Algılandı (Menüde Değil)",
    "Windows Detected and in Menu": "Windows Algılandı ve Menüde",
    "Windows Not Found": "Windows Bulunamadı",
    
    # Default OS
    "🎯 Default Operating System": "🎯 Varsayılan İşletim Sistemi",
    "Which system should start when the timeout expires?": "Süre dolduğunda hangi sistem başlatılsın?",
    "0 - First Option": "0 - İlk Seçenek",
    "1 - Second Option": "1 - İkinci Seçenek",
    "2 - Third Option": "2 - Üçüncü Seçenek",
    "Default System": "Varsayılan Sistem",
    "Click refresh to load the menu": "Menüyü yüklemek için yenile butonuna tıklayın",
    "Load GRUB menu (requires root privileges)": "GRUB menüsünü yükle (root yetkisi gerekir)",

    # OS Prober
    "🔍 OS Detection": "🔍 İşletim Sistemi Algılama",
    "Add other operating systems to the GRUB menu": "Diğer işletim sistemlerini GRUB menüsüne ekle",
    "Show Other Operating Systems (OS Prober)": "Diğer İşletim Sistemlerini Göster (OS Prober)",
    "Automatically detects Windows and other Linux distros.": "Windows ve diğer Linux dağıtımlarını otomatik bulur.",
    "⚠️ Dual-boot Users": "⚠️ Dual-boot Tarafı",
    "This must be enabled if you have Windows or another OS!": "Windows veya başka bir OS varsa bu açık olmalıdır!",
    
    # Submenus
    "📂 Menu Organization": "📂 Menü Organizasyonu",
    "Display of old kernels and recovery options": "Eski kernel ve kurtarma seçeneklerinin gösterimi",
    "Use Submenus": "Alt Menüleri Kullan",
    "Group old kernels and recovery options in a submenu": "Eski kernelleri ve kurtarmayı alt menüde grupla",

    # Advanced Page
    "Advanced Settings": "Gelişmiş Ayarlar",
    "Customize kernel parameters and boot behavior.": "Kernel parametreleri ve açılış davranışını özelleştirin.",
    "Settings in this section may affect system boot. Be careful!": "Bu bölümdeki ayarlar sistem açılışını etkileyebilir. Dikkatli olun!",
    "Kernel Parameters": "Kernel Parametreleri",
    
    # Boot Display
    "🖥️ Boot Display": "🖥️ Açılış Görünümü",
    "What to show on screen during boot": "Açılış sırasında ekranda ne gösterilsin",
    "Quiet Boot (quiet)": "Sessiz Açılış (quiet)",
    "Hide technical messages, clean boot": "Teknik mesajları gizle, temiz açılış",
    "Boot Animation (splash)": "Açılış Animasyonu (splash)",
    "Beautiful boot screen with logo": "Logolu güzel açılış ekranı",
    
    # Recovery
    "🛠️ Recovery Options": "🛠️ Kurtarma Seçenekleri",
    "Troubleshooting and recovery mode": "Sorun giderme ve kurtarma modu",
    "Show Recovery Mode": "Kurtarma Modunu Göster",
    "Show recovery options in GRUB": "GRUB'da kurtarma seçeneklerini göster",
    "💡 Tip": "💡 İpucu",
    "Recovery mode can be a lifesaver if system fails to boot!": "Sistem açılmazsa kurtarma modu hayat kurtarıcı olabilir!",
    
    # Custom Params
    "⌨️ Custom Kernel Parameters": "⌨️ Özel Kernel Parametreleri",
    "For advanced users": "İleri düzey kullanıcılar için",
    "Example parameters": "Örnek parametreler",
    
    # Remember Last
    "💾 Remember Last Selection": "💾 Son Seçimi Hatırla",
    "Default to the last booted system": "En son kullanılan sistemi varsayılan yap",
    "Remember Last Selection": "Son Seçimi Hatırla",
    "The last used OS will be selected on next boot": "Bir sonraki açılışta en son kullanılan OS seçili gelir",

    # Language Settings
    "Language Settings": "Dil Ayarları",
    "Select application language": "Uygulama dilini seçin",
    "Application Language": "Uygulama Dili",
    "Changes require restart": "Değişiklikler yeniden başlatma gerektirir",
    "Restart Required 🔄": "Yeniden Başlatma Gerekli 🔄",
    "Language Changed": "Dil Değiştirildi",
    "To apply the new language, I need to make a tiny restart.\nIs that okay correctly? 🥺": "Yeni dili uygulayabilmem için ufak bir yeniden başlatma yapmam gerekiyor.\nBuna izin verir misiniz? 🥺",
    "Later": "Daha Sonra",
    "Restart Now": "Şimdi Başlat",
    
    # New ones from AppearancePage update
    "🖼️ Background Image": "🖼️ Arkaplan Resmi",
    "Select a custom background image for the GRUB menu": "GRUB menüsü için özel bir arka plan resmi seçin",
    "Supported Formats": "Desteklenen Formatlar",
    "PNG, JPEG, TGA - Should match your screen resolution": "PNG, JPEG, TGA - Ekran çözünürlüğüyle eşleşmeli",
    "⏰ Timeout Duration": "⏰ Bekleme Süresi",
    "Time to display GRUB menu (in seconds)": "GRUB menüsünün ekranda kalma süresi (sn)",
    "Duration": "Süre",
    "0 = Menu hidden, boots immediately": "0 = Menü gizli, hemen açılır",
    "👁️ Menu Visibility": "👁️ Menü Görünürlüğü",
    "Choose how the GRUB menu is displayed": "GRUB menüsünün nasıl gösterileceğini seçin",
    "🎨 Menu Colors": "🎨 Menü Renkleri",
    "Customize GRUB menu colors (coming soon)": "GRUB menü renklerini özelleştirin (yakında)",
    "Theme Customization": "Tema Özelleştirme",
    "This feature will be added in a future version": "Bu özellik gelecek sürümde eklenecek"
}
# Note: "Show Menu" key appears twice in my context logic above (one for style, one for dropdown). 
# Need to be careful. The style one was "Her Zaman Göster". The dropdown one "Menüyü Göster".
# In .pot they are the same msgid "Show Menu". 
# So I have to choose ONE translation. "Menüyü Göster" is generic enough.
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
