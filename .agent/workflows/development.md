---
description: GRUB Settings geliştirme ve release yönetimi workflow'u
---

# GRUB Settings Development Workflow

## 🧑‍💻 Geliştirici Profili
Sen bir **Python uzmanı** ve **Linux yazılım geliştiricisi**sin. Bu proje:
- GTK4 + LibAdwaita kullanıyor
- Tüm Linux dağıtımlarında çalışabilecek **portable** bir uygulama
- **Flathub'da** yayınlanmak üzere başvuru yapılmış

---

## 📋 Her Önemli Değişiklik Sonrası

### 1. Versiyon Yükseltme
Her önemli değişiklik veya yenilik sonrası versiyonu küçük artırarak yükselt:

```
v1.2.0 → v1.2.1 (bug fix)
v1.2.1 → v1.2.2 (minor improvement)
v1.2.2 → v1.3.0 (new feature)
```

Versiyon numarası şurada güncellenmeli:
- `grub_settings.py` → `APP_VERSION` değişkeni
- `flatpak/io.github.taylan.grubsettings.metainfo.xml` → `<release>` tag

### 2. Commit ve Push
```bash
git add .
git commit -m "v1.2.1: [Değişiklik açıklaması]"
git push
```

---

## 🚀 Stabil Sürüm Release (GitHub)

Stabil kabul edilen her sürümü GitHub'a release olarak yükle:

### Adımlar:
// turbo
1. Versiyonu güncelle ve commit et

// turbo
2. Git tag oluştur:
```bash
git tag -a v1.2.1 -m "v1.2.1 - [Açıklama]"
git push origin v1.2.1
```

3. GitHub'da release oluştur:
```bash
gh release create v1.2.1 \
  --title "v1.2.1 - [Başlık]" \
  --notes "## Değişiklikler
- [Değişiklik 1]
- [Değişiklik 2]

## Kurulum
\`\`\`bash
chmod +x grub-settings
./grub-settings
\`\`\`"
```

4. PyInstaller ile build al ve release'e ekle:
```bash
pyinstaller --onefile --clean --name "grub-settings" --add-data "assets:assets" --add-data "locales:locales" grub_settings.py
gh release upload v1.2.1 dist/grub-settings
```

---

## 📦 Flathub Güncellemesi

**ÖNEMLİ:** Her değişiklikte Flathub durumu dikkate alınmalı!

1. Upstream repo güncellendiğinde Flathub manifest'i de güncellenmeli
2. Commit hash güncelle: `flathub_pr/io.github.taylan.grubsettings.yml`
3. Değişiklikleri Flathub branch'ine push et:
```bash
cd flathub_pr
git add io.github.taylan.grubsettings.yml
git commit -m "Update to v1.2.1"
git push
```

---

## 🔍 Periyodik Derin Debug

Belirli aralıklarla (özellikle major sürümlerden önce):

1. **Kod Temizliği:**
   - Kullanılmayan import'ları kaldır
   - Tekrarlanan kodları refactor et
   - Türkçe yorumları İngilizce'ye çevir

2. **Hata Ayıklama:**
   - Tüm exception handler'ları kontrol et
   - Logger mesajlarını gözden geçir
   - Edge case'leri test et

3. **Performans:**
   - Gereksiz widget yeniden çizimlerini kontrol et
   - Memory leak olup olmadığını kontrol et

---

## 📝 Checklist (Her Release Öncesi)

- [ ] Versiyon numarası güncellendi
- [ ] metainfo.xml'de release eklendi
- [ ] Changelog yazıldı
- [ ] Kod temizliği yapıldı
- [ ] Test edildi
- [ ] Git tag oluşturuldu
- [ ] GitHub release yayınlandı
- [ ] Flathub manifest güncellendi
