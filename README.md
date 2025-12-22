# PicoW-MPU6050--PicoSpaceGame
# Pico W + MPU6050 Tabanlı 3D Uzay Oyunu (GameIoT)

Bu proje, **Raspberry Pi Pico W** ve **MPU6050 IMU sensörü** kullanılarak geliştirilen,  
fiziksel hareketlerin **gerçek zamanlı olarak tarayıcı tabanlı 3D bir oyunu kontrol ettiği**
IoT tabanlı bir oyun sistemidir.

Proje, **Nesnelerin İnterneti (IoT)** ile **interaktif oyun sistemlerinin (GameIoT)**
entegrasyonunu modellemektedir.

---

## 🎮 Proje Özeti

MPU6050 sensöründen alınan ivme ve jiroskop verileri,  
Pico W üzerinde **MicroPython** ile işlenir ve **JSON formatında** bir web API üzerinden yayınlanır.

Tarayıcı tarafında çalışan **Three.js (WebGL)** tabanlı 3D oyun motoru,
bu verileri sürekli alarak uzay gemisinin yönelimini **gerçek zamanlı** olarak günceller.

> Fiziksel hareket → Sensör → Pico W → Web Sunucu → Tarayıcı → 3D Oyun

---

## 🧩 Kullanılan Teknolojiler

### Donanım
- **Raspberry Pi Pico W (RP2040)**
- **MPU6050 (6-Eksen IMU)**
- I2C Haberleşme Protokolü
- USB Güç ve Programlama

### Yazılım
- **MicroPython**
- Socket tabanlı gömülü web sunucusu
- **RESTful JSON API**
- **HTML5 / CSS3 (Glassmorphism UI)**
- **Three.js (WebGL)**

---

## 🔌 Donanım Bağlantıları

| Pico W Pin | MPU6050 |
|-----------|---------|
| 3.3V (Pin 36) | VCC |
| GND (Pin 38) | GND |
| GP21 (Pin 27) | SCL |
| GP20 (Pin 26) | SDA |

---

## ⚙️ Sistem Mimarisi

### 1️⃣ Sensör Veri İşleme
- Ham ivme ve jiroskop verileri okunur
- Pitch ve Roll açıları trigonometrik hesaplarla elde edilir
- Yaw açısı jiroskop entegrasyonu ile hesaplanır

### 2️⃣ Gömülü Web Sunucusu
- Pico W, **80 portu** üzerinden HTTP isteklerini dinler
- `/` → Oyun arayüzü (HTML / JS / CSS)
- `/data` → Anlık sensör verileri (JSON)

### 3️⃣ Oyun ve Grafik Motoru
- Three.js ile 3D sahne oluşturulur
- Uzay gemisi, engeller ve ödüller modellenir
- Sensör verileri ile gemi yönelimi güncellenir
- Çarpışma algılama ve skor sistemi çalışır

---

## 🚀 Çalıştırma Adımları

1. **MicroPython** firmware’i Pico W üzerine yükleyin
2. Bu repodaki `picospacegame.py` dosyasını karta atın
3. Kod içinde Wi-Fi bilgilerini girin:
   ```python
   ssid = 'WiFi_ADI'
   password = 'WiFi_SIFRESI'
Pico W çalıştırıldığında Terminal’de IP adresi görünecektir
Tarayıcıdan:
http://PICO_IP_ADRESI
adresine girin
📂 Dosya Yapısı
.
├── picospacegame.py   # Ana MicroPython uygulaması
├── README.md          # Proje dokümantasyonu

👥 Proje Ekibi
Azra Bahşi
Osman Küçük
Osmaniye Korkut Ata Üniversitesi
Bilgisayar Mühendisliği
BMB433 – Nesnelerin İnterneti ve Uygulamaları


