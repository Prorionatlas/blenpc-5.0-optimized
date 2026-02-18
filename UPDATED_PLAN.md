# BlenPC 5.0 - Güncellenmiş Geliştirme Planı (7 Uzman Panel Kararları)

## Güncelleme Özeti

Yeni uzman panel toplantısı sonucu **kritik mimari kararlar** alındı. Overengineering yerine **mühendislik** odaklı, kademeli geçiş stratejisi benimsendi.

---

## Uzman Panel Kararları

### ✅ KABUL EDİLEN KARARLAR

#### 1. Tamsayı Koordinat Sistemi (6/7 oy)
**Karar:** Tüm koordinatlar tamsayı olarak saklanacak, MICRO_UNIT = 0.025m temel birim.

**Gerekçe:**
- Float precision hataları ortadan kalkar
- Çakışma kontrolü deterministik olur
- Memory verimli (int vs float)

**Uygulama:**
```python
# config.py
MICRO_UNIT = 0.025   # 1 grid unit = 2.5cm
SNAP_MODES = {
    "micro":  1,    # 0.025m — silah parçası, vida
    "meso":   10,   # 0.25m  — mobilya, kapı, pencere
    "macro":  40,   # 1.0m   — duvar, oda
}
```

#### 2. Sparse Hashmap Grid (7/7 oy - Oybirliği)
**Karar:** Sahne grid'i `dict[tuple[int,int,int], str]` olarak saklanacak.

**Gerekçe:**
- Sonsuz grid mümkün (sadece dolu hücreler memory kullanır)
- Çakışma kontrolü O(1)
- Basit ve anlaşılır

**Uygulama:**
```python
# engine/grid_manager.py — YENİ DOSYA
class SceneGrid:
    def __init__(self):
        self._cells: dict[tuple[int,int,int], str] = {}
```

#### 3. IGridObject Interface (7/7 oy - Oybirliği)
**Karar:** Tüm atom'lar ortak interface implement edecek.

**Gerekçe:**
- Tip güvenliği (Protocol kullanımı)
- Grid manager ile temiz sözleşme
- Test edilebilirlik

**Uygulama:**
```python
# engine/grid_object.py — YENİ DOSYA
class IGridObject(Protocol):
    name:       str
    grid_pos:   GridPos
    grid_size:  tuple[int, int, int]
    snap_mode:  str
    slots:      list[dict]
```

#### 4. Kademeli Geçiş (7/7 oy - Oybirliği)
**Karar:** Eski API korunacak, yeni sistem paralel çalışacak.

**Gerekçe:**
- Mevcut testler bozulmayacak
- Risk minimize
- Aşamalı migration

**Uygulama:**
```python
# atoms/wall.py'de mevcut snap() korunur
def snap(v: float, mode: str = "meso") -> float:
    pos = GridPos.from_meters(v, 0, 0, snap=mode)
    return pos.to_meters()[0]
```

### ❌ REDDEDİLEN KARARLAR

#### 1. 3 Katmanlı Grid (4/7 oy - Yetersiz)
**Red Gerekçesi:** Tek grid + 3 snap modu yeterli. Ayrı grid sistemleri gereksiz karmaşıklık.

**Alternatif:** SNAP_MODES ile tek grid, farklı snap seviyeleri.

#### 2. Connection Mesh Şimdi (0/7 oy - Oybirliği ile Red)
**Red Gerekçesi:** Overengineering. MVP için AABB çakışma kontrolü yeterli.

**Alternatif:** Connection points sadece veri olarak saklanır, mesh üretimi ileride.

---

## Revize Edilmiş Geliştirme Fazları

### FAZ 1: ✅ Tamamlandı
- GitHub fork ve push
- Analiz dokümanları

### FAZ 2: Tamsayı Grid Sistemi (4 Yeni Dosya)
**Hedef:** Grid altyapısını kurmak, mevcut testleri bozmamak

**Yeni Dosyalar:**
1. `src/blenpc/engine/grid_pos.py` → GridPos class
2. `src/blenpc/engine/grid_manager.py` → SceneGrid class
3. `src/blenpc/engine/grid_object.py` → IGridObject interface
4. `src/blenpc/config.py` → MICRO_UNIT + SNAP_MODES ekle

**Kritik Kural:** Mevcut testler geçmeli. Geçmezse dur, düzelt, devam et.

**Test:**
```bash
python -m pytest tests/ -v
```

---

### FAZ 3: Modüler Duvar Sistemi
**Hedef:** Segment-based duvar, GridPos entegrasyonu

**Güncellenecek Dosyalar:**
- `src/blenpc/atoms/wall.py` → GridPos kullan
  - `build_wall()` → segment listesi + GridPos
  - Opening slot hesaplama (tamsayı koordinat)
  - Manifold-safe mesh

**Yeni Özellikler:**
```python
def build_wall(length, height, thickness=0.2, openings=None):
    # length, height metre olarak gelir
    # İçeride GridPos'a çevrilir
    grid_length = GridPos.from_meters(length, 0, 0, snap="macro")
    
    # Segment hesaplama tamsayı aritmetiği ile
    n_segments = grid_length.x // SNAP_MODES["meso"]
    
    return {
        "segments": [...],  # her segment GridPos
        "slots": [...],     # slot pozisyonları GridPos
        "meta": {...}
    }
```

**Test:** `tests/test_wall_grid.py`

---

### FAZ 4: Modüler Kapı Sistemi
**Hedef:** 4-part kapı, GridPos entegrasyonu

**Yeni Dosya:**
- `src/blenpc/atoms/door.py`
  - `build_door()` → IGridObject implement eder
  - Tüm pozisyonlar GridPos

**Slot Sistemi:**
```python
wall_interface_slot = {
    "id":   "wall_interface",
    "type": "door_opening",
    "pos":  GridPos(48, 0, 42),  # tamsayı koordinat
    "size": (36, 84)  # units cinsinden (0.9m, 2.1m)
}
```

**Test:** `tests/test_door_grid.py`

---

### FAZ 5: Modüler Pencere Sistemi
**Hedef:** 3-part pencere, dual material cam

**Yeni Dosya:**
- `src/blenpc/atoms/window.py`
  - `build_window()` → IGridObject implement eder
  - Cam material sistemi

**Cam Material:**
```python
glass_materials = {
    "transparent": {"alpha": 0.05, "ior": 1.45, "roughness": 0.0},
    "mirror":      {"alpha": 0.0,  "metallic": 1.0, "roughness": 0.0},
    "frosted":     {"alpha": 0.3,  "roughness": 0.6},
    "tinted":      {"alpha": 0.2,  "color": [0.1, 0.1, 0.15]},
}
```

**Test:** `tests/test_window_grid.py`

---

### FAZ 6: Duvar + Kapı/Pencere Entegrasyonu
**Hedef:** Composed wall sistemi

**Güncellenecek Dosyalar:**
- `src/blenpc/atoms/wall.py` → `build_wall_composed()`
- `src/blenpc/run_command.py` → Router güncelle

**JSON Komut:**
```json
{
  "command": "asset.wall_composed",
  "grid_mode": "macro",
  "wall": {
    "length": 5.0,
    "height": 3.0
  },
  "openings": [
    {"type": "door", "position": {"x_ratio": 0.3}},
    {"type": "window", "position": {"x_ratio": 0.8}}
  ]
}
```

**Test:** `tests/test_composed_wall.py`

---

### FAZ 7: Slot Sistemi ve Validation
**Hedef:** Compatibility matrix, otomatik tag

**Güncellenecek Dosyalar:**
- `_registry/slot_types.json` → Compatibility matrix
- `src/blenpc/engine/slot_engine.py` → Validation

**Compatibility Matrix:**
```json
{
  "compatibility": {
    "window_opening": ["arch_window"],
    "door_opening":   ["arch_door"]
  }
}
```

**Test:** `tests/test_slot_validation.py`

---

### FAZ 8: Sims-Tarzı Oda Otomasyonu
**Hedef:** Otomatik oda algılama, zemin/tavan

**Yeni Dosyalar:**
- `src/blenpc/engine/room_detector.py`
  - `detect_enclosed_rooms(walls)`
  - `auto_generate_floor(room_bounds)`
  - `auto_generate_ceiling(room_bounds)`

**Algoritma:**
1. Tüm duvarların GridPos footprint'lerini topla
2. Kapalı alan tespiti (flood fill algoritması)
3. Room objesi oluştur (IGridObject)
4. Zemin ve tavan otomatik ekle

**Test:** `tests/test_room_automation.py`

---

### FAZ 9: Test Suite ve Regression
**Hedef:** Geometry regression, golden file testler

**Yeni Test Dosyaları:**
- `tests/test_geometry_regression.py`
- `tests/test_slot_completeness.py`
- `tests/golden/` klasörü

**Regression Test:**
```python
def test_wall_geometry_regression():
    wall = build_wall(5.0, 3.0, 0.2)
    
    # GridPos doğrulaması
    assert isinstance(wall["grid_pos"], GridPos)
    
    # AABB karşılaştırma
    golden = load_golden("wall_5x3.json")
    assert wall["meta"]["aabb"] == golden["aabb"]
```

**Test Coverage Hedefi:** %80+

---

### FAZ 10: Dokümantasyon ve Final Push
**Hedef:** API docs, kullanım örnekleri, GitHub push

**Güncellenecek Dosyalar:**
- `docs/GRID_SYSTEM.md` → Tamsayı grid açıklaması
- `docs/API_EXAMPLES.md` → JSON komut örnekleri
- `API_REFERENCE.md` → GridPos, SceneGrid API
- `CHANGELOG.md` → v5.2.0 notları

**Dokümantasyon İçeriği:**
- GridPos kullanımı
- Snap mode seçimi
- IGridObject implement etme
- SceneGrid ile çakışma kontrolü

---

## Kritik Mimari Kararlar Özeti

### 1. Tek Grid, 3 Snap Modu
```python
MICRO_UNIT = 0.025m
SNAP_MODES = {
    "micro":  1,    # 2.5cm
    "meso":   10,   # 25cm
    "macro":  40,   # 1m
}
```

### 2. Tamsayı Koordinat
```python
class GridPos:
    x: int  # units (1 unit = 0.025m)
    y: int
    z: int
```

### 3. Sparse Hashmap
```python
_cells: dict[tuple[int,int,int], str] = {}
# Sadece dolu hücreler memory kullanır
```

### 4. Kademeli Geçiş
```python
# Eski API korunur
def snap(v: float) -> float:
    # Yeni sisteme delegate eder
    return GridPos.from_meters(v, 0, 0).to_meters()[0]
```

---

## Başarı Kriterleri

### Teknik
- ✅ Tüm mevcut testler geçmeli
- ✅ Yeni testler %80+ coverage
- ✅ GridPos tüm atom'larda kullanılmalı
- ✅ SceneGrid çakışma kontrolü O(1)
- ✅ Manifold geometri korunmalı

### Performans
- ✅ 5m duvar + kapı + pencere < 2 saniye
- ✅ RAM kullanımı < 3GB
- ✅ Grid lookup < 1ms

### Kod Kalitesi
- ✅ Type hints her yerde
- ✅ Docstring her fonksiyonda
- ✅ Hiçbir test bozulmamalı

---

## Geliştirme Sırası (Öncelik)

### Sprint 1 (Hemen)
1. FAZ 2 - Grid sistemi (4 dosya)
2. FAZ 3 - Duvar GridPos entegrasyonu
3. FAZ 4 - Kapı sistemi

### Sprint 2
4. FAZ 5 - Pencere sistemi
5. FAZ 6 - Composed wall
6. FAZ 7 - Slot validation

### Sprint 3
7. FAZ 8 - Oda otomasyonu
8. FAZ 9 - Test suite
9. FAZ 10 - Dokümantasyon

---

## Önemli Notlar

### 🚨 Kademeli Geçiş Kuralı
Her yeni özellik eklendiğinde:
1. Eski API korunmalı
2. Testler çalıştırılmalı
3. Geçmezse dur, düzelt, devam et

### 🚨 Overengineering Önleme
- Connection mesh → ileride
- LOD sistemi → ileride
- MCP entegrasyonu → ileride

### 🚨 MVP Odaklı
Şimdi sadece:
- Grid sistemi
- Modüler duvar/kapı/pencere
- Slot validation
- Temel oda otomasyonu

---

**Hazırlayan:** Manus AI Agent  
**Tarih:** 2026-02-18  
**Versiyon:** 2.0 (Uzman Panel Revizyonu)  
**Durum:** Plan Güncellendi - FAZ 2 Başlıyor
