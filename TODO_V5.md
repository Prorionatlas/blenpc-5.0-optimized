# BlenPC v5.0 - Geliştirme Yol Haritası (TODO List)

## Sprint 0: Altyapı Hazırlığı (Phase 0)
- [ ] `config.py` güncelleme: `USE_NEW_GEOMETRY` bayrağı ekle.
- [ ] `engine.py` güncelleme: Eski ve yeni pipeline arasında seçim yapacak mantığı ekle.
- [ ] Loglama: `USE_NEW_GEOMETRY=False` durumunda uyarı mesajı ekle.

## Sprint 1: Otorite Katmanları (Phase 1)
- [ ] `geometry_authority.py` oluştur: `quantize()`, `quantize_room()` fonksiyonları.
- [ ] `vertical_authority.py` oluştur: `FloorElevations` dataclass ve `floor_elevations()` fonksiyonu.
- [ ] `validator.py` oluştur: `ValidationResult` ve `validate_mesh()` iskeleti.

## Sprint 2: Geometri Motoru (Phase 2-3)
- [ ] `geometry_authority.py`: `robust_union()` implementasyonu ve buffer fallback.
- [ ] `edge_classifier.py` oluştur: `EdgeType`, `ClassifiedEdge` ve `classify_edges()`.
- [ ] `canonical_edge()` fonksiyonu ile duplicate edge temizliği.

## Sprint 3: Mesh Üretimi (Phase 4)
- [ ] `walls.py`: Strip tabanlı wall builder (`build_wall_strip`).
- [ ] `inward_normal()` fonksiyonu: Centroid dot product ile normal yönü doğrulama.
- [ ] Tek taraflı (dış) ve simetrik (iç) duvar kalınlık yönetimi.

## Sprint 4: Pipeline Entegrasyonu (Phase 5)
- [ ] `engine.py`: Tüm katmanları (`quantize` -> `union` -> `classify` -> `build` -> `validate`) birleştir.
- [ ] `generation_gate()`: Validation başarısız olursa exception fırlat.
- [ ] GLB Export entegrasyonu.

## Sprint 5: Optimizasyon ve Temizlik (Phase 6)
- [ ] Eski `box builder` mantığını `@deprecated` olarak işaretle.
- [ ] Mesh cleanup işlemlerini minimalize et (geometri artık temiz üretilmeli).
- [ ] Performans benchmarkı ve final testler.
