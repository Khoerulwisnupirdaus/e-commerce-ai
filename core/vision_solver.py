import base64
import cv2
import numpy as np
import time
from typing import Tuple, Optional, Dict, Any, List
from core.camofox import CamofoxClient

class OpenCVCanvasSolver:
    """
    Local Computer Vision Puzzle Captcha Solver for Shopee/Marketplaces.
    Uses Dark Basin Profile + Sobel Vertical Gradient + Alpha Offset Calibration.
    Integrates with Camofox hardware-level Humanized Drag (Bézier S-Curve).
    """

    def __init__(self, camofox: CamofoxClient):
        self.camofox = camofox

    def has_puzzle(self, tab_id: str) -> bool:
        """Check if puzzle captcha is active on screen."""
        script = """
        (() => {
            const canvases = document.querySelectorAll('canvas').length >= 2;
            const slider = !!(document.querySelector('.dExCsf') || document.querySelector('[class*="slider"]'));
            return canvases && slider;
        })()
        """
        try:
            res = self.camofox.evaluate(tab_id, script)
            return bool(res.get("result"))
        except Exception:
            return False

    def extract_canvas_images(self, tab_id: str) -> Optional[Dict[str, Any]]:
        """Extracts background, piece canvas images, and exact DOM layout dimensions."""
        script = """
        (() => {
            const bg = document.querySelector('canvas.EkGpDI') || document.querySelectorAll('canvas')[0];
            const piece = document.querySelector('canvas._0N0-Dn') || document.querySelectorAll('canvas')[1];
            const handle = document.querySelector('.dExCsf') || document.querySelector('[class*="slider"]');
            
            if (!bg || !piece || !handle) return null;
            
            const bgRect = bg.getBoundingClientRect();
            const pieceRect = piece.getBoundingClientRect();
            const handleRect = handle.getBoundingClientRect();
            const relY = pieceRect.top - bgRect.top;
            
            return {
                bgData: bg.toDataURL('image/png'),
                pieceData: piece.toDataURL('image/png'),
                relY: relY,
                bgWidth: bgRect.width,
                bgHeight: bgRect.height,
                pieceWidth: pieceRect.width,
                pieceHeight: pieceRect.height,
                handleRect: {
                    x: handleRect.x,
                    y: handleRect.y,
                    width: handleRect.width,
                    height: handleRect.height
                }
            };
        })()
        """
        try:
            res = self.camofox.evaluate(tab_id, script)
            return res.get("result")
        except Exception as e:
            print(f"[VisionSolver] Gagal ekstrak canvas: {e}")
            return None

    def find_gap_offset(self, bg_b64: str, piece_b64: str, rel_y: float = 40.0) -> Tuple[int, int, int]:
        """
        Calculates the exact X coordinate where the puzzle piece fits.
        Uses Dark Basin profiling + Sobel Edge Jump + Alpha Cutout Margin calibration.
        Returns (target_drag_x, best_hole_x, xmin).
        """
        bg_bytes = base64.b64decode(bg_b64.split(",")[-1])
        piece_bytes = base64.b64decode(piece_b64.split(",")[-1])

        bg_arr = np.frombuffer(bg_bytes, np.uint8)
        piece_arr = np.frombuffer(piece_bytes, np.uint8)

        bg_img = cv2.imdecode(bg_arr, cv2.IMREAD_COLOR)
        piece_img = cv2.imdecode(piece_arr, cv2.IMREAD_UNCHANGED)

        # 1. Analyze alpha channel of the puzzle piece to find bounds (xmin, xmax, pw, ph)
        if piece_img.shape[2] == 4:
            alpha = piece_img[:, :, 3]
            y_idx, x_idx = np.where(alpha > 120)
            if len(x_idx) > 0 and len(y_idx) > 0:
                ymin, ymax = y_idx.min(), y_idx.max()
                xmin, xmax = x_idx.min(), x_idx.max()
            else:
                ymin, ymax, xmin, xmax = 0, piece_img.shape[0] - 1, 0, piece_img.shape[1] - 1
        else:
            ymin, ymax, xmin, xmax = 0, piece_img.shape[0] - 1, 0, piece_img.shape[1] - 1

        pw = max(15, xmax - xmin + 1)
        ph = max(15, ymax - ymin + 1)
        int_rel_y = max(0, min(bg_img.shape[0] - ph, int(round(rel_y))))

        # 2. Extract horizontal band from background at the exact puzzle height
        gray = cv2.cvtColor(bg_img, cv2.COLOR_BGR2GRAY)
        band = gray[int_rel_y : int_rel_y + ph, :]
        col_means = np.mean(band, axis=0)

        # 3. Dark Basin contrast scoring (Shopee puzzle holes are dark silhouettes)
        # Search range from 45px to width - pw - 10px
        max_search_x = max(50, bg_img.shape[1] - pw - 10)
        basin_scores = []
        for x in range(45, max_search_x):
            pre = np.mean(col_means[max(0, x - 12) : x])
            inside = np.mean(col_means[x : x + pw])
            post = np.mean(col_means[x + pw : min(bg_img.shape[1], x + pw + 12)])
            contrast = ((pre + post) / 2.0) - inside
            basin_scores.append((x, contrast))

        if not basin_scores:
            return 110, 110, 0

        basin_scores.sort(key=lambda item: item[1], reverse=True)
        top_basin_x = basin_scores[0][0]

        # 4. Refine with Sobel vertical edge jump around the basin
        hole_inner = gray[int_rel_y + 3 : int_rel_y + ph - 3, :]
        sobel_x = cv2.Sobel(hole_inner, cv2.CV_64F, 1, 0, ksize=3)
        edge_profile = np.mean(np.abs(sobel_x), axis=0)

        local_window = edge_profile[max(40, top_basin_x - 6) : min(bg_img.shape[1] - 10, top_basin_x + 7)]
        if len(local_window) > 0:
            local_peak_offset = np.argmax(local_window)
            best_edge_x = max(40, top_basin_x - 6) + local_peak_offset
        else:
            best_edge_x = top_basin_x

        # 5. Subtract alpha transparent margin (xmin) for exact drag alignment
        target_drag_x = int(best_edge_x - xmin)
        print(f"[VisionSolver] Lubang terdeteksi: Basin X={top_basin_x}, Tepi Presisi X={best_edge_x}, Margin Xmin={xmin} -> Drag={target_drag_x}px")
        return target_drag_x, int(best_edge_x), int(xmin)

    def solve(self, tab_id: str, max_retries: int = 5) -> bool:
        """
        Executes autonomous detection and Humanized Drag solver.
        Includes auto-retry loop with micro-calibrations if challenge repeats.
        """
        offsets = [0, 2, -2, 4, -3]

        for attempt in range(1, max_retries + 1):
            if not self.has_puzzle(tab_id):
                print("[VisionSolver] Tidak ada puzzle captcha di layar.")
                return True

            print(f"\n[VisionSolver] === Mencoba menyelesaikan puzzle captcha (Percobaan {attempt}/{max_retries}) ===")
            canvas_info = self.extract_canvas_images(tab_id)
            if not canvas_info or not canvas_info.get("bgData"):
                print("[VisionSolver] Gagal membaca gambar canvas. Menunggu...")
                time.sleep(1.5)
                continue

            rel_y = canvas_info.get("relY", 40.0)
            target_x, best_hole_x, xmin = self.find_gap_offset(
                canvas_info["bgData"],
                canvas_info["pieceData"],
                rel_y
            )

            # Apply attempt offset for multi-pass calibration
            cur_offset = offsets[(attempt - 1) % len(offsets)]
            calibrated_target_x = max(20, target_x + cur_offset)

            print(f"[VisionSolver] Menggerakkan slider dengan Humanized Bézier Curve (Target: {calibrated_target_x}px, offset: {cur_offset:+d}px)...")
            try:
                drag_res = self.camofox.drag(
                    tab_id,
                    selector=".dExCsf",
                    distance_x=calibrated_target_x
                )
                print(f"[VisionSolver] Drag selesai dieksekusi: {drag_res.get('steps', 0)} steps.")
            except Exception as e:
                print(f"[VisionSolver] Error saat request drag: {e}")

            time.sleep(3.5)

            # Check if captcha passed
            outcome = self.check_verification_success(tab_id)
            if outcome.get("success"):
                print("\n🎉 [VisionSolver] CAPTCHA BERHASIL DILEWATI SECARA OTOMATIS!")
                return True
            else:
                print(f"[VisionSolver] Percobaan {attempt} belum lolos. Menunggu puzzle baru...")
                time.sleep(1.5)

        print("[VisionSolver] Maksimal percobaan tercapai.")
        return False

    def check_verification_success(self, tab_id: str) -> Dict[str, Any]:
        """Checks whether verification succeeded (canvases gone, OTP input visible, etc)."""
        check_script = """
        (() => {
            const canvases = document.querySelectorAll('canvas').length;
            const slider = !!(document.querySelector('.dExCsf') || document.querySelector('[class*="slider"]'));
            const otpInput = !!(document.querySelector('input[type="tel"]') || 
                                document.querySelector('input[autocomplete="one-time-code"]') || 
                                document.querySelector('input[maxlength="6"]') ||
                                document.querySelector('.shopee-pin-input'));
            const isSuccess = (canvases === 0 && !slider) || otpInput;
            return {
                canvases,
                slider,
                otpInput,
                success: isSuccess
            };
        })()
        """
        try:
            res = self.camofox.evaluate(tab_id, check_script)
            return res.get("result", {})
        except Exception:
            return {"success": False}
