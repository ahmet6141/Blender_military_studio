# Hangar Studio — mimari ve bileşen kataloğu
## 1. Dosya sınırları

```text
mb01_military_studio/
  core.py                    # Önceki beş bina ailesi; değiştirilmedi
  materials.py               # Önceki materyal kurucu; değiştirilmedi
  modular/                   # Önceki 14 parça ve cephe sırası; korundu
  vendor/as07_reference.py    # Kullanıcının özgün kaynağı; byte düzeyinde korundu
  hangar_studio/
    contracts.py             # Strict config, üç önayar, JSON, kapı hareketi
    geometry.py              # Yapı, kabuk, çatı, kapı, zemin ve bağlantılar
    style.py                 # Ayrı HG_* malzeme rolleri
    blender_tools.py         # Blender mesh/material/pose/staging adaptörü
    ui.py                    # Yedi kategorili panel, operatörler
```

Önceki __init__, ui, blender_backend ve exporter'a yalnız kayıt/ayırma/aktarımı tanıtan köprüler eklenir. Yeni Hangar Studio için eski HANGAR geometri yolu çağrılmaz. Bütün 56 katalog kaydı tamamlanmış gibi işaretlenmez.

## 2. Üretilen bileşen kategorileri

| Kategori | Mevcut geometri | Ayrı tek parça UI durumu |
|---|---|---|
| Taşıyıcı görünüşü | I-kesit portal, ayak plakası, mahya birleştirme, seçili civata, aşık, opak hücre çaprazı | Hangar kurulumu içinde |
| Yan kabuk | METAL, CLERESTORY, LOUVER, PERSONNEL | Önceki modüler tarayıcıda da var |
| Ön/arka kabuk | Kapı yan cepleri, ön başlık, gable kapamalar, arka hücreler, köşe kapakları | Hangar kurulumu içinde |
| Çatı | Bölmeli metal kaplama, kenetler, mahya veya gerçek monitor boşluğu, küçük üst çatı | Hangar kurulumu içinde |
| Cam/ışıklık | Üst bant cam, monitor yan cam ve çerçeveler, ana kapı cam bandı | Yapı parametresi |
| Ana kapı | 4/6/8 teleskopik kanat, C-ray, makaralar, üst saçak ve alt yüzeyi, sığ kılavuz | Yapı parametresi + pose |
| Personel | Kapılar, sahanlıklar, açıklık/yaya portları | Yapı parametresi + pose |
| Zemin | Beton plaklar, alt derz yatağı, drenaj kesisi, kanal/ızgara ve çizgiler | Yerel/dış sahiplik |
| Servis | Oluk/iniş/kelepçe, kablo tavası, kanallar, opak hücre servis kutusu | Aç/kapat |
| Işık/kimlik | Askılı armatür, difüzör, askı/bağlantı ve numara paneli | Geometri; gerçek ışık ayrıca preview |

## 3. Koordinat ve isim sözleşmesi

Kaynak hesap: X en, Y derinlik, Z yukarı. Teslim: +X bina içine, +Y sol, +Z yukarı; dönüşüm `(x,y,z) → (y,-x,z)` bir kez uygulanır. `*_design` isimli metadata özellikle kaynak koordinatlarını taşır. Export dünya matrislerini ve hedef kalibrasyon tabanını kullanır.

UV0_Tile ve SW01_Tint korunur. Tint nötr beyazdır; ıslaklık maskesi diye bu kanalın anlamı değiştirilmez. Islaklık ayrı açık/kapalı beton tarifleriyle çözülür.

Katmanlar: STRUCTURE, BODY, ROOF, FACADE, GLASS, DOOR, GROUND, MARKINGS, DETAIL, SIGNAGE, PORTS. Kimlikler açıklayıcı ve stabil parça semantiği taşır. Her yeni üretim ayrı owner UUID alır; export edilmiş yeni revizyonun eski projeyi kendiliğinden üzerine yazması beklenmez.

## 4. Geometri ve kalite kararları

Modüller doğrudan önceki dört hangar üreticisini çağırır, geometri üzerinde sonradan non-uniform scale yapmaz. Boyuna cell genişliği parametre olarak verilir. Kapı/pencere açıklıkları kabukta vardır; dekor olarak düz duvar üstüne çizilmez.

Monitor boşluğunda ana çatı yüzeyi yoktur. Altındaki portal kirişleri görünmeye devam edebilir; bu bir çatı penceresinin her taşıyıcının da kaldırılması anlamına gelmez. Çelik profil kesitleri sanatçı ölçüleridir.

Çatı UV'si boyuna ve eğimli yüzey boyuna göre kesintisizdir. Modül başında doku fazı sıfırlanmaz. Uç kapaklar ayrı düzlem UV'si kullanır. Negatif determinantlı yansıtma, yazı/normal yönünü sessizce ters çevirmek için kullanılmaz.

Gate rest geometri, pozdan bağımsızdır. Kapı açık oranı geometriyi yeniden yazmaz; yerel pivot/konum üzerinden uygulanır. Personel menteşesi ile ana kapı kayması farklı kanallardır. Kinematik görünüm, fiziksel mekanizma simülasyonu değildir.

Drenaj kesisi basit dikdörtgen çıkarımıyla hesaplanır; genel Boolean çözücü vaadi yoktur. Dış apron seçildiğinde yalnız oyuk talebi kaydı tutulur, mevcut AF01 mesh'i yerinde değiştirilmez.

## 5. Gelecek kapsam — bu teslimde yok

Tam modüler çoklu hangar bloğu, yay üzerinde yerleşim, kiriş yük hesabı, gerçek havalandırma/yangın tesisatı, ek oda planları, vinç hesapları, hava aracı süpürme emniyeti, otomatik SW01/PK01 bağlama, UE runtime parametrik üretim, Blueprint kapı motoru, bake atlası/LOD/HISM ve doğrulanmış askerî standart profili.

Sonraki işin önceliği yeni bina adedi değil; bu tam hangarın gerçek Blender/UE üretim/aktarım raporu, native malzeme ve hareketli kamera incelemesidir.
