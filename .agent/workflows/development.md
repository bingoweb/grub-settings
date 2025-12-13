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

### 1. Versiyon Yükseltme (Semantic Versioning)
```
0.x.x = Geliştirme aşaması (API değişebilir)
1.0.0 = İlk stabil sürüm (production-ready)

0.1.0 → 0.1.1 (bug fix)
0.1.1 → 0.1.2 (minor improvement)
0.1.2 → 0.2.0 (new feature)
```

Versiyon numarası şurada güncellenmeli:
- `grub_settings.py` → `APP_VERSION` değişkeni
- `flatpak/io.github.taylan.grubsettings.metainfo.xml` → `<release>` tag

### 2. Commit ve Push
```bash
git add .
git commit -m "v0.1.x: [Değişiklik açıklaması]"
git push
```

---

## 📖 README Güncellemesi

Belirli aralıklarla (özellikle yeni özellikler eklendiğinde) README.md'yi güncelle:

1. **Yeni Özellikler:** Features bölümüne ekle
2. **Ekran Görüntüleri:** Güncel screenshots ekle
3. **Kurulum Talimatları:** Değişiklik varsa güncelle
4. **Changelog:** Son değişiklikleri özetle

---

## 🚀 Stabil Sürüm Release (GitHub)

Stabil kabul edilen her sürümü GitHub'a release olarak yükle:

### Adımlar:
// turbo
1. Versiyonu güncelle ve commit et

// turbo
2. Git tag oluştur:
```bash
git tag -a v0.1.0 -m "v0.1.0 - [Açıklama]"
git push origin v0.1.0
```

3. GitHub'da release oluştur:
```bash
gh release create v0.1.0 \
  --title "v0.1.0 - [Başlık]" \
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
gh release upload v0.1.0 dist/grub-settings
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
git commit -m "Update to v0.1.0"
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
- [ ] README.md güncellendi (yeni özellikler varsa)
- [ ] Changelog yazıldı
- [ ] Kod temizliği yapıldı
- [ ] Test edildi
- [ ] Git tag oluşturuldu
- [ ] GitHub release yayınlandı
- [ ] Flathub manifest güncellendi
