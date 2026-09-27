# MB01 0.3.0-alpha.1 — değişiklik kaydı

## Eklemeler
- Altı gerçek hangar modülü, on cephe token'ı, beş yeni tam önayar; aile filtreleri korunur.
- Tek cephe hücresini panelden değiştirme; mevcut binayı otomatik değiştirmez.
- Küçük modül derleyicisi: opak/cam/kapı ayrımı, LOD0/1/2, sabit slot/pivot/socket, kapalı rest pose.
- Basit duvar collision parçaları; nominal açıklık hacmine pozitif kesişim testi; ayrı kapı hull'u.
- Ayrı LOD FBX exporter kodu; `GAME_KIT.json`, PBR kaynak hash'leri ve tamamlanmamış export işareti.
- Native Blender test aracı, tekrar üretilebilir gerçek renderlar ve gelişim planı.

## Uyarlamalar
- İki delikli panel için validator artık her deliğin gerçek merkezini kullanıyor; x=0 varsayımı kaldırıldı.
- Giriş kuralları/sahanlık/kapı metadatası yeni çift servis ve canopy girişlerini tanıyor.
- Eski alpha.2/alpha.3 Hangar JSON'ları kabul ediliyor; yeni şema 0.3-alpha.1.
- Katalog 56→62 ve uygulanmış kaynak modülü 14→20 oldu. Eski testlerde yalnız bu sabit adet beklentileri ve 3→8 preset beklentisi güncellendi; eski test dosyaları `reference` altında saklandı. Geometri doğrulama hatalarını gizlemek için test silinmedi.
- Eski native smoke testinin üç varsayılan hangar kapsamı, açık üçlü liste olarak sabitlendi; yeni kapsam ayrı EXPANSION smoke içinde.

## Korunanlar / kapsam dışı
- AS07 orijinali, beş eski bina ve üç eski Hangar Studio geometrisi; diğer kit ZIP'leri değişmedi.
- 40 prosedürel PNG ve materyal kurucusu aynen korundu; yeni tarama/trim bake yok.
- Yeni büyük kapı veya çatı türü, tam bina LOD, otomatik UE LOD bağlayıcı/Nanite/HISM, artımlı sahne güncelleme ve sertifikasyon eklenmedi.
- Native Blender ve Unreal testi yapılmadı. Saf test adedi bu kapıların yerine geçmez.
