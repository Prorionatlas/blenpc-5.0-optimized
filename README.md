# MF v5.1 - Godot Static Level Engine (Blender Edition)

Bu proje, Blender kullanarak deterministik, prosedürel binalar üreten ve Godot Engine uyumlu GLB çıktıları sağlayan bir üretim hattıdır.

## Özellikler
- **Deterministik BSP**: Aynı seed değeri ile her zaman aynı kat planı üretilir.
- **Koridor Farkındalığı**: Odalar koridorları kesmez, koridorlar merkezi omurga olarak korunur.
- **Manifold-Safe Duvarlar**: Boolean işlemleri yerine segment tabanlı üretim ile temiz mesh yapısı sağlanır.
- **Godot Hazır**: Otomatik collider (`-col` suffix) ve GLB export pipeline.
- **Modüler Mimari**: Blender bağımlılığı sadece mesh üretim ve export aşamasındadır.

## Kurulum ve Kullanım

### Gereksinimler
- Blender 3.0+
- Python 3.10+ (Blender içindeki Python sürümü ile uyumlu olmalıdır)
- `numpy` (Blender GLTF export eklentisi için gereklidir)

### Çalıştırma
Bina üretimini başlatmak için:
```bash
blender --background --python run_blender.py
```

### Çıktılar
Üretilen dosyalar `./output` dizinine kaydedilir:
- `Building.glb`: Ana bina mesh'i.
- `Building-col.glb`: Godot için otomatik collision mesh'i.
- `export_manifest.json`: Üretim ve export detaylarını içeren rapor.

## Mimari (v5.1)
- `config.py`: Merkezi sabitler ve grid ayarları.
- `floorplan.py`: BSP tabanlı kat planı üretimi.
- `blender_mesh.py`: Blender API (`bpy`, `bmesh`) ile mesh inşası.
- `engine.py`: Tüm süreci yöneten orkestratör.
