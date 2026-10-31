import time
from typing import Dict, Any, Optional
from core.camofox import CamofoxClient
from core.vision_solver import OpenCVCanvasSolver

class ShopeeLoginHandler:
    """Handles Shopee Login and Registration flow via Camofox stealth browser."""

    LOGIN_URL = "https://shopee.co.id/buyer/login"

    def __init__(self, camofox: CamofoxClient):
        self.camofox = camofox
        self.vision_solver = OpenCVCanvasSolver(camofox)

    def start_login(self, store_id: str, phone: str) -> Dict[str, Any]:
        """
        Initiates the login flow for a specific store.
        1. Launches an isolated tab for the store.
        2. Navigates to Shopee login page.
        3. Fills in the phone number.
        4. Clicks continue / request OTP.
        """
        # Ensure Camofox uses store-specific isolation
        self.camofox.user_id = f"store_{store_id}"
        self.camofox.session_key = f"session_shopee_{store_id}"

        print(f"[{store_id}] Membuat tab browser terisolasi di Camofox...")
        tab_info = self.camofox.create_tab()
        tab_id = tab_info.get("tabId")

        print(f"[{store_id}] Membuka halaman login Shopee...")
        self.camofox.navigate(tab_id, url=self.LOGIN_URL)
        time.sleep(3)

        print(f"[{store_id}] Memasukkan nomor HP: {phone}...")
        # Common Shopee login input selectors: input[name="loginKey"] or input[type="text"]
        fill_script = f"""
        (() => {{
            const input = document.querySelector('input[name="loginKey"]') || 
                          document.querySelector('input[placeholder*="No. Handphone"]') ||
                          document.querySelector('input[placeholder*="Email"]') ||
                          document.querySelector('input[type="text"]');
            if (input) {{
                input.focus();
                const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeSetter.call(input, '{phone}');
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}
            return false;
        }})()
        """
        eval_res = self.camofox.evaluate(tab_id, fill_script)
        filled = eval_res.get("result", False)

        if not filled:
            # Fallback using Camofox selector
            try:
                self.camofox.type_text(tab_id, phone, selector='input[name="loginKey"]')
            except Exception:
                pass

        time.sleep(1)

        # Click the Login / Next button
        print(f"[{store_id}] Mengklik tombol Berikutnya / Log In...")
        click_script = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const target = btns.find(b => {
                const txt = (b.textContent || '').trim().toLowerCase();
                return txt.includes('log in') || txt.includes('berikutnya') || txt.includes('masuk');
            });
            if (target) {
                target.click();
                return true;
            }
            return false;
        })()
        """
        self.camofox.evaluate(tab_id, click_script)
        time.sleep(2)

        # Check if puzzle captcha appears and auto-solve via OpenCV Computer Vision!
        print(f"[{store_id}] Memeriksa puzzle captcha...")
        time.sleep(2)
        self.vision_solver.solve(tab_id)
        time.sleep(3)

        # Check if Shopee asks to choose OTP method (WhatsApp vs SMS)
        choose_sms_script = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, div, a'));
            const smsBtn = btns.find(b => (b.textContent || '').toLowerCase().includes('kirim sms') || (b.textContent || '').toLowerCase().includes('via sms'));
            if (smsBtn) {
                smsBtn.click();
                return 'SMS_CLICKED';
            }
            const waBtn = btns.find(b => (b.textContent || '').toLowerCase().includes('whatsapp'));
            if (waBtn) {
                waBtn.click();
                return 'WA_CLICKED';
            }
            return 'NO_METHOD_CHOICE';
        })()
        """
        method_res = self.camofox.evaluate(tab_id, choose_sms_script)

        # Take a screenshot so the user can visually verify
        screenshot_file = f"screenshots/{store_id}_shopee_login.png"
        self.camofox.save_screenshot(tab_id, screenshot_file)
        print(f"[{store_id}] Screenshot tersimpan: {screenshot_file}")

        # Take a snapshot to inspect status
        snapshot_data = self.camofox.snapshot(tab_id)
        snapshot_text = snapshot_data.get("snapshot", "")

        return {
            "success": True,
            "tab_id": tab_id,
            "otp_method": method_res.get("result"),
            "screenshot_path": screenshot_file,
            "snapshot_summary": snapshot_text[:250] if snapshot_text else "Tab aktif",
            "message": "Form login telah diisi. Shopee sedang mengirimkan kode OTP."
        }

    def submit_otp(self, tab_id: str, otp_code: str) -> Dict[str, Any]:
        """
        Fills the OTP digits and clicks verify.
        """
        otp_clean = "".join(filter(str.isdigit, str(otp_code)))
        print(f"Memasukkan kode OTP ({len(otp_clean)} digit)...")

        # Shopee OTP inputs are often 6 separate digit boxes or one single input
        otp_script = f"""
        (() => {{
            const code = "{otp_clean}";
            const inputs = Array.from(document.querySelectorAll('input[type="number"], input[inputmode="numeric"], input[autocomplete="one-time-code"], .shopee-pin-input input'));
            
            if (inputs.length >= 6) {{
                // Multi-box digit input
                for (let i = 0; i < 6 && i < code.length; i++) {{
                    inputs[i].focus();
                    inputs[i].value = code[i];
                    inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
                return "FILLED_BOXES";
            }} else {{
                // Single OTP input
                const singleInput = document.querySelector('input[placeholder*="Kode"], input[name="otp"]');
                if (singleInput) {{
                    singleInput.focus();
                    singleInput.value = code;
                    singleInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    singleInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return "FILLED_SINGLE";
                }}
            }}
            return "NO_OTP_FIELD_FOUND";
        }})()
        """
        fill_res = self.camofox.evaluate(tab_id, otp_script)
        time.sleep(1.5)

        # Click verify / lanjut button
        verify_script = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const target = btns.find(b => {
                const txt = (b.textContent || '').trim().toLowerCase();
                return txt.includes('lanjut') || txt.includes('verifikasi') || txt.includes('konfirmasi') || txt.includes('ok');
            });
            if (target) {
                target.click();
                return true;
            }
            return false;
        })()
        """
        self.camofox.evaluate(tab_id, verify_script)
        time.sleep(4)

        # Check current URL and check if login succeeded
        status_check = """
        (() => {
            const url = window.location.href;
            const isHomeOrDashboard = !url.includes('/buyer/login') && !url.includes('/verify');
            const hasUserAvatar = Boolean(document.querySelector('.navbar__username, .shopee-avatar, a[href*="/user/account"]'));
            return {
                url: url,
                is_logged_in: isHomeOrDashboard || hasUserAvatar
            };
        })()
        """
        check_res = self.camofox.evaluate(tab_id, status_check)
        login_info = check_res.get("result", {})

        return {
            "fill_status": fill_res.get("result"),
            "is_logged_in": login_info.get("is_logged_in", False),
            "current_url": login_info.get("url", "")
        }
