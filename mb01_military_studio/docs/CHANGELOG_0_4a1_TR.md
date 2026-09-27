# MB01 0.4 alpha.1 Changelog

- Glonorce Blender MCP için `agent_api.py`: `create_hq`, `rebuild`, `audit`, `prepare_review`, `export_game_ready`.
- Yeni MB01 paneli: **AI / Glonorce MCP / Game-Ready**.
- HQ tasarım dilleri: `EXECUTIVE`, `TECHNICAL`, `MONOLITHIC`.
- Parametrik `facade_relief`, `vertical_fins`, `atrium_floors`, `base_cladding`, `micro_details`, `night_lighting`.
- Karargâhta yeni portal kanatları/crown, spandrel gölge bantları, dikey fins, alt cephe cladding, roof-screen detayları, expansion-joint ve HERO micro-detail katmanı.
- PBR shader: ORM AO entegrasyonu + Height/Bump + NormalGL zinciri; yeni `ConcreteDark` semantiği; daha kuvvetli cam transmission.
- Cycles preview: daha yüksek sample profili, Nishita Sky + AgX sunum ayarı.
- Whole-building **Classic LOD0/1/2** ve **Nanite Hero** merged FBX/PBR bundle exporter eklendi.
- Whole-building read-only game-ready audit: evaluated triangles, UV0, negative scale, collision metadata, materials ve mevcut mesh QA.
- Export manifest `mb01.scene/0.2`: MCP agent API, PBR workflow ve render profile metadata.
- Saf Python regresyonu: HQ 3 varyant × 3 detail + diğer 4 aile PASS; mevcut 6 modül LOD0/1/2 compiler PASS.

## Bilinen sınırlar
Blender-native, Glonorce MCP-native ve Unreal runtime testleri paketleme ortamında çalıştırılmadı; hedef makinede doğrulanmalıdır.
