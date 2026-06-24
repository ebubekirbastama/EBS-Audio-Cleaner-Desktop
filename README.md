# EBS Audio Cleaner Desktop

EBS Audio Cleaner Desktop, video ve ses dosyalarındaki dip ses, tıslama, fan/klima uğultusu, elektrik uğultusu, nefes/puf sesleri ve arka plan konuşmalarını azaltmak için geliştirilmiş masaüstü Python uygulamasıdır.

Özellikle röportaj, haber videosu, sokak röportajı, podcast, YouTube içerikleri ve sosyal medya videoları için hazırlanmıştır.

## Özellikler

- Video dosyası seçme
- Program içinden ses önizleme
- 15 saniyelik hızlı önizleme oluşturma
- Ses dalgası görüntüleme
- Dip ses azaltma
- Tıslama ve sibilans azaltma
- Fan / klima uğultusu azaltma
- 50Hz / 60Hz elektrik uğultusu azaltma
- Nefes ve puf seslerini azaltma
- Arka plan insan seslerini bastırma
- Röportaj modu
- Podcast modu
- Sokak röportajı modu
- Agresif nefes temizleme modu
- CPU / NVIDIA CUDA / AMD-Intel DirectML motor seçimi
- Çıktıyı otomatik olarak programın çalıştığı klasöre kaydetme

## Kullanım Alanları

- Haber röportajları
- Sokak röportajları
- Podcast kayıtları
- YouTube videoları
- Sosyal medya videoları
- Basın toplantısı kayıtları
- Eğitim videoları
- Telefon veya kamera ile çekilmiş gürültülü videolar

## Gereksinimler

- Windows 10 / Windows 11
- Python 3.10 veya üzeri
- FFmpeg

## FFmpeg Kurulumu

Windows için FFmpeg kurulumu:

```bash
winget install Gyan.FFmpeg
```

Kurulumdan sonra terminali kapatıp tekrar açın ve kontrol edin:

```bash
ffmpeg -version
```

## Python Kurulumu

Gerekli Python paketlerini yükleyin:

```bash
pip install -r requirements.txt
```

Alternatif olarak:

```bash
pip install numpy sounddevice soundfile matplotlib
```

## Çalıştırma

```bash
python EBS_AudioCleaner_Desktop.py
```

## Çıktı Klasörü

İşlenen video dosyaları otomatik olarak programın çalıştığı klasöre kaydedilir.

Önizleme dosyaları ise `onizlemeler` klasöründe oluşturulur.

## Motor Seçenekleri

Uygulama farklı sistemlerde çalışacak şekilde tasarlanmıştır:

| Motor | Açıklama |
|---|---|
| Otomatik | Uygun sistemi kendisi seçmeye çalışır |
| CPU | Tüm bilgisayarlarda çalışır |
| NVIDIA CUDA | NVIDIA ekran kartı olan sistemler için |
| AMD-Intel DirectML | AMD / Intel GPU bulunan sistemler için |

> Not: CPU modu tüm sistemlerde en uyumlu seçenektir. AI tabanlı GPU işlemleri sistem donanımına ve kurulu paketlere göre değişebilir.

## Nefes Sesi Temizleme

Uygulamada nefes/puf seslerini azaltmak için özel filtre seçenekleri bulunur.  
Hafif mod konuşmayı doğal bırakmaya çalışır.  
Agresif mod ise konuşmalar arasındaki nefesleri daha belirgin şekilde bastırır.

## Arka Plan İnsan Sesleri

Tek kanal bir kayıtta arka plandaki insan seslerini yüzde yüz silmek teknik olarak her zaman mümkün değildir.  
Bu uygulama, röportaj yapılan ana sesi öne çıkarıp arka plan konuşmalarını bastırmaya yardımcı olur.



## Geliştirici

Ebubekir Bastama  
GitHub: [ebubekirbastama](https://github.com/ebubekirbastama)
