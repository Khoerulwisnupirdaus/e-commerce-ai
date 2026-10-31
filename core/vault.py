import os
import json
from datetime import datetime
from typing import List, Dict, Optional

VAULT_FILE = "store_vault.json"

class StoreVault:
    """Manages the database of multi-store accounts (100-200 stores)."""

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

    def add_store(self, store_id: str, name: str, phone: str, platform: str = "shopee", proxy: Optional[str] = None) -> Dict:
        """Register a new store into the vault."""
        store_id = store_id.strip()
        data = {
            "id": store_id,
            "name": name.strip(),
            "phone": phone.strip(),
            "platform": platform.lower(),
            "proxy": proxy,
            "status": "NOT_LOGGED_IN",  # NOT_LOGGED_IN, WAITING_OTP, LOGGED_IN, ERROR
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": None,
            "active_tab_id": None
        }
        self.stores[store_id] = data
        self.save()
        return data

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

    def list_stores(self, platform: Optional[str] = None) -> List[Dict]:
        """List all stores, optionally filtered by platform."""
        res = list(self.stores.values())
        if platform:
            res = [s for s in res if s.get("platform") == platform.lower()]
        return res
