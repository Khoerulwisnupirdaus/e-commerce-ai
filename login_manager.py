import os
import sys
import time
from core.vault import StoreVault
from core.camofox import CamofoxClient
from platforms.shopee_login import ShopeeLoginHandler

CAMOFOX_DIR = r"C:\Users\Hype G12\Downloads\camofox-browser"

def print_banner():
    print("=" * 60)
    print("      STORE SWARM AGENT - MULTI-ACCOUNT LOGIN MANAGER       ")
    print("         (Shopee / Camofox Anti-Detect Automation)          ")
    print("=" * 60)

def show_store_table(vault: StoreVault):
    stores = vault.list_stores()
    if not stores:
        print("\n[!] Belum ada toko di database vault. Silakan tambah toko baru.")
        return

    print("\nDAFTAR TOKO / AKUN DI VAULT:")
    print("-" * 75)
    print(f"{'ID':<10} | {'NAMA TOKO':<22} | {'NO. HP':<16} | {'STATUS':<15}")
    print("-" * 75)
    for s in stores:
        status = s.get("status", "NOT_LOGGED_IN")
        status_display = {
            "LOGGED_IN": "AKTIF (LOGIN)",
            "WAITING_OTP": "MENUNGGU OTP",
            "NOT_LOGGED_IN": "BELUM LOGIN",
            "ERROR": "GAGAL"
        }.get(status, status)

        print(f"{s['id']:<10} | {s['name'][:22]:<22} | {s['phone']:<16} | {status_display:<15}")
    print("-" * 75)

def main():
    vault = StoreVault()
    camofox = CamofoxClient()

    while True:
        print_banner()
        show_store_table(vault)
        print("\nMENU UTAMA:")
        print("1. Tambah Akun Toko Baru (Input nomor HP & nama)")
        print("2. Mulai Login Toko (Kirim OTP ke HP)")
        print("3. Masukkan Kode OTP untuk Toko yang Menunggu")
        print("4. Cek Koneksi Server Camofox")
        print("5. Keluar")

        pilihan = input("\nPilih menu [1-5]: ").strip()

        if pilihan == "1":
            print("\n--- TAMBAH AKUN TOKO BARU ---")
            store_id = input("Masukkan ID Toko (misal: toko_001): ").strip()
            if not store_id:
                print("[!] ID Toko tidak boleh kosong.")
                continue

            if vault.get_store(store_id):
                print(f"[!] Toko dengan ID '{store_id}' sudah ada di vault!")
                continue

            name = input("Masukkan Nama Toko / Keterangan: ").strip()
            phone = input("Masukkan Nomor Handphone (format: 08...): ").strip()
            if not phone:
                print("[!] Nomor HP tidak boleh kosong.")
                continue

            vault.add_store(store_id, name, phone, platform="shopee")
            print(f"[OK] Toko '{name}' ({store_id}) berhasil ditambahkan ke vault!")

        elif pilihan == "2":
            print("\n--- MULAI PROSES LOGIN TOKO ---")
            store_id = input("Masukkan ID Toko yang ingin di-login: ").strip()
            store = vault.get_store(store_id)
            if not store:
                print(f"[!] ID Toko '{store_id}' tidak ditemukan di vault.")
                continue

            print(f"\n[1/3] Menyiapkan koneksi ke Camofox stealth engine...")
            if not camofox.ensure_server(CAMOFOX_DIR):
                print("[!] Server Camofox belum menyala di port 9377.")
                print(f"[!] Jalankan file 'start_camofox.bat' atau jalankan 'npm start' di {CAMOFOX_DIR}")
                continue

            handler = ShopeeLoginHandler(camofox)
            print(f"[2/3] Membuka sesi khusus untuk Toko '{store['name']}' ({store['phone']})...")
            
            try:
                result = handler.start_login(store_id, store["phone"])
                tab_id = result.get("tab_id")
                vault.update_status(store_id, "WAITING_OTP", tab_id=tab_id)
                print("\n" + "=" * 50)
                print(f"[OK] {result.get('message')}")
                print(f"[!] Status Toko '{store_id}' sekarang: MENUNGGU OTP")
                print(f"[!] Silakan cek SMS / WhatsApp di HP nomor {store['phone']}.")
                print("=" * 50)

                # Langsung beri opsi input OTP
                otp_code = input(f"\nMasukkan kode OTP untuk {store_id} (atau tekan ENTER untuk input nanti): ").strip()
                if otp_code:
                    print(f"[3/3] Memasukkan kode OTP '{otp_code}' ke browser Camofox...")
                    otp_res = handler.submit_otp(tab_id, otp_code)
                    if otp_res.get("is_logged_in"):
                        vault.update_status(store_id, "LOGGED_IN")
                        print(f"\n[SUKSES] Toko '{store_id}' BERHASIL LOGIN & SESI TERSIMPAN!")
                    else:
                        print(f"\n[?] Hasil verifikasi: {otp_res}")
                        print("[i] Sesi disimpan. Anda dapat mengecek status toko kembali.")
            except Exception as e:
                print(f"[ERROR] Terjadi kesalahan saat proses login: {e}")
                vault.update_status(store_id, "ERROR")

        elif pilihan == "3":
            print("\n--- INPUT KODE OTP TOKO ---")
            store_id = input("Masukkan ID Toko yang menunggu OTP: ").strip()
            store = vault.get_store(store_id)
            if not store:
                print(f"[!] Toko '{store_id}' tidak ditemukan.")
                continue

            tab_id = store.get("active_tab_id")
            if not tab_id:
                print(f"[!] Tidak ada tab aktif untuk '{store_id}'. Silakan jalankan menu #2 terlebih dahulu.")
                continue

            otp_code = input(f"Masukkan kode OTP untuk {store_id}: ").strip()
            if not otp_code:
                print("[!] Kode OTP tidak boleh kosong.")
                continue

            handler = ShopeeLoginHandler(camofox)
            otp_res = handler.submit_otp(tab_id, otp_code)
            if otp_res.get("is_logged_in"):
                vault.update_status(store_id, "LOGGED_IN")
                print(f"\n[SUKSES] Toko '{store_id}' BERHASIL LOGIN!")
            else:
                print(f"\n[i] Status verifikasi: {otp_res}")

        elif pilihan == "4":
            print("\n--- CEK STATUS SERVER CAMOFOX ---")
            if camofox.is_running():
                print("[OK] Server Camofox SEDANG AKTIF di http://localhost:9377!")
            else:
                print("[X] Server Camofox BELUM AKTIF.")
                print("Mencoba menyalakan server otomatis...")
                if camofox.ensure_server(CAMOFOX_DIR):
                    print("[OK] Server Camofox berhasil dinyalakan!")
                else:
                    print("[!] Silakan jalankan 'start_camofox.bat' secara manual.")

        elif pilihan == "5":
            print("\nSampai jumpa! Data vault telah tersimpan.")
            break
        else:
            print("[!] Pilihan tidak valid.")

        input("\nTekan ENTER untuk kembali ke menu...")

if __name__ == "__main__":
    main()
