# BlenPC v5.1.1 (Expert Edition)

BlenPC, Blender 5.0.1+ için geliştirilmiş, uzman kadro kararlarıyla modernize edilmiş prosedürel bina üretim motorudur.

## 🏗️ Uzman Mimari (Expert Architecture)
Bu sürüm, 10 farklı uzman disiplinin (Software Architect, DevOps, QA, UX vb.) kararlarıyla `src/` tabanlı modern bir paket yapısına kavuşmuştur.

### Klasör Yapısı
```text
blenpc-5.0-optimized/
├── src/
│   └── blenpc/            # Ana Paket (Source)
│       ├── atoms/         # Temel yapı taşları (Wall, Window, Door)
│       ├── engine/        # Envanter ve Slot motoru
│       ├── mf_v5/         # Bina üretim mantığı
│       ├── config.py      # Uzman ayarları ve path yönetimi
│       └── run_command.py # Blender bridge script
├── tests/                 # Otomatik testler
├── _library/              # Üretilen .blend varlıkları
├── _registry/             # JSON tabanlı varlık veritabanı
├── output/                # Çıktı (GLB, FBX) dizini
└── blenpc.py              # Modern CLI Giriş Noktası
```

## 🚀 Hızlı Başlangıç (CLI)

### 1. Bina Üretimi
```bash
# Parametrelerle
python blenpc.py generate -w 20 -d 16 -f 3 -s 42 --roof gabled

# YAML Spec dosyasından
python blenpc.py generate --spec mansion.yaml
```

### 2. Batch (Toplu) Üretim
```bash
python blenpc.py batch --spec city_block.yaml
```

### 3. Varlık (Asset) Kaydı
```bash
python blenpc.py registry list
```

## 🔧 Uzman Ayarları (config.py)
10 yeni kritik ayar ve 10 mimari düzeltme uygulanmıştır:
-   **Windows Uyumluluğu:** Blender yolu otomatik keşfi ve `%APPDATA%` desteği.
-   **Hassasiyet:** `EXPORT_PRECISION` ile koordinat yuvarlama kontrolü.
-   **Güvenlik:** `AUTO_BACKUP_REGISTRY` ve dosya kilitleme sistemi.
-   **Performans:** `CACHE_ENABLED` ve `MAX_WORKER_PROCESSES`.

## 🛠️ Kurulum
```bash
git clone https://github.com/ozyorionlast-cloud/blenpc-5.0-optimized
pip install -r requirements.txt
```

## 📄 Lisans
MIT License - Uzman Kadro tarafından geliştirilmiştir.
