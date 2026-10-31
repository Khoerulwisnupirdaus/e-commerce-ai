import os
import sys
import time
from core.vault import StoreVault
from core.camofox import CamofoxClient
from platforms.registry import PLATFORM_REGISTRY, list_all_platforms, get_platform_summary_by_region, get_platform_info
from platforms.universal_manager import UniversalStoreManager
from platforms.shopee_register import ShopeeRegisterHandler
from services.recommender import ShoppingRecommender

CAMOFOX_DIR = r"C:\Users\Hype G12\Downloads\camofox-browser"


def print_banner(vault: StoreVault):
    stats = vault.get_vault_stats()
    print("\n" + "=" * 82)
    print("      🚀 E-COMMERCE AI — MULTI-PLATFORM SWARM AGENT (125+ PLATFORMS / STORES)     ")
    print(f"   Total Toko: {stats['total_stores']} | Platform Unik: {stats['unique_platforms']} | Aktif: {stats['logged_in']} | Menunggu OTP: {stats['waiting_otp']}")
    print("=" * 82)


def show_store_table(vault: StoreVault, limit: int = 15, platform_filter: str = None, region_filter: str = None):
    stores = vault.list_stores(platform=platform_filter, region=region_filter)
    print(f"\n📦 DAFTAR AKUN TOKO DI DATABASE VAULT (Menampilkan {min(len(stores), limit)} dari {len(stores)} toko):")
    print("-" * 92)
    print(f"{'ID':<9} | {'PLATFORM':<16} | {'NAMA TOKO':<28} | {'REGION':<15} | {'STATUS':<14}")
    print("-" * 92)
    if not stores:
        print("  (Belum ada toko. Pilih Menu 2 untuk generate otomatis 125 toko lintas platform)")
    else:
        status_map = {
            "LOGGED_IN": "✅ AKTIF",
            "WAITING_OTP": "⏳ WAITING OTP",
            "NOT_LOGGED_IN": "⚪ BELUM LOGIN",
            "ERROR": "❌ ERROR"
        }
        for s in stores[:limit]:
            status = status_map.get(s.get("status", "NOT_LOGGED_IN"), s.get("status", ""))
            plat = s.get("platform", "shopee_id")[:16]
            name = s.get("name", "")[:28]
            reg = s.get("region", "Indonesia")[:15]
            print(f"{s['id']:<9} | {plat:<16} | {name:<28} | {reg:<15} | {status:<14}")
        if len(stores) > limit:
            print(f"  ... dan {len(stores) - limit} toko lainnya (gunakan Menu 3 untuk filter lengkap).")
    print("-" * 92)


def menu_katalog_platform():
    summary = get_platform_summary_by_region()
    print("\n🌍 RINGKASAN 125+ PLATFORM E-COMMERCE YANG DIDUKUNG:")
    for reg, cnt in summary.items():
        print(f"  • {reg:<26}: {cnt} platform")

    region_q = input("\nKetik nama region untuk filter (misal: 'Indonesia', 'East Asia', 'Europe', atau ENTER untuk semua): ").strip()
    platforms = list_all_platforms(region=region_q if region_q else None)
    print("\n" + "-" * 95)
    print(f"{'ID PLATFORM':<18} | {'NAMA PLATFORM':<28} | {'REGION':<18} | {'KATEGORI':<22}")
    print("-" * 95)
    for p in platforms:
        print(f"{p['id']:<18} | {p['name'][:28]:<28} | {p['region'][:18]:<18} | {p['category'][:22]:<22}")
    print("-" * 95)
    print(f"Total ditampilkan: {len(platforms)} platform.")


def menu_rekomendasi_belanja():
    recommender = ShoppingRecommender()
    print("\n--- 🛒 REKOMENDASI BELANJA & ANALISIS HARGA LINTAS MARKETPLACE ---")
    keyword = input("Masukkan nama produk yang ingin dicari (misal: 'mouse wireless', 'kopi arabika'): ").strip()
    if not keyword:
        return

    print(f"\n[Agent] Menganalisis katalog dan membandingkan penawaran untuk '{keyword}'...")
    mock_products = [
        {
            "title": f"{keyword.title()} Original Garansi Resmi 1 Tahun",
            "price": 89000,
            "rating": 4.9,
            "sales_count": 4200,
            "discount_pct": 25,
            "seller_type": "Official Store",
            "shop_name": "Official Tech Store (Shopee Mall)",
            "recommendation_reason": "Harga diskon tertinggi dengan rating 4.9 dan garansi resmi."
        },
        {
            "title": f"{keyword.title()} Termurah Grosir Berkualitas",
            "price": 65000,
            "rating": 4.4,
            "sales_count": 850,
            "discount_pct": 10,
            "seller_type": "Star Seller",
            "shop_name": "Grosir Mandiri (Tokopedia Power Merchant)",
            "recommendation_reason": "Harga paling murah namun rating sedikit lebih rendah."
        },
        {
            "title": f"Premium {keyword.title()} Extra Fast Delivery",
            "price": 115000,
            "rating": 4.8,
            "sales_count": 1500,
            "discount_pct": 15,
            "seller_type": "LazMall",
            "shop_name": "Mega Mall Online (Lazada)",
            "recommendation_reason": "Pengiriman kilat dan jaminan keaslian mall."
        }
    ]

    ranked = recommender.rank_products(mock_products)
    report = recommender.generate_recommendation_summary(keyword, ranked)
    print("\n" + report)


def main():
    vault = StoreVault()
    # Auto-seed 125 stores if vault is empty or has < 100 stores
    if len(vault.stores) < 100:
        vault.seed_125_stores(overwrite=True)

    camofox = CamofoxClient()

    while True:
        print_banner(vault)
        show_store_table(vault, limit=15)
        print("\nMENU OPERASIONAL E-COMMERCE AI:")
        print("1. Tambah Akun Toko Baru ke Vault (Pilih dari 125+ Platform)")
        print("2. Generate / Reset Massal 125 Akun Toko Lintas Marketplace (100+ Toko)")
        print("3. Lihat Katalog 125+ Platform Marketplace & Filter Daftar Toko")
        print("4. Mulai Sesi Login / Seller Center Toko (Camofox + Vision Solver)")
        print("5. Masukkan Kode OTP untuk Toko yang Menunggu")
        print("6. Mode Rekomendasi Belanja & Analisis Harga Kompetitor")
        print("7. Cek Status Mesin Camofox Browser")
        print("8. Keluar")

        pilihan = input("\nPilih menu [1-8]: ").strip()

        if pilihan == "1":
            print("\n--- TAMBAH AKUN TOKO BARU ---")
            store_id = input("Masukkan ID Toko (misal: toko_126): ").strip()
            if not store_id:
                print("[!] ID Toko tidak boleh kosong.")
                continue

            platform = input("Masukkan ID Platform (misal: shopee_id, tokopedia, tiktok_shop_id, lazada_id, amazon_us, shopify): ").strip() or "shopee_id"
            name = input("Masukkan Nama Toko: ").strip()
            phone = input("Masukkan Nomor Handphone (format: 08...): ").strip()
            if not phone:
                print("[!] Nomor HP tidak boleh kosong.")
                continue

            vault.add_store(store_id, name, phone, platform=platform)
            print(f"[OK] Toko '{name}' ({store_id}) pada platform '{platform}' berhasil disimpan!")

        elif pilihan == "2":
            konfirmasi = input("Inisialisasi ulang 125 akun toko lintas 125 platform e-commerce? [y/N]: ").strip().lower()
            if konfirmasi == "y":
                total = vault.seed_125_stores(overwrite=True)
                print(f"[OK] Berhasil membuat {total} akun toko lintas platform di database vault!")

        elif pilihan == "3":
            menu_katalog_platform()
            plat_f = input("\nFilter daftar toko berdasarkan platform (kosongkan untuk lewati): ").strip()
            reg_f = input("Filter daftar toko berdasarkan region (kosongkan untuk lewati): ").strip()
            if plat_f or reg_f:
                show_store_table(vault, limit=125, platform_filter=plat_f or None, region_filter=reg_f or None)

        elif pilihan == "4":
            print("\n--- MULAI SESI LOGIN / SELLER CENTER TOKO ---")
            store_id = input("Masukkan ID Toko (misal: toko_001 s/d toko_125): ").strip()
            store = vault.get_store(store_id)
            if not store:
                print(f"[!] Toko '{store_id}' tidak ditemukan di database.")
                continue

            if not camofox.ensure_server(CAMOFOX_DIR):
                print("[!] Server Camofox belum menyala di port 9377. Jalankan 'start_camofox.bat'.")
                continue

            mode = input("Pilih mode [1=Login Buyer/OTP, 2=Registrasi Baru, 3=Seller Center Dashboard] (default: 1): ").strip()
            mode_str = {"1": "login", "2": "register", "3": "seller"}.get(mode, "login")

            manager = UniversalStoreManager(camofox)
            try:
                res = manager.open_store_session(store, mode=mode_str)
                tab_id = res.get("tab_id")
                vault.update_status(store_id, "WAITING_OTP", tab_id=tab_id)
                print("\n" + "=" * 60)
                print(f"[OK] {res.get('message')}")
                print(f"[!] Tab ID Aktif: {tab_id}")
                print("=" * 60)
            except Exception as e:
                print(f"[ERROR] Kendala saat membuka sesi toko: {e}")

        elif pilihan == "5":
            print("\n--- INPUT KODE OTP TOKO ---")
            store_id = input("Masukkan ID Toko yang menunggu OTP: ").strip()
            store = vault.get_store(store_id)
            if not store:
                print(f"[!] Toko '{store_id}' tidak ditemukan.")
                continue

            tab_id = store.get("active_tab_id")
            if not tab_id:
                print(f"[!] Tidak ada tab aktif untuk {store_id}. Jalankan menu 4 terlebih dahulu.")
                continue

            otp = input(f"Masukkan kode OTP untuk {store_id}: ").strip()
            if otp:
                handler = ShopeeRegisterHandler(camofox)
                handler.submit_otp(tab_id, otp)
                vault.update_status(store_id, "LOGGED_IN")
                print(f"\n🎉 [SUKSES] Toko '{store_id}' BERHASIL AKTIF!")

        elif pilihan == "6":
            menu_rekomendasi_belanja()

        elif pilihan == "7":
            print("\n--- STATUS MESIN CAMOFOX BROWSER ---")
            if camofox.is_running():
                print("🟢 Camofox Browser AKTIF & TERHUBUNG di http://localhost:9377")
            else:
                print("🔴 Camofox Browser BELUM AKTIF. Jalankan 'start_camofox.bat'.")

        elif pilihan == "8":
            print("\nSampai jumpa! Sistem E-Commerce AI siap digunakan kapan saja.")
            break

        input("\nTekan ENTER untuk kembali ke menu...")


if __name__ == "__main__":
    main()
