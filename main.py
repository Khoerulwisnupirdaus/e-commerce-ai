import os
import sys
import time
from core.vault import StoreVault
from core.camofox import CamofoxClient
from platforms.shopee_register import ShopeeRegisterHandler
from services.recommender import ShoppingRecommender

CAMOFOX_DIR = r"C:\Users\Hype G12\Downloads\camofox-browser"

def print_banner():
    print("\n" + "=" * 70)
    print("      🚀 STORE SWARM AGENT - MULTI-ACCOUNT & SHOPPING ENGINE        ")
    print("            (Otomasi 100-200 Toko + Camofox Browser)                ")
    print("=" * 70)

def show_store_table(vault: StoreVault):
    stores = vault.list_stores()
    print("\n📦 DAFTAR AKUN TOKO DI DATABASE VAULT:")
    print("-" * 75)
    print(f"{'ID':<10} | {'NAMA TOKO':<22} | {'NO. HP':<16} | {'STATUS':<15}")
    print("-" * 75)
    if not stores:
        print("  (Belum ada toko yang terdaftar. Pilih menu 1 untuk menambah toko)")
    else:
        for s in stores:
            status = s.get("status", "NOT_LOGGED_IN")
            status_map = {
                "LOGGED_IN": "✅ AKTIF (LOGIN)",
                "WAITING_OTP": "⏳ MENUNGGU OTP",
                "NOT_LOGGED_IN": "⚪ BELUM LOGIN",
                "ERROR": "❌ GAGAL"
            }
            display_status = status_map.get(status, status)
            print(f"{s['id']:<10} | {s['name'][:22]:<22} | {s['phone']:<16} | {display_status:<15}")
    print("-" * 75)

def menu_rekomendasi_belanja():
    recommender = ShoppingRecommender()
    print("\n--- 🛒 REKOMENDASI BELANJA CERDAS ---")
    keyword = input("Masukkan nama produk yang ingin dicari (misal: 'mouse wireless', 'kopi arabika'): ").strip()
    if not keyword:
        return

    print(f"\n[Agent] Menganalisis katalog dan membandingkan penawaran untuk '{keyword}'...")
    
    # Sample multi-seller comparison data
    mock_products = [
        {
            "title": f"{keyword.title()} Original Garansi Resmi 1 Tahun",
            "price": 89000,
            "rating": 4.9,
            "sales_count": 4200,
            "discount_pct": 25,
            "seller_type": "Official Store",
            "shop_name": "Official Tech Store",
            "recommendation_reason": "Harga diskon tertinggi dengan rating 4.9 dan garansi resmi."
        },
        {
            "title": f"{keyword.title()} Termurah Grosir Berkualitas",
            "price": 65000,
            "rating": 4.4,
            "sales_count": 850,
            "discount_pct": 10,
            "seller_type": "Star Seller",
            "shop_name": "Grosir Mandiri",
            "recommendation_reason": "Harga paling murah namun rating sedikit lebih rendah."
        },
        {
            "title": f"Premium {keyword.title()} Extra Fast Delivery",
            "price": 115000,
            "rating": 4.8,
            "sales_count": 1500,
            "discount_pct": 15,
            "seller_type": "Shopee Mall",
            "shop_name": "Mega Mall Online",
            "recommendation_reason": "Pengiriman kilat dan jaminan keaslian mall."
        }
    ]

    ranked = recommender.rank_products(mock_products)
    report = recommender.generate_recommendation_summary(keyword, ranked)
    print("\n" + report)

def main():
    vault = StoreVault()
    camofox = CamofoxClient()

    while True:
        print_banner()
        show_store_table(vault)
        print("\nMENU OPERASIONAL:")
        print("1. Tambah Toko Baru ke Vault (Input No. HP & Nama)")
        print("2. Mulai Pendaftaran / Login Toko (Agent otomatis buka Camofox)")
        print("3. Masukkan Kode OTP untuk Toko yang Menunggu")
        print("4. Mode Rekomendasi Belanja & Analisis Harga")
        print("5. Cek Status Mesin Camofox Browser")
        print("6. Keluar")

        pilihan = input("\nPilih menu [1-6]: ").strip()

        if pilihan == "1":
            print("\n--- TAMBAH AKUN TOKO BARU ---")
            store_id = input("Masukkan ID Toko (misal: toko_002): ").strip()
            if not store_id:
                print("[!] ID Toko tidak boleh kosong.")
                continue

            name = input("Masukkan Nama Toko: ").strip()
            phone = input("Masukkan Nomor Handphone (format: 08...): ").strip()
            if not phone:
                print("[!] Nomor HP tidak boleh kosong.")
                continue

            vault.add_store(store_id, name, phone, platform="shopee")
            print(f"[OK] Toko '{name}' ({store_id}) berhasil disimpan ke database!")

        elif pilihan == "2":
            print("\n--- MULAI PROSES PENDAFTARAN / LOGIN TOKO ---")
            store_id = input("Masukkan ID Toko: ").strip()
            store = vault.get_store(store_id)
            if not store:
                print(f"[!] Toko '{store_id}' tidak ditemukan di database.")
                continue

            if not camofox.ensure_server(CAMOFOX_DIR):
                print("[!] Server Camofox belum menyala di port 9377. Jalankan 'start_camofox.bat'.")
                continue

            handler = ShopeeRegisterHandler(camofox)
            print(f"\n[Agent] Membuka sesi khusus untuk Toko '{store['name']}' ({store['phone']})...")
            try:
                res = handler.start_registration(store_id, store["phone"])
                tab_id = res.get("tab_id")
                vault.update_status(store_id, "WAITING_OTP", tab_id=tab_id)
                print("\n" + "=" * 55)
                print(f"[OK] Form selesai diisi oleh agent!")
                print(f"[!] Status Toko: MENUNGGU OTP")
                print(f"[!] Cek SMS / WhatsApp di HP {store['phone']}.")
                print("=" * 55)

                otp = input(f"\nMasukkan 6 digit kode OTP untuk {store_id} (atau tekan ENTER untuk isi nanti): ").strip()
                if otp:
                    print(f"[Agent] Memasukkan OTP {otp} ke browser Camofox...")
                    otp_res = handler.submit_otp(tab_id, otp)
                    vault.update_status(store_id, "LOGGED_IN")
                    print(f"\n🎉 [SUKSES] Toko '{store_id}' BERHASIL TERDAFTAR & AKTIF!")
            except Exception as e:
                print(f"[ERROR] Proses pendaftaran mengalami kendala: {e}")

        elif pilihan == "3":
            print("\n--- INPUT KODE OTP TOKO ---")
            store_id = input("Masukkan ID Toko yang menunggu OTP: ").strip()
            store = vault.get_store(store_id)
            if not store:
                print(f"[!] Toko '{store_id}' tidak ditemukan.")
                continue

            tab_id = store.get("active_tab_id")
            if not tab_id:
                print(f"[!] Tidak ada tab aktif untuk {store_id}. Jalankan menu 2 terlebih dahulu.")
                continue

            otp = input(f"Masukkan kode OTP untuk {store_id}: ").strip()
            if otp:
                handler = ShopeeRegisterHandler(camofox)
                handler.submit_otp(tab_id, otp)
                vault.update_status(store_id, "LOGGED_IN")
                print(f"\n🎉 [SUKSES] Toko '{store_id}' BERHASIL TERDAFTAR & AKTIF!")

        elif pilihan == "4":
            menu_rekomendasi_belanja()

        elif pilihan == "5":
            print("\n--- STATUS MESIN CAMOFOX BROWSER ---")
            if camofox.is_running():
                print("🟢 Camofox Browser AKTIF & TERHUBUNG di http://localhost:9377")
            else:
                print("🔴 Camofox Browser BELUM AKTIF. Jalankan 'start_camofox.bat'.")

        elif pilihan == "6":
            print("\nSampai jumpa! Sistem agent siap digunakan kapan saja.")
            break

        input("\nTekan ENTER untuk kembali ke menu...")

if __name__ == "__main__":
    main()
