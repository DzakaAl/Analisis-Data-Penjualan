# Dashboard Analisis Data Penjualan

Proyek ini berisi cleaning data, analisis eksploratif, dan dashboard Streamlit untuk file [SalesData.xlsx](SalesData.xlsx).

## Struktur Proyek

- [notebook.ipynb](notebook.ipynb) untuk cleaning dan analisis.
- [dashboard/dashboard.py](dashboard/dashboard.py) untuk dashboard interaktif.
- [requirements.txt](requirements.txt) untuk dependensi Python.
- [url.txt](url.txt) untuk menyimpan URL dashboard yang sudah dipublikasikan.

## Setup Environment - Anaconda

```bash
conda create --name main-ds python=3.13
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal

```bash
mkdir Data-Penjualan
cd Data-Penjualan
pip install -r requirements.txt
```

## Menjalankan Notebook

Buka [notebook.ipynb](notebook.ipynb) lalu jalankan seluruh sel secara berurutan.

## Menjalankan Dashboard

```bash
streamlit run dashboard/dashboard.py
```

## Langkah Analisis

1. Muat data dari [SalesData.xlsx](SalesData.xlsx).
2. Bersihkan kolom dan validasi kualitas data.
3. Buat fitur turunan seperti bulan, nama bulan, dan profit margin.
4. Analisis tren penjualan, profit, channel, region, dan kategori produk.
5. Jalankan dashboard untuk memfilter dan memvisualisasikan hasil analisis.

## URL Dashboard

Isi file [url.txt](url.txt) dengan URL publik dashboard setelah deployment. Saat ini file tersebut masih memakai URL lokal untuk pengujian.
