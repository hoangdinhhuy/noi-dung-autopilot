# -*- coding: utf-8 -*-
"""
Kill-switch tự động cho Chợ Nội Dung — chạy hàng tuần trong GitHub Actions.

Hai điều kiện tự đóng dự án (cái nào đến trước):
1. HẾT NGÂN SÁCH DUY TRÌ: von_ban_dau + doanh_thu_tich_luy - chi_phi_tich_luy < 0.
   (Mặc định chi phí 0đ/tháng → nhánh này không bao giờ kích hoạt trừ khi
   bạn nâng cấp lên dịch vụ trả phí và ghi lại chi phí trong config/sustain.json)
2. KHÔNG CÒN NGƯỜI DÙNG: số người dùng duy nhất/tuần < ngưỡng, lặp lại liên
   tiếp quá số tuần cho phép → dự án vô nghĩa, tự đóng để không chạy vô ích.

Khi tự đóng: trang chủ đổi thành trang tạm biệt, cron sinh nội dung bị tắt,
một issue được tạo để báo cho chủ repo (GitHub gửi email), workflow này cũng
tự tắt. Mọi thứ vẫn nằm trong git history — mở lại được bất cứ lúc nào.

Chỉ dùng stdlib. Biến môi trường cần: GH_TOKEN (hoặc GITHUB_TOKEN),
GITHUB_REPOSITORY (Actions tự set).
"""
import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG_PATH = ROOT / "config" / "sustain.json"
LOG_PATH = ROOT / "config" / "vitality_log.jsonl"

TOKEN = (os.environ.get("GH_PAT") or os.environ.get("GH_TOKEN")
         or os.environ.get("GITHUB_TOKEN"))
REPO = os.environ.get("GITHUB_REPOSITORY", "hoangdinhhuy/noi-dung-autopilot")
API = f"https://api.github.com/repos/{REPO}"


def api(path: str, method: str = "GET", payload: dict | None = None):
    if payload is not None:
        data = json.dumps(payload).encode()
    elif method == "PUT":
        data = b""
    else:
        data = None
    req = urllib.request.Request(
        f"{API}/{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "sustain-bot",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
    return json.loads(body) if body else {}


def doc_nguoi_dung_7ngay() -> int:
    """Số người dùng duy nhất trong 7 ngày gần nhất (GitHub traffic)."""
    try:
        views = api("traffic/views")["views"]
        days = {v["timestamp"][:10]: v["uniques"] for v in views}
        tuan = sorted(days)[-7:]
        return sum(days[d] for d in tuan)
    except Exception as e:
        print(f"[warn] không đọc được traffic: {e}")
        return -1  # không có dữ liệu → không tính là tuần tốt, cũng không crash


def tuan_kem_lien_tiep() -> int:
    if not LOG_PATH.exists():
        return 0
    lines = [json.loads(l) for l in LOG_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    # Gộp theo ngày (kết quả cuối của mỗi ngày thắng) — chạy tay nhiều lần
    # trong một ngày không được đếm thành nhiều tuần kém ảo.
    theo_ngay: dict[str, str] = {}
    for dong in lines:
        theo_ngay[dong["ngay"]] = dong["ket_qua_tuan"]
    dem = 0
    for ket_qua in reversed(list(theo_ngay.values())):
        if ket_qua == "kem":
            dem += 1
        else:
            break
    return dem


def dong_du_an(cfg: dict, ly_do: str):
    cfg["trang_thai"] = "da_dong"
    cfg["ngay_dong"] = date.today().isoformat()
    CFG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    # Đổi trang chủ thành trang tạm biệt (bản cũ nằm trong git history)
    (ROOT / "index.html").write_text(
        (ROOT / "goodbye.html").read_text(encoding="utf-8"), encoding="utf-8"
    )

    # Tắt cron sinh nội dung + tắt chính workflow này
    for wf in ("daily.yml", "healthcheck.yml"):
        try:
            api(f"actions/workflows/{wf}/disable", method="PUT")
        except Exception as e:
            print(f"[warn] không tắt được {wf}: {e}")

    body = (
        "🛑 **Dự án Chợ Nội Dung đã TỰ ĐÓNG** — quyết định tự động, không ai bấm.\n\n"
        f"**Lý do:** {ly_do}\n\n"
        "**Đã làm:** trang chủ đổi thành trang tạm biệt, cron sinh nội dung tắt, "
        "workflow giám sát tắt. Toàn bộ lịch sử còn nguyên trong git.\n\n"
        "**Muốn mở lại:**\n"
        "1. Actions tab → enable lại `Sinh nội dung mỗi ngày` và `Giám sát sống còn`\n"
        "2. `git revert` commit đóng dự án gần nhất (khôi phục index.html + sustain.json)\n"
        "3. Sửa `trang_thai` trong `config/sustain.json` về `dang_chay`\n\n"
        "— bot tự viết báo cáo này."
    )
    try:
        api("issues", method="POST", payload={
            "title": f"🛑 Dự án tự đóng ngày {date.today().isoformat()}",
            "body": body,
            "labels": ["auto-sunset"],
        })
    except Exception as e:
        print(f"[warn] không tạo được issue: {e}")


def main():
    if not TOKEN:
        sys.exit("Thiếu GH_TOKEN/GITHUB_TOKEN")
    cfg = json.loads(CFG_PATH.read_text(encoding="utf-8"))
    if cfg.get("trang_thai") != "dang_chay":
        print("Dự án đã đóng từ trước, không chạy giám sát.")
        return

    hom_nay = date.today().isoformat()

    # --- Chỉ số 1: người dùng thật ---
    uniques = doc_nguoi_dung_7ngay()
    nguong = cfg["nguong_nguoi_dung_toi_thieu_tuan"]
    # Fail-safe: KHÔNG đọc được traffic cũng tính là tuần kém — nếu tính là "đạt"
    # thì khi API lỗi mãi, kill-switch sẽ không bao giờ cài được.
    kem = uniques == -1 or uniques < nguong
    nhan = {True: "KÉM", False: "đạt"}[kem]
    print(f"Người dùng duy nhất 7 ngày: {uniques} (ngưỡng {nguong}) → {nhan}")

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ngay": hom_nay,
            "nguoi_dung_7ngay": uniques,
            "ket_qua_tuan": "kem" if kem else "dat",
        }, ensure_ascii=False) + "\n")

    # --- Chỉ số 2: ngân sách duy trì ---
    bat_dau = date.fromisoformat(cfg["ngay_bat_dau"])
    so_thang = max(0, (date.today() - bat_dau).days // 30)
    chi_phi = cfg["phi_du_tri_moi_thang_vnd"] * so_thang
    du_lieu = cfg["von_ban_dau_vnd"] + cfg["doanh_thu_tich_luy_vnd"] - chi_phi
    print(f"Ngân sách còn lại (tính): {du_lieu:,}đ sau {so_thang} tháng")

    # --- Quyết định ---
    if du_lieu < 0:
        dong_du_an(cfg, f"Hết ngân sách duy trì: còn {du_lieu:,}đ "
                       f"(vốn {cfg['von_ban_dau_vnd']:,}đ + doanh thu {cfg['doanh_thu_tich_luy_vnd']:,}đ "
                       f"- chi phí {chi_phi:,}đ).")
        print("SUNSET: hết ngân sách")
        return

    kem_lien_tiep = tuan_kem_lien_tiep()
    gioi_han = cfg["so_tuan_lien_tiep_duoc_phep"]
    if kem_lien_tiep >= gioi_han:
        dong_du_an(cfg, f"Không còn người dùng: {kem_lien_tiep} tuần liên tiếp dưới ngưỡng "
                       f"{nguong} người/tuần (giới hạn {gioi_han} tuần).")
        print(f"SUNSET: {kem_lien_tiep} tuần liên tiếp không có người dùng")
        return

    print(f"OK: dự án sống. Tuần kém liên tiếp: {kem_lien_tiep}/{gioi_han}")


if __name__ == "__main__":
    main()
