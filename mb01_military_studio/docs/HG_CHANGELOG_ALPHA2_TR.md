# 0.2.0-alpha.2 değişiklik kaydı

## Eklenenler
- Mevcut dört modüler hangar yan panelinden tam kapalı hangar kurucusu.
- Üç mimari önayar, iki çatı tipi ve gerçek monitor açıklığı.
- 4/6/8 kanatlı karşılıklı teleskopik kapı, ayrı raylar/kanat pivotları.
- Gerçek slab/alt yatak drenaj kesimi, kolon/ışıklık/çatı detayları ve sahanlıklar.
- Yeni fakat eski materyalleri değiştirmeyen HG_* yüzey rolleri.
- Ayrı açık apron/kapalı döşeme roughness-albedo görünümü.
- Strict JSON, kategorize Blender paneli, yeni revizyon üretimi ve poz kontrolü.
- Mevcut exporter'a hangar tarifini tanıyan ek; runtime animasyon değil.
- 86 yeni Python testi; 24 ilave geometri konfigürasyonu; 9 render incelemesi.
- Kullanıcı bilgisayarında koşacak ayrı native Blender test aracı.

## Korunanlar
- AS07 özgün kaynak dosyası, 0.1 bina çekirdeği, orijinal materyal kurucu ve alpha.1 modüler geometri.
- Önceki beş bina ailesi ve 14 parçalık cephe laboratuvarı.
- 40 orijinal prosedürel PNG ve lisans bildirimleri.

## Güncellenen köprüler
- Eklenti register/unregister sırasında Hangar Studio modülü kaydı.
- Eski bina üreticisinin yeni hangar/modüler kök üzerinde yanlışlıkla çalışmasını önleyen kontrol.
- Exporter'da hangar tarifi/malzeme/kapı metadata seçimi.

## Hâlâ eksik
Native Blender/UE doğrulaması; canlı UE parametrik üretim; gerçek mühendislik/standart onayı; artımlı yerinde yeniden üretim; otomatik geniş yerleşke bağlantısı; fotogrametri indirme paketi; otomatik LOD/Nanite/HISM, lightmap ve runtime Blueprint.
