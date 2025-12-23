import network
import socket
from machine import Pin, I2C
import utime
import math
import ujson
import gc

# RAM optimizasyonu için bellek temizliği
gc.collect()

# --- 1. AĞ AYARLARI ---
ssid = 'ssid'
password = 'sifre'

# --- 2. SENSÖR SÜRÜCÜ KATMANI (MPU6050) ---
def init_mpu6050(i2c):
    """Sensörü uyku modundan çıkarır ve filtre ayarlarını yapar."""
    try:
        i2c.writeto_mem(0x68, 0x6B, b'\x00')  # Uyku modunu kapat
        utime.sleep_ms(100)
        i2c.writeto_mem(0x68, 0x19, b'\x07')  # Örnekleme hızı ayarı
        i2c.writeto_mem(0x68, 0x1A, b'\x03')  # DLPF (Gürültü filtresi)
    except: pass

def read_raw(i2c, addr):
    """Sensörden 16-bitlik ham veriyi okur ve işaretli tamsayıya çevirir."""
    try:
        h = i2c.readfrom_mem(0x68, addr, 1)[0]   # Yüksek bayt (High byte)
        l = i2c.readfrom_mem(0x68, addr+1, 1)[0] # Düşük bayt (Low byte)
        v = h << 8 | l
        if v > 32768: v -= 65536  # Signed (işaretli) dönüşüm
        return v
    except: return 0

# Jiroskop sapma hesabı için global değişkenler
yaw_z = 0.0
last_time = utime.ticks_ms()

def get_data(i2c):
    """İvmeölçer ve Jiroskop verilerini işleyerek Euler açılarını hesaplar."""
    global yaw_z, last_time
    
    # Ham ivme verilerini hassasiyet değerine bölerek normalize et
    ax = read_raw(i2c, 0x3B) / 16384.0
    ay = read_raw(i2c, 0x3D) / 16384.0
    az = read_raw(i2c, 0x3F) / 16384.0
    
    # Trigonometrik hesaplama ile X ve Y ekseni eğimlerini bul (Pitch & Roll)
    try:
        ang_x = math.atan2(ay, math.sqrt(ax*ax + az*az)) * 57.3
        ang_y = math.atan2(-ax, math.sqrt(ay*ay + az*az)) * 57.3
    except: ang_x = 0; ang_y = 0
    
    # Zaman farkını (Delta T) hesapla
    ct = utime.ticks_ms()
    dt = (ct - last_time) / 1000.0
    last_time = ct
    
    # Jiroskop verisi ile Z ekseni (Yaw) takibi
    gz = read_raw(i2c, 0x47) / 131.0
    if abs(gz) < 1: gz = 0  # Küçük titreşimleri yok say
    yaw_z += gz * dt
    
    # JSON formatında sözlük döndür
    return {'x': int(ang_x), 'y': int(ang_y), 'z': int(yaw_z)}

# --- 3. SİSTEM BAŞLATMA ---
print("Donanım Başlatılıyor...")
# I2C Protokolü kurulumu (SDA: Pin 20, SCL: Pin 21)
i2c = I2C(0, scl=Pin(21), sda=Pin(20), freq=400000)
init_mpu6050(i2c)

# Wi-Fi Bağlantı Döngüsü
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

wait = 20
while wait > 0 and wlan.status() != 3:
    wait -= 1
    utime.sleep(1)

if wlan.status() == 3:
    print(f'Sunucu Aktif: http://{wlan.ifconfig()[0]}')
else:
    print("Wi-Fi Bağlantı Hatası!")

# Web Sunucusu Soket Kurulumu (Port 80)
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try: s.bind(('', 80))
except: pass
s.listen(5) # Maksimum 5 bağlantı kuyruğu

# --- 4. ARAYÜZ (HTML/JS/CSS) ---
# Not: HTML içeriği main.py dosyasında h1, h2, h3, h4 değişkenlerinde tutulmaktadır.
# (Burada kodun uzunluğunu korumak için HTML değişkenleri aynen bırakılmıştır)

# --- 5. ANA SUNUCU DÖNGÜSÜ ---
print("Sistem Hazır. İstemci bekleniyor...")
gc.collect()

while True:
    try:
        # İstemci bağlantısını kabul et
        conn, addr = s.accept()
        conn.settimeout(3.0) 
        try:
            # Gelen HTTP isteğini al
            req = str(conn.recv(1024))
            
            # API: Sensör verisi isteği (Oyun döngüsü buradan beslenir)
            if 'GET /data' in req:
                d = get_data(i2c)
                conn.send(b'HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n')
                conn.send(ujson.dumps(d).encode())
            
            # UI: Ana sayfa isteği (Oyun arayüzünü yükler)
            elif 'GET / ' in req:
                conn.send(b'HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')
                # HTML parçalarını sırayla gönder
                conn.sendall(h1.encode())
                conn.sendall(h2.encode())
                conn.sendall(h3.encode())
                conn.sendall(h4.encode())
                
            gc.collect() # Her işlemden sonra belleği temizle
        except OSError:
            pass 
        conn.close() # Bağlantıyı kapat
    except Exception as e:
        print("Kritik Hata:", e)
