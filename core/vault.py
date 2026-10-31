import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from platforms.registry import PLATFORM_REGISTRY, get_platform_info

VAULT_FILE = "store_vault.json"


class StoreVault:
    """Manages the database of multi-store accounts (100-200+ stores across 125+ platforms)."""

    def __init__(self, filepath: str = VAULT_FILE):
        self.filepath = filepath
        self.stores: Dict[str, Dict] = {}
        self.load()

    def load(self):
        """Load store records from JSON vault."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.stores = json.load(f)
            except Exception:
                self.stores = {}
        else:
            self.stores = {}

    def save(self):
        """Save store records to JSON vault."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.stores, f, indent=2, ensure_ascii=False)

    def add_store(
        self,
        store_id: str,
        name: str,
        phone: str,
        platform: str = "shopee_id",
        category: str = "General",
        region: str = "Indonesia",
        proxy: Optional[str] = None
    ) -> Dict:
        """Register a new store into the vault."""
        store_id = store_id.strip()
        p_info = get_platform_info(platform)
        if p_info:
            region = p_info["region"]
            category = p_info["category"]

        data = {
            "id": store_id,
            "name": name.strip(),
            "phone": phone.strip(),
            "platform": platform.lower(),
            "platform_name": p_info["name"] if p_info else platform,
            "region": region,
            "category": category,
            "seller_url": p_info["seller_url"] if p_info else "",
            "proxy": proxy,
            "status": "NOT_LOGGED_IN",  # NOT_LOGGED_IN, WAITING_OTP, LOGGED_IN, ERROR
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": None,
            "active_tab_id": None
        }
        self.stores[store_id] = data
        self.save()
        return data

    def seed_125_stores(self, overwrite: bool = False) -> int:
        """
        Inisialisasi otomatis 125 akun toko di seluruh 125 platform e-commerce
        (Indonesia, Asia Tenggara, Asia Timur, Amerika, Eropa, MENA, dan Storefront CMS).
        """
        if self.stores and not overwrite:
            return len(self.stores)

        if overwrite:
            self.stores = {}

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for idx, (platform_id, meta) in enumerate(PLATFORM_REGISTRY.items(), start=1):
            store_id = f"toko_{idx:03d}"
            phone_stub = f"0812{idx:08d}"
            store_name = f"Official Store {idx:03d} - {meta['name']}"
            self.stores[store_id] = {
                "id": store_id,
                "name": store_name,
                "phone": phone_stub,
                "platform": platform_id,
                "platform_name": meta["name"],
                "region": meta["region"],
                "category": meta["category"],
                "seller_url": meta["seller_url"],
                "proxy": None,
                "status": "NOT_LOGGED_IN",
                "created_at": now_str,
                "last_login": None,
                "active_tab_id": None
            }

        self.save()
        return len(self.stores)

    def get_store(self, store_id: str) -> Optional[Dict]:
        """Retrieve a specific store record."""
        return self.stores.get(store_id)

    def update_status(self, store_id: str, status: str, tab_id: Optional[str] = None):
        """Update login state and active tab for a store."""
        if store_id in self.stores:
            self.stores[store_id]["status"] = status
            if tab_id is not None:
                self.stores[store_id]["active_tab_id"] = tab_id
            if status == "LOGGED_IN":
                self.stores[store_id]["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save()

    def list_stores(self, platform: Optional[str] = None, region: Optional[str] = None) -> List[Dict]:
        """List all stores, optionally filtered by platform or region."""
        res = list(self.stores.values())
        if platform:
            res = [s for s in res if platform.lower() in s.get("platform", "").lower()]
        if region:
            res = [s for s in res if region.lower() in s.get("region", "").lower()]
        return res

    def get_vault_stats(self) -> Dict[str, int]:
        """Return summary statistics of stores in the vault."""
        total = len(self.stores)
        logged_in = sum(1 for s in self.stores.values() if s.get("status") == "LOGGED_IN")
        waiting_otp = sum(1 for s in self.stores.values() if s.get("status") == "WAITING_OTP")
        not_logged_in = sum(1 for s in self.stores.values() if s.get("status") == "NOT_LOGGED_IN")
        platforms_count = len({s.get("platform") for s in self.stores.values()})
        return {
            "total_stores": total,
            "unique_platforms": platforms_count,
            "logged_in": logged_in,
            "waiting_otp": waiting_otp,
            "not_logged_in": not_logged_in
        }
