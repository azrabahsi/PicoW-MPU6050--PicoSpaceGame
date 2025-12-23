import network
import socket
from machine import Pin, I2C
import utime
import math
import ujson
import gc

# Hafizayi temizle
gc.collect()

# --- 1. AYARLAR ---
ssid = ''
password = ''

# --- 2. SENSOR ---
def init_mpu6050(i2c):
    try:
        i2c.writeto_mem(0x68, 0x6B, b'\x00')
        utime.sleep_ms(100)
        i2c.writeto_mem(0x68, 0x19, b'\x07')
        i2c.writeto_mem(0x68, 0x1A, b'\x03') 
    except: pass

def read_raw(i2c, addr):
    try:
        h = i2c.readfrom_mem(0x68, addr, 1)[0]
        l = i2c.readfrom_mem(0x68, addr+1, 1)[0]
        v = h<<8|l
        if v>32768: v-=65536
        return v
    except: return 0

yaw_z = 0.0
last_time = utime.ticks_ms()

def get_data(i2c):
    global yaw_z, last_time
    ax = read_raw(i2c, 0x3B)/16384.0
    ay = read_raw(i2c, 0x3D)/16384.0
    az = read_raw(i2c, 0x3F)/16384.0
    try:
        ang_x = math.atan2(ay, math.sqrt(ax*ax+az*az))*57.3
        ang_y = math.atan2(-ax, math.sqrt(ay*ay+az*az))*57.3
    except: ang_x=0; ang_y=0
    
    ct = utime.ticks_ms()
    dt = (ct-last_time)/1000.0
    last_time = ct
    
    gz = read_raw(i2c, 0x47)/131.0
    if abs(gz)<1: gz=0
    yaw_z += gz*dt
    return {'x':int(ang_x),'y':int(ang_y),'z':int(yaw_z)}

# --- 3. BAGLANTI ---
print("Sistem Baslatiliyor...")
i2c = I2C(0, scl=Pin(21), sda=Pin(20), freq=400000)
init_mpu6050(i2c)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

wait=20
while wait>0 and wlan.status()!=3:
    wait-=1
    utime.sleep(1)

if wlan.status()==3:
    print(f'BAGLANDI: http://{wlan.ifconfig()[0]}')
else:
    print("Wifi Hatasi!")

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try: s.bind(('', 80))
except: pass
s.listen(5)

# --- 4. HTML PARCALARI (KADEMELI HIZ ARTIS SISTEMI) ---

# Parca 1: CSS
h1 = """<!DOCTYPE html><html><head><title>PicoSpace V22</title><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap" rel="stylesheet">
<style>
body{margin:0;overflow:hidden;background:#000;color:#fff;font-family:'Orbitron',sans-serif}
.ui{position:absolute;top:20px;left:20px;z-index:5;display:none;background:rgba(0,10,30,0.6);backdrop-filter:blur(4px);padding:15px;border:1px solid #0ff;border-radius:15px;box-shadow:0 0 10px #0ff}
.ui div{font-size:16px;margin-bottom:5px;text-shadow:0 0 5px #0ff}.ui span{color:#0ff;font-size:22px}
.ov{position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);z-index:10;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.card{background:rgba(255,255,255,0.05);backdrop-filter:blur(15px);padding:40px 60px;border-radius:30px;border:1px solid rgba(255,255,255,0.1);box-shadow:0 0 50px rgba(0,255,255,0.2)}
h1.title{font-size:60px;margin:0 0 20px 0;color:#fff;text-shadow:0 0 20px #00ffff, 0 0 40px #0000ff;letter-spacing:4px}
@keyframes pulse { 0% {transform:scale(1);box-shadow:0 0 20px #00aaff;} 50% {transform:scale(1.05);box-shadow:0 0 40px #00aaff;} 100% {transform:scale(1);box-shadow:0 0 20px #00aaff;} }
button.start-btn{padding:15px 50px;font-size:28px;font-family:'Orbitron';font-weight:bold;color:#fff;background:linear-gradient(45deg, #00c6ff, #0072ff);border:none;border-radius:50px;cursor:pointer;animation:pulse 2s infinite;text-transform:uppercase;letter-spacing:2px}
button.start-btn:active{transform:scale(0.95);animation:none}
#nt{position:absolute;top:40%;left:50%;transform:translate(-50%,-50%);font-size:40px;color:#ff0;display:none;z-index:8;text-shadow:0 0 20px gold}
#pop{position:absolute;top:30%;left:50%;transform:translate(-50%,-50%);font-size:60px;color:#0f0;font-weight:bold;display:none;z-index:9;text-shadow:0 0 20px #0f0}
#hint{position:absolute;top:10%;width:100%;text-align:center;display:none;z-index:7}
.hint-box{background:rgba(0,255,0,0.15);border:1px solid #0f0;color:#0f0;padding:10px 30px;border-radius:20px;display:inline-block;font-size:20px;text-shadow:0 0 10px #0f0;backdrop-filter:blur(5px)}
</style>
<script>
function err(){ alert("GRAFIK MOTORU YUKLENEMEDI! Internet baglantisini kontrol et."); }
function go(){ 
    document.getElementById('st').style.display='none'; 
    document.getElementById('ui').style.display='block'; 
    var h = document.getElementById('hint'); h.style.display='block';
    setTimeout(function(){ h.style.display='none'; }, 4000);
    window.act=true; 
    if(window.up)window.up(0); 
}
</script>
"""

# Parca 2: HTML Govde
h2 = """<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js" onerror="err()"></script>
</head><body>
<div id="ui" class="ui"><div>LEVEL: <span id="lv">1</span></div><div>SKOR: <span id="sc">0</span></div></div>
<div id="nt">LEVEL UP!</div>
<div id="pop">+50</div>
<div id="hint"><div class="hint-box">IPUCU: YESIL KRISTAL = +50 PUAN</div></div>

<div id="st" class="ov">
    <div class="card">
        <h1 class="title">PICO UZAY</h1>
        <button class="start-btn" onclick="go()">BASLAT</button>
        <div style="margin-top:20px;color:#aaa;font-size:14px">V22.0 - PROGRESSIVE</div>
    </div>
</div>

<div id="go" class="ov" style="display:none">
    <div class="card" style="border-color:#f00;box-shadow:0 0 50px rgba(255,0,0,0.3)">
        <h1 class="title" style="color:#f00;text-shadow:0 0 20px red">OYUN BITTI</h1>
        <p style="font-size:24px;margin:20px">SKOR: <span id="es" style="color:#ff0">0</span></p>
        <button class="start-btn" style="background:linear-gradient(45deg,#f00,#900);animation:none" onclick="location.reload()">TEKRAR OYNA</button>
    </div>
</div>

<script>
if(!window.THREE) err();
var act=false;
// BASLANGIC HIZI: 0.12 (Yavas)
let sc=0,lv=1,sp=0.12,lst=0,tx=0,ty=0,cx=0,cy=0;
const C=[{c:0x050510,n:"DERIN UZAY"},{c:0x300000,n:"KIZIL BOLGE"},{c:0x002000,n:"ZEHIRLI GAZ"},{c:0x200030,n:"MOR NEBULA"},{c:0x001030,n:"BUZUL"}];
const scn=new THREE.Scene();scn.fog=new THREE.FogExp2(C[0].c,0.04);scn.background=new THREE.Color(C[0].c);
const cam=new THREE.PerspectiveCamera(70,innerWidth/innerHeight,0.1,100);cam.position.set(0,2,8);cam.rotation.x=-0.1;
const ren=new THREE.WebGLRenderer({antialias:true});ren.setSize(innerWidth,innerHeight);document.body.appendChild(ren.domElement);
scn.add(new THREE.AmbientLight(0x666666));const l=new THREE.PointLight(0xffffff,1);l.position.set(5,5,5);scn.add(l);
</script>
"""

# Parca 3: Gemi ve Objeler
h3 = """<script>
const shp=new THREE.Group();
const b=new THREE.Mesh(new THREE.ConeGeometry(0.4,2,8),new THREE.MeshPhongMaterial({color:0xdddddd})); b.rotation.x=1.57; shp.add(b);
const w=new THREE.Mesh(new THREE.BoxGeometry(2.4,0.1,0.6),new THREE.MeshPhongMaterial({color:0xff3300})); w.position.z=0.3; shp.add(w);
const e=new THREE.Mesh(new THREE.CylinderGeometry(0.2,0.1,0.3,8),new THREE.MeshBasicMaterial({color:0xffaa00})); e.rotation.x=1.57; e.position.z=1.1; shp.add(e);
scn.add(shp);
const sg=new THREE.BufferGeometry(),spos=[];for(let i=0;i<3000;i++)spos.push((Math.random()-0.5)*150);
sg.setAttribute('position',new THREE.Float32BufferAttribute(spos,3));
const strs=new THREE.Points(sg,new THREE.PointsMaterial({color:0xffffff,size:0.15}));scn.add(strs);
const G=[new THREE.IcosahedronGeometry(0.7),new THREE.BoxGeometry(1,1,1),new THREE.OctahedronGeometry(0.7),new THREE.TorusGeometry(0.6,0.2,8,12)];
const M=[new THREE.MeshLambertMaterial({color:0xccaa00}),new THREE.MeshPhongMaterial({color:0x00ffff}),new THREE.MeshPhongMaterial({color:0xff00aa}),new THREE.MeshLambertMaterial({color:0xff6600})];
const bG = new THREE.OctahedronGeometry(0.5); const bM = new THREE.MeshBasicMaterial({color:0x00ff00});
let ens=[], bons=[];
</script>
"""

# Parca 4: Oyun Dongusu (KADEMELI HIZ ARTIS SISTEMI)
h4 = """<script>
window.up = function(i){
    let c=C[i%C.length]; scn.background.setHex(c.c);scn.fog.color.setHex(c.c);
    let n=document.getElementById('nt');n.innerHTML="LEVEL "+lv+"<br><span style='font-size:25px;color:#fff'>"+c.n+"</span>";n.style.display='block';
    setTimeout(()=>{n.style.display='none'},2000);
}
function showPop(){
    let p=document.getElementById('pop'); p.style.display='block';
    setTimeout(()=>{p.style.display='none'}, 800);
}
setInterval(async()=>{if(!act)return;try{let r=await fetch('/data');let d=await r.json();tx=d.y/3.5;ty=-d.x/3.5;}catch(e){}},50);

// --- OYUN DONGUSU ---
function anim(t){requestAnimationFrame(anim);
const p=strs.geometry.attributes.position.array;for(let i=2;i<p.length;i+=3){p[i]+=sp*4;if(p[i]>20)p[i]=-100;}strs.geometry.attributes.position.needsUpdate=true;

if(act){
    cx+=(tx-cx)*0.1;cy+=(ty-cy)*0.1;cx=Math.max(-10,Math.min(10,cx));cy=Math.max(-6,Math.min(6,cy));
    shp.position.set(cx,cy,0);shp.rotation.z=-cx*0.1;shp.rotation.x=cy*0.05;
    
    /* 1. ZORLUK AYARI: SPAWN SIKLIGI */
    /* Level arttikca 1600ms'den baslayip azalir. Daha sik obje gelir. */
    let spawnRate = Math.max(400, 1600 - (lv * 110));
    
    if(t-lst > spawnRate){
        let idx=Math.min(lv-1,3); if(Math.random()>0.7)idx=Math.floor(Math.random()*(idx+1));
        let e=new THREE.Mesh(G[idx],M[idx]); e.position.set((Math.random()-0.5)*20,(Math.random()-0.5)*12,-70);scn.add(e);ens.push(e);
        if(Math.random()>0.75){let bo=new THREE.Mesh(bG,bM);bo.position.set((Math.random()-0.5)*18,(Math.random()-0.5)*10,-75);scn.add(bo);bons.push(bo);}
        lst=t;
    }
    
    /* 2. HIZ AYARI: OBJELERIN HAREKETI */
    /* Artik sabit sayi eklemiyoruz, direkt 'sp' degiskeni hizi belirliyor. */
    
    // -- YESIL KRISTALLER --
    for(let i=bons.length-1;i>=0;i--){
        let b=bons[i]; 
        b.position.z += sp; // HIZ BURADAN GELIYOR
        b.rotation.y+=0.1; 
        
        if(b.position.z>-1 && b.position.z<1 && shp.position.distanceTo(b.position)<1.6){
            scn.remove(b);bons.splice(i,1);sc+=50;document.getElementById('sc').innerText=sc; showPop(); 
            
            // LEVEL ATLAMASI (BONUS ILE)
            if(sc%150<50 && sc>150){
                lv=Math.floor(sc/150)+1;
                /* YENI HIZ FORMULU: 0.12 + (Level * 0.03) */
                sp = 0.12 + (lv * 0.03); 
                document.getElementById('lv').innerText=lv;up(lv-1);
            }
        } else if(b.position.z>8){scn.remove(b);bons.splice(i,1);}
    }
    
    // -- DUSMANLAR --
    for(let i=ens.length-1;i>=0;i--){
        let e=ens[i];
        e.position.z += sp; // HIZ BURADAN GELIYOR
        e.rotation.x+=0.04; 
        
        if(e.position.z>-1&&e.position.z<1&&shp.position.distanceTo(e.position)<1.6){
            act=false;document.getElementById('es').innerText=sc;document.getElementById('ui').style.display='none';document.getElementById('go').style.display='flex';
        } 
        if(e.position.z>8){
            scn.remove(e);ens.splice(i,1);sc+=10;document.getElementById('sc').innerText=sc;
            
            // LEVEL ATLAMASI (SKOR ILE)
            if(sc%150==0){
                lv++;
                /* YENI HIZ FORMULU: Ayni sekilde artar */
                sp = 0.12 + (lv * 0.03);
                document.getElementById('lv').innerText=lv;up(lv-1);
            }
        }
    }
} ren.render(scn,cam);} anim(0); window.onresize=()=>{cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix();ren.setSize(innerWidth,innerHeight)};
</script></body></html>
"""

# --- 5. SUNUCU DONGUSU ---
print("Sunucu Hazir. Istek bekleniyor...")
gc.collect()

while True:
    try:
        conn, addr = s.accept()
        conn.settimeout(3.0) 
        try:
            req = str(conn.recv(1024))
            
            if 'GET /data' in req:
                d = get_data(i2c)
                conn.send(b'HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n')
                conn.send(ujson.dumps(d).encode())
            
            elif 'GET / ' in req:
                conn.send(b'HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')
                conn.sendall(h1.encode())
                conn.sendall(h2.encode())
                conn.sendall(h3.encode())
                conn.sendall(h4.encode())
                
            gc.collect()
        except OSError as e:
            pass 
        conn.close()
    except Exception as e:
        print("Hata:", e)