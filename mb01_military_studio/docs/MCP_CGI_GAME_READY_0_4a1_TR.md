# MB01 0.4 alpha.1 — Glonorce Blender MCP + CGI/PBR/Game-Ready yükseltmesi

## Hedef
Bu sürüm, önceki MB01 0.3 alpha.2 bina üreticisini bir **AI denetimli asset üretim sistemi** haline getirir. Glonorce Blender MCP'nin `execute_blender_code`, `get_scene_graph` ve çoklu viewport screenshot akışlarıyla kullanılmak üzere yüksek seviyeli `agent_api` eklenmiştir.

## Karargâh / HQ yükseltmesi
- `EXECUTIVE`, `TECHNICAL`, `MONOLITHIC` komuta binası tasarım dili.
- Parametrik cephe relief'i, dikey fins, atrium kat yüksekliği.
- Taş/beton alt cephe bandı, spandrel gölge bantları, expansion-joint/mikro detay, portal kütlesi, çatı ekran konstrüksiyonu.
- HERO seviyesinde kontrollü yakın-plan detay; DRAFT/WORKING seviyeleri daha hafiftir.
- Mevcut cam giriş, köşe camı, pencere açıklıkları, servis ekipmanı, kapı ve port metadata sistemi korunur.

## PBR shader yükseltmesi
- BaseColor + renk tint + vertex tint.
- ORM'nin **R/AO** kanalı BaseColor'a çarpılır; **G/Roughness** roughness zincirine gider.
- NormalGL → Normal Map; Height → Bump; ikisi birlikte Principled BSDF normaline bağlanır.
- Glass transmission artırılmıştır. Harici PBR klasörü ve source hash kontrolleri korunur.
- `ConcreteDark` semantik materyali eklendi.

## Whole-building game-ready export
- **Classic LOD bundle:** LOD0/HERO, LOD1/WORKING semantik sadeleştirme, LOD2 ana mimari gruplar.
- **Nanite Hero bundle:** tek yüksek detaylı merged static mesh + PBR manifest; Nanite hedef Unreal projesinde kullanıcı tarafından açılır.
- Mimari açıklıkları kapatabilecek kaba UCX otomatik üretilmez; collision politikası manifestte açıkça proje-kontrollüdür.
- LOD bundle manuel kilitli sahne objelerini değil, parametrik config’den yeniden üretilmiş kanonik asseti kullanır.

## Game-ready QA
Yeni `game_ready.audit.audit_building()`:
- evaluated triangle toplamı
- UV0_Tile varlığı
- negatif scale
- material slots
- collision policy metadata
- mevcut native mesh QA sonuçları
- proje tarafında native Unreal doğrulaması gerekliliği

Panel: **MB01 > AI / Glonorce MCP / Game-Ready**.

## Glonorce MCP kullanımı
MCP üzerinden örnek yüksek seviye çağrı:

```python
from mb01_military_studio import agent_api
result = agent_api.create_hq({
    "name": "KARARGAH_HERO_01",
    "width": 38.0,
    "depth": 22.0,
    "floors": 3,
    "detail": "HERO",
    "command_variant": "TECHNICAL",
    "facade_relief": 0.72,
    "vertical_fins": 8,
    "corner_glass": True,
    "wear": 0.12,
})
print(result)
```

Sonra Glonorce tarafında önerilen kapı:
1. `get_viewport_screenshot_base64`: `MULTI`, `MATERIAL`.
2. Silhouette, giriş hiyerarşisi, cephe relief'i, repetition, materyal ölçeği, çatı yoğunluğu incelenir.
3. `get_scene_graph`: `CHECK_PRODUCTION_READINESS`.
4. `get_scene_graph`: `DETECT_GEOMETRY_ERRORS` ve gerekirse `ANALYZE_ASSEMBLY`.
5. Düzeltme `agent_api.rebuild(root_name, patch)` ile yapılır.
6. Screenshot + QA tekrarlanır; tek üretim sonucu otomatik olarak “final” kabul edilmez.
7. Kabul sonrası `agent_api.export_building_lods(..., mode='CLASSIC_LOD')` veya `NANITE_HERO` ile merged bina bundle üretilebilir.

## Güvenli kapsam
Bu, kurgusal/CGI mimari ve oyun asset üreticisidir. Gerçek tesis güvenlik planı, inşaat/taşıyıcı hesap, balistik veya saha operasyon standardı üretmez.

## Test durumu
- Saf Python kaynak/geometry testleri paketlenmeden önce çalıştırılır.
- Blender-native ve MCP-native işlevler Blender içinde doğrulanmalıdır; paket üretim ortamı Blender çalıştırmıyorsa bu iddia edilmez.
- Unreal import/runtime testi hedef projede yapılmalıdır.
