# MB01 0.3 alpha.2 – Bina Tasarım İyileştirmesi

## Amaç
HQ, birlik, destek ve lojistik yapılarını daha gelişmiş, daha okunur ve oyun motoruna daha uygun bir mimari dille güncellemek.

## Eklenen Parametreler
- `office_style`: `AUTO`, `COMMAND`, `BARRACKS`, `SUPPORT`, `LOGISTICS`
- `service_bays`: servis/lojistik kapı adedi (0–5)
- `stair_tower`: harici merdiven kulesi
- `roof_screen`: çatı ekipman perdesi
- `corner_glass`: komuta binası için köşe cam vurgusu

## Görsel / Geometrik İyileştirmeler
1. **Command HQ**
   - daha güçlü merkezi cam giriş
   - dikey vurgu pilasterleri
   - opsiyonel köşe cam detayları
   - çatı ekipmanı için ekran/perde
2. **Barracks / Birlik**
   - daha kompakt giriş dili
   - harici merdiven kulesi
   - tekrarlı oda ritmi ve düz askeri cephe
3. **Support / Destek**
   - idari kütle + servis kanadı birleşimi
   - roll-up kapılar ve servis saçağı
   - güvenlik babaları ve ekipman avlusu
4. **Logistics / Eğitim**
   - daha geniş servis bölgesi
   - lojistik cephesi ve servis avlusu
   - aynı çekirdekten farklı oyun içi varyasyon üretimi

## Oyun / Game-Ready Tarafı
- mevcut PBR malzeme grupları korunur
- geometri yine parametriktir
- bağımsız GLB örnekleri üretildi
- Blender dışı saf Python testleri geçirildi

## Not
Bu üretici hâlâ kurgu/CGI mimari varlık üretir; gerçek askerî tesis inşaatı, emniyet onayı veya standart sertifikasyonu iddia etmez.
