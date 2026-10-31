import time
from core.camofox import CamofoxClient
from core.vision_solver import OpenCVCanvasSolver

class ShopeeSliderSolver:
    """
    Automated Slider Puzzle Captcha Solver for Shopee.
    Delegates to OpenCVCanvasSolver with Humanized Bézier Curve trajectory.
    """

    def __init__(self, camofox: CamofoxClient):
        self.camofox = camofox
        self.solver = OpenCVCanvasSolver(camofox)

    def has_puzzle(self, tab_id: str) -> bool:
        """Check if puzzle captcha is currently displayed."""
        return self.solver.has_puzzle(tab_id)

    def solve(self, tab_id: str) -> bool:
        """Analyze puzzle canvas, calculate distance, and drag slider handle naturally."""
        return self.solver.solve(tab_id)
