import time
from typing import Dict, Any, Optional
from core.camofox import CamofoxClient
from core.vision_solver import OpenCVCanvasSolver

class ShopeeRegisterHandler:
    """Handles Shopee Account Registration via Camofox stealth engine."""

    SIGNUP_URL = "https://shopee.co.id/buyer/signup"

    def __init__(self, camofox: CamofoxClient):
        self.camofox = camofox
        self.vision_solver = OpenCVCanvasSolver(camofox)

    def start_registration(self, store_id: str, phone: str) -> Dict[str, Any]:
        """
        1. Opens an isolated tab for this specific store.
        2. Navigates to Shopee buyer signup page.
        3. Fills in the phone number.
        4. Clicks Berikutnya / Submit.
        5. Handles language modal or slider puzzle if they appear.
        6. Reaches the OTP input screen.
        """
        self.camofox.user_id = f"store_{store_id}"
        self.camofox.session_key = f"session_reg_{store_id}"

        print(f"[{store_id}] 1. Membuat tab browser terisolasi di Camofox...")
        tab_info = self.camofox.create_tab()
        tab_id = tab_info.get("tabId")

        print(f"[{store_id}] 2. Membuka halaman pendaftaran resmi Shopee...")
        self.camofox.navigate(tab_id, url=self.SIGNUP_URL)
        time.sleep(3)

        # Handle language modal if present
        dismiss_lang_script = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const setuju = btns.find(b => (b.innerText || '').trim().toLowerCase() === 'setuju');
            if (setuju) {
                setuju.click();
                return true;
            }
            return false;
        })()
        """
        self.camofox.evaluate(tab_id, dismiss_lang_script)
        time.sleep(1)

        print(f"[{store_id}] 3. Mengetikkan nomor HP {phone}...")
        fill_react_script = f"""
        (() => {{
            const input = document.querySelector('input[type="text"]') || 
                          document.querySelector('input[type="tel"]') ||
                          document.querySelector('input[placeholder*="Telepon"]') ||
                          document.querySelector('input');
            if (!input) return false;
            input.focus();
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            nativeSetter.call(input, '{phone}');
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return true;
        }})()
        """
        filled = self.camofox.evaluate(tab_id, fill_react_script).get("result", False)
        if not filled:
            self.camofox.type_text(tab_id, phone, selector='input[type="text"], input[placeholder*="Telepon"]')
        time.sleep(1.5)

        print(f"[{store_id}] 4. Mengklik tombol 'Berikutnya'...")
        click_btn_script = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const btn = btns.find(b => {
                const txt = (b.innerText || '').toLowerCase().trim();
                return txt.includes('berikutnya') || txt.includes('lanjut') || txt.includes('daftar');
            });
            if (btn) {
                btn.removeAttribute('disabled');
                btn.click();
                return true;
            }
            return false;
        })()
        """
        clicked = self.camofox.evaluate(tab_id, click_btn_script).get("result", False)
        if not clicked:
            self.camofox.click(tab_id, selector='button:not([disabled])')

        time.sleep(3)

        # Check if slider puzzle appears and solve via OpenCV Computer Vision
        print(f"[{store_id}] 5. Memeriksa puzzle captcha...")
        time.sleep(2)
        self.vision_solver.solve(tab_id)
        time.sleep(3)

        # Check if Shopee asks to choose verification method (WhatsApp vs SMS)
        choose_method_script = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, div, a'));
            const waBtn = btns.find(b => (b.innerText || '').toLowerCase().includes('whatsapp'));
            if (waBtn) {
                waBtn.click();
                return 'WHATSAPP';
            }
            const smsBtn = btns.find(b => (b.innerText || '').toLowerCase().includes('sms'));
            if (smsBtn) {
                smsBtn.click();
                return 'SMS';
            }
            return 'AUTO_DISPATCH';
        })()
        """
        method_res = self.camofox.evaluate(tab_id, choose_method_script)
        time.sleep(2)

        # Take screenshot of the OTP waiting screen
        screenshot_path = f"screenshots/{store_id}_waiting_otp.png"
        self.camofox.save_screenshot(tab_id, screenshot_path)

        return {
            "success": True,
            "tab_id": tab_id,
            "method": method_res.get("result"),
            "screenshot": screenshot_path,
            "message": f"Pendaftaran diproses. Menunggu kode OTP untuk {phone}."
        }

    def submit_otp(self, tab_id: str, otp_code: str) -> Dict[str, Any]:
        """
        Inputs the received OTP digits and finalizes registration.
        """
        otp_digits = "".join(filter(str.isdigit, str(otp_code)))
        print(f"Memasukkan kode OTP ({otp_digits}) ke form Shopee...")

        otp_script = f"""
        (() => {{
            const code = "{otp_digits}";
            const inputs = Array.from(document.querySelectorAll('input[type="number"], input[inputmode="numeric"], input[autocomplete="one-time-code"], .shopee-pin-input input'));
            
            if (inputs.length >= 6) {{
                for (let i = 0; i < 6 && i < code.length; i++) {{
                    inputs[i].focus();
                    inputs[i].value = code[i];
                    inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
                return "FILLED_BOXES";
            }} else {{
                const single = document.querySelector('input[placeholder*="Kode"], input[name="otp"], input[type="text"]');
                if (single) {{
                    single.focus();
                    single.value = code;
                    single.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    single.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return "FILLED_SINGLE";
                }}
            }}
            return "NO_INPUT";
        }})()
        """
        res_fill = self.camofox.evaluate(tab_id, otp_script)
        time.sleep(1.5)

        # Click submit / konfirmasi / lanjut
        verify_script = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const btn = btns.find(b => {
                const t = (b.innerText || '').toLowerCase();
                return t.includes('lanjut') || t.includes('verifikasi') || t.includes('konfirmasi') || t.includes('ok');
            });
            if (btn) {
                btn.click();
                return true;
            }
            return false;
        })()
        """
        self.camofox.evaluate(tab_id, verify_script)
        time.sleep(3)

        # Check final registration status
        check_script = """
        (() => {
            const url = window.location.href;
            const isSuccess = !url.includes('/verify/otp') && !url.includes('/buyer/signup');
            return {
                url: url,
                is_registered: isSuccess
            };
        })()
        """
        status_res = self.camofox.evaluate(tab_id, check_script)
        return {
            "fill_status": res_fill.get("result"),
            "result": status_res.get("result", {})
        }
