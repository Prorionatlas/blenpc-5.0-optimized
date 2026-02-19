# BlenPC v5.0 - Geliştirme Yol Haritası (TODO List)

## Sprint 0: Altyapı Hazırlığı (Phase 0)
- [x] `config.py` güncelleme: `USE_NEW_GEOMETRY` bayrağı ekle.
- [x] `engine.py` güncelleme: Eski ve yeni pipeline arasında seçim yapacak mantığı ekle.
- [x] Loglama: `USE_NEW_GEOMETRY=False` durumunda uyarı mesajı ekle.

## Sprint 1: Otorite Katmanları (Phase 1)
- [x] `geometry_authority.py` oluştur: `quantize()`, `quantize_room()` fonksiyonları.
- [x] `vertical_authority.py` oluştur: `FloorElevations` dataclass ve `floor_elevations()` fonksiyonu.
- [x] `validator.py` oluştur: `ValidationResult` ve `validate_mesh()` iskeleti.

## Sprint 2: Geometri Motoru (Phase 2-3)
- [x] `geometry_authority.py`: `robust_union()` implementasyonu ve buffer fallback.
- [x] `edge_classifier.py` oluştur: `EdgeType`, `ClassifiedEdge` ve `classify_edges()`.
- [x] `canonical_edge()` fonksiyonu ile duplicate edge temizliği.

## Sprint 3: Mesh Üretimi (Phase 4)
- [x] `walls.py`: Strip tabanlı wall builder (`build_wall_strip`).
- [x] `inward_normal()` fonksiyonu: Centroid dot product ile normal yönü doğrulama.
- [x] Tek taraflı (dış) ve simetrik (iç) duvar kalınlık yönetimi.

## Sprint 4: Pipeline Entegrasyonu (Phase 5)
- [x] `engine.py`: Tüm katmanları (`quantize` -> `union` -> `classify` -> `build` -> `validate`) birleştir.
- [x] `generation_gate()`: Validation başarısız olursa exception fırlat.
- [x] GLB Export entegrasyonu.

## Sprint 5: Optimizasyon ve Temizlik (Phase 6)
- [x] Eski `box builder` mantığını `@deprecated` olarak işaretle.
- [x] Mesh cleanup işlemlerini minimalize et (geometri artık temiz üretilmeli).
- [x] Mimari düzeltmeler ve Mantık hatalarının giderilmesi.
- [x] Kapsamlı test süiti oluşturulması (`tests/test_v5_*.py`).
- [x] Performans benchmarkı ve v5.2.0 Core testleri.

## Sprint 6: Integer Grid & Collision Engine (v5.2.0)
- [x] `MICRO_UNIT` (0.025m) tam sayı grid sisteminin kurulması.
- [x] `geometry_authority.py` güncellemesi: Float drift hatalarının önlenmesi.
- [x] `collision_engine.py`: Uzamsal çakışma kontrol motoru.
- [x] `engine.py` entegrasyonu: Üretim öncesi çakışma validasyonu.
- [x] v5.2.0 test süiti (`tests/test_v5_2_core.py`) ve GEOS hatalarının giderilmesi.
