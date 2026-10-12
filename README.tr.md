<div align="center">

[English](README.md) · **Türkçe** · [Deutsch](README.de.md)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./.github/assets/logo-white.png">
  <img src="./.github/assets/logo.png" alt="PrayerTaskbar logosu" title="PrayerTaskbar logosu" width="140"/>
</picture>

# PrayerTaskbar

### Namaz vakitleri doğrudan Windows görev çubuğunuzda
PrayerTaskbar, bir sonraki namaza kalan süreyi saatin hemen yanında gösterir. Tek tıkla bugünün namaz vakitlerini ve sıradaki mübarek günü görürsünüz.

[![Windows 11](https://img.shields.io/badge/Windows-11-0078D4?labelColor=27303D)](https://www.microsoft.com/windows/windows-11)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?labelColor=27303D&logo=python&logoColor=FFFFFF)](https://www.python.org)
[![PyQt](https://img.shields.io/badge/PyQt-6-41CD52?labelColor=27303D&logo=qt&logoColor=FFFFFF)](https://www.riverbankcomputing.com/software/pyqt/)
[![Lisans: MIT](https://img.shields.io/badge/license-MIT-27303D?labelColor=27303D&color=0877d2)](/LICENSE)

<img src="./.github/assets/prayer-times.png" alt="Görev çubuğunun üzerinde bugünün namaz vakitleri" width="380"/>

## İndir

[![Windows için indir](https://img.shields.io/badge/%C4%B0ndir-Windows-0078D4?labelColor=0067C0&color=005A9E)](https://github.com/Muhammed-Coskun/PrayerTaskbar/releases/latest/download/PrayerTaskbar-Setup.exe)

*Kurulum dosyasını çalıştırın, PrayerTaskbar görev çubuğunuzda görünür.*<br>
*Windows bir SmartScreen uyarısı gösterirse "Ek bilgi"ye ve ardından "Yine de çalıştır"a tıklayın.*<br>
*PrayerTaskbar açık kaynaklıdır. Her kurulum dosyası [GitHub Actions](https://github.com/Muhammed-Coskun/PrayerTaskbar/actions/workflows/release.yml) tarafından bu koddan oluşturulur.*

## Özellikler

<div align="left">

- **Görev çubuğunda geri sayım:** Bir sonraki namaza kalan süre, saatin hemen yanında. Son 15 dakikada kırmızıya döner.
- **Bugün tek bakışta:** Tek tıkla bugünün tüm namaz vakitleri, sıradaki namaz vurgulanmış olarak.
- **Sıradaki mübarek gün:** Ramazan veya bayram gibi bir sonraki mübarek güne kaç gün kaldığını görün. Tarihler Diyanet takvimine göredir.
- **Şehriniz:** Şehrinizi arayın, namaz vakitleri Diyanet'ten yüklenir.
- **Windows 11 için tasarlandı:** Açık ve koyu moda ve vurgu renginize uyum sağlar.
- **Üç dil:** İngilizce, Türkçe ve Almanca.
- **Otomatik güncellemeler:** Yeni sürümler uygulama başlarken kendiliğinden yüklenir. Bunu kapatırsanız uygulama yalnızca haber verir. Her güncelleme, yüklenmeden önce GitHub'daki sağlama toplamıyla karşılaştırılır.

</div>

## Ayarlar

Şehrinizi seçin veya Diyanet'ten bir namaz vakti tablosu içe aktarın.

<img src="./.github/assets/settings-location.png" alt="Konum ayarları" width="600"/>

Ekranı seçin ve widget'ı görev çubuğunda kaydırın.

<img src="./.github/assets/settings-taskbar.png" alt="Görev çubuğu ayarları" width="600"/>

Dili değiştirin ve PrayerTaskbar'ı Windows ile başlatın.

<img src="./.github/assets/settings-general.png" alt="Genel ayarlar" width="600"/>

### Gizlilik

PrayerTaskbar'da hesap, reklam ve takip yoktur. Uygulama yalnızca şunlara bağlanır:

<div align="left">

- **prayertimes.api.abdus.dev**: şehrinizin namaz vakitlerini yüklemek için
- **github.com**: güncellemeleri aramak ve indirmek için

</div>

Ayarlarınız bilgisayarınızda, `%APPDATA%\PrayerTaskbar` klasöründe kalır.

### Kaynak koddan derleme

<div align="left">

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m src.main
```

Uygulamayı ve kurulum dosyasını oluşturmak için `.venv\Scripts\pyinstaller --noconfirm PrayerTaskbar.spec` ve ardından [Inno Setup](https://jrsoftware.org/isinfo.php) ile `ISCC installer.iss` komutunu çalıştırın. [Release iş akışı](.github/workflows/release.yml) aynısını yapar ve ayrıca PyInstaller'ın bootloader'ını kaynak koddan derler.

</div>

### Teşekkürler

Namaz vakitleri [Diyanet](https://namazvakitleri.diyanet.gov.tr)'ten, [abdus.dev Diyanet API](https://prayertimes.api.abdus.dev/) aracılığıyla sağlanır.

### Lisans

[MIT Lisansı](/LICENSE) ile yayınlanmıştır.

</div>
