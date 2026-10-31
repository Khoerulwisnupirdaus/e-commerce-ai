import json
from typing import List, Dict, Any, Optional

class ShoppingRecommender:
    """
    Analyzes and compares products across stores/marketplaces to recommend
    the best deals based on price, rating, discounts, and seller reputation.
    """

    def __init__(self):
        pass

    def score_deal(self, product: Dict[str, Any]) -> float:
        """
        Calculates a deal score (0 to 100):
        - Lower price relative to market
        - Higher rating (4.8+ gets big boost)
        - High sales volume (terjual ribuan)
        - Active voucher discount percentage
        - Official / Star seller status
        """
        score = 50.0

        # Rating score (0 - 25 pts)
        rating = float(product.get("rating", 4.0))
        score += (rating - 3.5) * 20.0

        # Discount score (0 - 20 pts)
        discount_pct = float(product.get("discount_pct", 0))
        score += min(discount_pct * 0.4, 20.0)

        # Sales volume score (0 - 15 pts)
        sales = int(product.get("sales_count", 0))
        if sales > 1000:
            score += 15.0
        elif sales > 100:
            score += 10.0
        elif sales > 10:
            score += 5.0

        # Seller badge bonus
        seller_type = str(product.get("seller_type", "")).lower()
        if "mall" in seller_type or "official" in seller_type:
            score += 10.0
        elif "star" in seller_type or "power" in seller_type:
            score += 5.0

        return round(min(max(score, 0.0), 100.0), 1)

    def rank_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank products by deal score and price efficiency."""
        for p in products:
            p["deal_score"] = self.score_deal(p)

        # Sort by deal_score descending, then price ascending
        return sorted(products, key=lambda x: (-x["deal_score"], x.get("price", 999999999)))

    def generate_recommendation_summary(self, keyword: str, ranked_products: List[Dict[str, Any]]) -> str:
        """Generates a human-friendly executive summary for the business owner."""
        if not ranked_products:
            return f"Tidak ditemukan produk untuk kata kunci '{keyword}'."

        best = ranked_products[0]
        summary = []
        summary.append(f"=== REKOMENDASI BELANJA TERBAIK: '{keyword.upper()}' ===")
        summary.append(f"🏆 Pilihan Terbaik: {best.get('title', 'Produk')}")
        summary.append(f"   Harga      : Rp {best.get('price', 0):,}")
        summary.append(f"   Skor Deal  : {best.get('deal_score')}/100")
        summary.append(f"   Toko       : {best.get('shop_name', '-')} ({best.get('seller_type', 'Reguler')})")
        summary.append(f"   Rating     : ⭐ {best.get('rating', '-')} ({best.get('sales_count', 0)} terjual)")
        summary.append(f"   Alasan     : {best.get('recommendation_reason', 'Kombinasi harga terbaik dan reputasi toko terpercaya.')}\n")

        summary.append("Alternative 2-3 Pilihan Lainnya:")
        for i, alt in enumerate(ranked_products[1:4], 2):
            summary.append(f"{i}. {alt.get('title', '')[:40]}... - Rp {alt.get('price', 0):,} (Skor: {alt.get('deal_score')})")

        return "\n".join(summary)
