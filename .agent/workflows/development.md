---
description: GRUB Settings geliştirme ve release yönetimi workflow'u
---

# GRUB Settings Development Workflow

## 🧑‍💻 Geliştirici Profili
Sen bir **Python uzmanı** ve **Linux yazılım geliştiricisi**sin. Bu proje:
- GTK4 + LibAdwaita kullanıyor
- Tüm Linux dağıtımlarında çalışabilecek bir uygulama
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

### 2. README Güncellemesi
**Her yeni özellik veya değişiklikte README.md'yi güncelle!**
- Features bölümüne yeni özellikler ekle
- Ekran görüntülerini güncelle
- Kurulum talimatlarını kontrol et

### 3. Commit ve Push
```bash
git add .
git commit -m "v0.1.x: [Değişiklik açıklaması]"
git push
```

---

## 🚀 Yeni Release Oluşturma (Otomatik!)

GitHub Actions artık otomatik derleme yapıyor! Sadece tag push et:

// turbo
1. Versiyonu güncelle ve commit et

// turbo
2. Tag oluştur ve push et:
```bash
git tag -a v0.x.x -m "v0.x.x - [Açıklama]"
git push origin v0.x.x
```

3. **Otomatik olarak:**
   - `.deb` paketi oluşturulur
   - Kaynak kod arşivi oluşturulur
   - Her ikisi de Release'e yüklenir

---

## 📦 Flathub Güncellemesi

**ÖNEMLİ:** Her değişiklikte Flathub durumu dikkate alınmalı!

1. Upstream repo güncellendiğinde Flathub manifest'i de güncellenmeli
2. Commit hash güncelle: `flathub_pr/io.github.taylan.grubsettings.yml`
3. Değişiklikleri Flathub branch'ine push et:
```bash
cd flathub_pr
git add io.github.taylan.grubsettings.yml
git commit -m "Update to v0.x.x"
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
- [ ] Kod temizliği yapıldı
- [ ] Test edildi
- [ ] Git tag push edildi (otomatik build tetiklenir)
- [ ] Flathub manifest güncellendi
