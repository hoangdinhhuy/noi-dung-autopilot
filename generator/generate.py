# -*- coding: utf-8 -*-
"""
Bot nội dung hàng ngày cho người bán TikTok Shop / Shopee VN.
Chạy trong GitHub Actions cron mỗi ngày, viết 1 gói nội dung mới vào content/.

- Không có GEMINI_API_KEY: dùng bộ mẫu determinstic (seed theo ngày) — miễn phí vĩnh viễn.
- Có GEMINI_API_KEY (secret trong repo): gọi Gemini flash để viết lại script chất lượng cao hơn.
  Lỗi API tự rơi về bộ mẫu, cron không bao giờ fail vì LLM.

Chỉ dùng thư viện chuẩn Python.
"""
import json
import os
import random
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "niches.json"
OUT = ROOT / "content"

# ---- Bộ mẫu (stdlib-only engine) ------------------------------------------

HOOKS = [
    "Dừng lại 3 giây nếu bạn cũng {noi_dau}!",
    "Mình đã mất {so_tien} vì {noi_dau} — cho đến khi tìm ra món này.",
    "Ai đang {noi_dau} thì xem hết video này, đừng bỏ lỡ!",
    "Đây là lý do {san_pham} đang cháy hàng trên TikTok Shop.",
    "Review thật sau 7 ngày dùng {san_pham}: kết quả ngoài dự đoán.",
    "3 giây đầu mà lướt qua là bạn bỏ lỡ món {san_pham} này đấy.",
    "Mình không tin luôn, nhưng {san_pham} này thật sự đáng đồng tiền.",
    "Bạn bè mình cứ hỏi mình mua {san_pham} ở đâu — thôi thì chia sẻ hết đây.",
]

NOI_DAU_CUM = [
    "chịu đựng {noi_dau} mỗi ngày",
    "ngại ngùng mỗi khi {noi_dau}",
    "tốn bao nhiêu tiền vì {noi_dau}",
]

GIAI_PHAP = [
    "Mình tìm được {san_pham} — dùng thử 1 tuần là thấy khác ngay.",
    "Cứ tưởng là trà trộn, ai ngờ {san_pham} này dùng thật sự ổn áp.",
    "Chốt luôn món {san_pham}: đúng cái mình cần, giá lại vừa túi sinh viên.",
    "{san_pham} là món mình lười review nhất mà lại được hỏi nhiều nhất.",
]

TAO_TIN_CAY = [
    "Shop có phòng chống giả, mình check mã trước khi dùng — dùng mới dám quay video này.",
    "Video quay thật 100%, không cắt ghép phần test — bạn tự xem mà đánh giá.",
    "Lưu ý nho nhỏ: {loi_khuyen} thì trải nghiệm sẽ rõ hơn nhiều.",
    "Cỡ 2000+ đơn đã bán rồi mình mới dám mua, giờ chia sẻ lại cho bạn nào cần.",
]

CTA = [
    "Link mua mình để ngay giỏ hàng TikTok, giá hôm nay có voucher nữa!",
    "Bấm vào giỏ hàng màu vàng bên cạnh, mình chọn size nào trong phần comment nha!",
    "Săn deal hôm nay ở giỏ hàng — hết voucher thì đừng tiếc nhé!",
    "Cần thì bấm giỏ hàng, không cần thì lưu lại để mai cần còn tìm.",
]

HASHTAG_CHUNG = ["xuhuong", "reviewchanthat", "tiktokshop", "giaredep", "sanhanghieutoday"]

# ---- LLM tuỳ chọn ---------------------------------------------------------

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key={key}"
)


def gemini_viet_lai(niche: dict, script_mau: dict) -> dict | None:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    prompt = (
        "Bạn là copywriter TikTok Shop Việt Nam. Viết lại script video ngắn "
        "(30-45 giây) bằng tiếng Việt tự nhiên, giọng người bán trẻ, KHÔNG viết "
        "kiểu quảng cáo sến. Chỉ trả về JSON đúng schema sau, không thêm chữ nào:\n"
        '{"hook": "...", "noi_dau": "...", "giai_phap": "...", "tao_tin_cay": "...", '
        '"cta": "...", "caption": "...", "hashtags": ["...", "..."]}\n\n'
        f"Sản phẩm: {niche['san_pham']}\nNgách: {niche['ten']}\n"
        f"Khán giả: {niche['khan_gia']}\nNỗi đau: {niche['noi_dau']}\n"
        f"Lời khuyên quay: {niche['loi_khuyen']}\n\n"
        f"Bản mẫu để cải thiện: {json.dumps(script_mau, ensure_ascii=False)}"
    )
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(
        GEMINI_URL.format(key=key),
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            text = json.load(r)["candidates"][0]["content"]["parts"][0]["text"]
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        out = json.loads(text)
        return out if isinstance(out, dict) and "hook" in out else None
    except Exception as e:  # rơi về bộ mẫu, cron không chết vì LLM
        print(f"[warn] Gemini fallback sang bộ mẫu: {e}")
        return None


# ---- Sinh gói nội dung ----------------------------------------------------

def tao_bai(niche: dict, rng: random.Random, dung_llm: bool) -> dict:
    pham = niche["san_pham"]
    mau = {
        "hook": rng.choice(HOOKS).format(san_pham=pham, noi_dau=niche["noi_dau"], so_tien="500k"),
        "noi_dau": rng.choice(NOI_DAU_CUM).format(noi_dau=niche["noi_dau"]),
        "giai_phap": rng.choice(GIAI_PHAP).format(san_pham=pham),
        "tao_tin_cay": rng.choice(TAO_TIN_CAY).format(loi_khuyen=niche["loi_khuyen"]),
        "cta": rng.choice(CTA),
        "caption": "",
        "hashtags": [],
    }
    caption = f"{mau['hook']} {mau['giai_phap']} {mau['cta']}"
    tags = [t.lstrip("#") for t in niche["tu_khoa"]] + rng.sample(HASHTAG_CHUNG, 3)
    mau["caption"] = caption[:250].strip() + ("…" if len(caption) > 250 else "")
    mau["hashtags"] = ["#" + t for t in tags]

    if dung_llm:
        better = gemini_viet_lai(niche, mau)
        if better:
            for k in ("hook", "noi_dau", "giai_phap", "tao_tin_cay", "cta", "caption", "hashtags"):
                if better.get(k):
                    mau[k] = better[k]
            mau["nguon"] = "gemini"
    mau.setdefault("nguon", "mau")
    mau["ngach"] = niche["ten"]
    mau["san_pham"] = pham
    mau["khuyen_quay"] = niche["loi_khuyen"]
    mau["khung"] = ["HOOK(0-3s)", "NỖI ĐAU(3-8s)", "GIẢI PHÁP+DEMO(8-25s)", "TẠO TIN CẬY(25-35s)", "CTA(35-45s)"]
    return mau


def sinh_goi(ngay: str) -> dict:
    data = json.load(open(DATA, encoding="utf-8"))
    niches = data["niches"]
    rng = random.Random(ngay)  # seed theo ngày: cùng ngày → cùng kết quả
    picked = rng.sample(niches, 3)
    dung_llm = bool(os.environ.get("GEMINI_API_KEY"))
    bai = [tao_bai(n, rng, dung_llm) for n in picked]
    return {
        "ngay": ngay,
        "tao_boi": "gemini" if dung_llm else "bo-mau",
        "bai": bai,
    }


def main():
    ngay = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    OUT.mkdir(exist_ok=True)

    goi = sinh_goi(ngay)
    (OUT / f"{ngay}.json").write_text(
        json.dumps(goi, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    idx_path = OUT / "index.json"
    ds = []
    if idx_path.exists():
        ds = json.load(open(idx_path, encoding="utf-8"))
    if ngay not in ds:
        ds.append(ngay)
    ds.sort(reverse=True)
    idx_path.write_text(json.dumps(ds, ensure_ascii=False), encoding="utf-8")

    print(f"OK: gói {ngay} — {len(goi['bai'])} bài, nguồn: {goi['tao_boi']}, tổng {len(ds)} gói")


if __name__ == "__main__":
    main()
