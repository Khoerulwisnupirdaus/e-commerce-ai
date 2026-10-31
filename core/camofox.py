import time
import requests
import subprocess
import os
import json
from typing import Optional, Dict, Any

class CamofoxClient:
    """Client to interact with Camofox Anti-Detect Browser REST API."""

    def __init__(self, base_url: str = "http://localhost:9377", user_id: str = "agent_user", session_key: str = "default"):
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.session_key = session_key

    def is_running(self) -> bool:
        """Check if Camofox browser server is healthy and accepting requests."""
        try:
            r = requests.get(f"{self.base_url}/health", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def ensure_server(self, server_dir: Optional[str] = None) -> bool:
        """Verify server is running, or attempt to launch it in background if not."""
        if self.is_running():
            return True

        if server_dir and os.path.exists(server_dir):
            print(f"[Camofox] Server belum aktif. Menjalankan server dari {server_dir}...")
            try:
                subprocess.Popen(
                    ["cmd.exe", "/c", "npm", "start"],
                    cwd=server_dir,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                for _ in range(15):
                    time.sleep(2)
                    if self.is_running():
                        print("[Camofox] Server berhasil aktif di port 9377!")
                        return True
            except Exception as e:
                print(f"[Camofox] Gagal menjalankan server otomatis: {e}")

        return self.is_running()

    def create_tab(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Create a new browser tab with session isolation."""
        payload = {
            "userId": self.user_id,
            "sessionKey": self.session_key
        }
        if url:
            payload["url"] = url
        res = requests.post(f"{self.base_url}/tabs", json=payload, timeout=30)
        res.raise_for_status()
        return res.json()

    def navigate(self, tab_id: str, url: Optional[str] = None, macro: Optional[str] = None, query: Optional[str] = None) -> Dict[str, Any]:
        """Navigate tab to URL or invoke a search macro."""
        payload = {"userId": self.user_id}
        if macro:
            payload["macro"] = macro
            if query:
                payload["query"] = query
        elif url:
            payload["url"] = url

        res = requests.post(f"{self.base_url}/tabs/{tab_id}/navigate", json=payload, timeout=45)
        res.raise_for_status()
        return res.json()

    def snapshot(self, tab_id: str, screenshot: bool = False) -> Dict[str, Any]:
        """Get accessibility tree snapshot with interactive refs (e.g., e1, e2)."""
        params = {"userId": self.user_id}
        if screenshot:
            params["screenshot"] = "true"
        res = requests.get(f"{self.base_url}/tabs/{tab_id}/snapshot", params=params, timeout=30)
        res.raise_for_status()
        return res.json()

    def click(self, tab_id: str, ref: Optional[str] = None, selector: Optional[str] = None) -> Dict[str, Any]:
        """Click an element by ref or CSS selector."""
        payload = {"userId": self.user_id}
        if ref:
            payload["ref"] = ref
        elif selector:
            payload["selector"] = selector
        res = requests.post(f"{self.base_url}/tabs/{tab_id}/click", json=payload, timeout=20)
        res.raise_for_status()
        return res.json()

    def type_text(self, tab_id: str, text: str, ref: Optional[str] = None, selector: Optional[str] = None, press_enter: bool = False) -> Dict[str, Any]:
        """Type text into an input field identified by ref or selector."""
        payload = {
            "userId": self.user_id,
            "text": text,
            "pressEnter": press_enter
        }
        if ref:
            payload["ref"] = ref
        elif selector:
            payload["selector"] = selector
        res = requests.post(f"{self.base_url}/tabs/{tab_id}/type", json=payload, timeout=20)
        res.raise_for_status()
        return res.json()

    def press(self, tab_id: str, key: str) -> Dict[str, Any]:
        """Send a keyboard key press (e.g. Enter, Escape, ArrowDown)."""
        payload = {"userId": self.user_id, "key": key}
        res = requests.post(f"{self.base_url}/tabs/{tab_id}/press", json=payload, timeout=15)
        res.raise_for_status()
        return res.json()

    def drag(self, tab_id: str, selector: str = ".dExCsf", distance_x: int = 100, distance_y: int = 0, duration_ms: int = 650, target_piece_x: Optional[float] = None) -> Dict[str, Any]:
        """Hardware-level native mouse drag with isTrusted=true (bypasses bot detection)."""
        payload = {
            "userId": self.user_id,
            "selector": selector,
            "distanceX": distance_x,
            "distanceY": distance_y,
            "durationMs": duration_ms
        }
        if target_piece_x is not None:
            payload["targetPieceX"] = float(target_piece_x)
        res = requests.post(f"{self.base_url}/tabs/{tab_id}/drag", json=payload, timeout=60)
        res.raise_for_status()
        return res.json()

    def scroll(self, tab_id: str, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        """Scroll page."""
        payload = {
            "userId": self.user_id,
            "direction": direction,
            "amount": amount
        }
        res = requests.post(f"{self.base_url}/tabs/{tab_id}/scroll", json=payload, timeout=15)
        res.raise_for_status()
        return res.json()

    def wait(self, tab_id: str, ms: int = 1500) -> Dict[str, Any]:
        """Wait for specified milliseconds."""
        payload = {"userId": self.user_id, "ms": ms}
        try:
            res = requests.post(f"{self.base_url}/tabs/{tab_id}/wait", json=payload, timeout=20)
            return res.json()
        except Exception:
            time.sleep(ms / 1000.0)
            return {"status": "ok"}

    def evaluate(self, tab_id: str, script: str) -> Dict[str, Any]:
        """Execute JavaScript inside the tab context."""
        payload = {"userId": self.user_id, "expression": script}
        res = requests.post(f"{self.base_url}/tabs/{tab_id}/evaluate", json=payload, timeout=20)
        res.raise_for_status()
        return res.json()

    def save_screenshot(self, tab_id: str, output_path: str) -> bool:
        """Capture screenshot and save to file."""
        try:
            res = requests.get(
                f"{self.base_url}/tabs/{tab_id}/screenshot",
                params={"userId": self.user_id},
                timeout=25
            )
            if res.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(res.content)
                return True
        except Exception as e:
            print(f"[Camofox] Gagal screenshot: {e}")
        return False

    def close_tab(self, tab_id: str) -> bool:
        """Close an open tab."""
        try:
            requests.delete(f"{self.base_url}/tabs/{tab_id}", params={"userId": self.user_id}, timeout=10)
            return True
        except Exception:
            return False
