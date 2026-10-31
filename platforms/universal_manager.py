import time
from typing import Dict, Any, Optional
from core.camofox import CamofoxClient
from core.vision_solver import OpenCVCanvasSolver
from platforms.registry import get_platform_info, PLATFORM_REGISTRY
from platforms.shopee_login import ShopeeLoginHandler
from platforms.shopee_register import ShopeeRegisterHandler


class UniversalStoreManager:
    """
    Universal Multi-Platform Store Session & Automation Manager.
    Mendukung pengelolaan lebih dari 100+ platform e-commerce & 100+ akun toko terisolasi.
    """

    def __init__(self, camofox: CamofoxClient):
        self.camofox = camofox
        self.vision_solver = OpenCVCanvasSolver(camofox)
        self.shopee_login = ShopeeLoginHandler(camofox)
        self.shopee_register = ShopeeRegisterHandler(camofox)

    def open_store_session(self, store: Dict[str, Any], mode: str = "seller") -> Dict[str, Any]:
        """
        Membuka sesi browser terisolasi khusus untuk akun toko pada platform mana pun
        (Shopee, Tokopedia, TikTok Shop, Lazada, Blibli, Amazon, Shopify, dll.).
        """
        store_id = store["id"]
        platform_key = store.get("platform", "shopee_id")
        phone = store.get("phone", "")

        platform_info = get_platform_info(platform_key)
        if not platform_info:
            return {
                "success": False,
                "error": f"Platform '{platform_key}' tidak ditemukan di registry."
            }

        # Jika platform adalah Shopee dan mode login/register spesifik diminta
        if platform_key in ("shopee", "shopee_id") and mode == "register":
            return self.shopee_register.start_registration(store_id, phone)
        elif platform_key in ("shopee", "shopee_id") and mode == "login":
            return self.shopee_login.start_login(store_id, phone)

        # Isolasi profil Camofox spesifik per toko & platform
        self.camofox.user_id = f"store_{store_id}"
        self.camofox.session_key = f"session_{platform_key}_{store_id}"

        target_url = platform_info.get("seller_url") if mode == "seller" else platform_info.get("login_url")
        if not target_url:
            target_url = platform_info["base_url"]

        print(f"[{store_id}] Membuka sesi terisolasi untuk {platform_info['name']} -> {target_url}")
        tab_info = self.camofox.create_tab(url=target_url)
        tab_id = tab_info.get("tabId")
        time.sleep(2.5)

        # Cek apabila ada kanvas puzzle slider dan jalankan vision solver otomatis
        if self.vision_solver.has_puzzle(tab_id):
            print(f"[{store_id}] Puzzle terdeteksi di {platform_info['name']}, menjalankan Vision Solver...")
            self.vision_solver.solve(tab_id)

        return {
            "success": True,
            "store_id": store_id,
            "platform": platform_key,
            "platform_name": platform_info["name"],
            "tab_id": tab_id,
            "target_url": target_url,
            "message": f"Sesi {platform_info['name']} untuk toko '{store.get('name')}' aktif."
        }
