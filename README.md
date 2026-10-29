# Chợ Nội Dung 🛒

Bot AI tự sinh **nội dung bán hàng mỗi ngày** cho người bán nhỏ trên TikTok Shop & Shopee Việt Nam — chạy hoàn toàn tự động, **chi phí vận hành 0đ/tháng**.

**Trang chủ:** `https://hoangdinhhuy.github.io/noi-dung-autopilot/` (bật sau khi deploy)

## Nó làm gì

Mỗi ngày lúc **8:30 sáng (giờ VN)**, GitHub Actions chạy bot:

1. Bot chọn ngẫu nhiên (theo ngày) **3 ngách** trong 12 ngách bán hàng đã nghiên cứu.
2. Với mỗi ngách, bot viết **1 kịch bản video TikTok 30–45s** đầy đủ khung
   `Hook → Nỗi đau → Giải pháp + Demo → Tạo tin cậy → CTA`, kèm caption + hashtag
   + mẹo quay video cho người bán.
3. Gói nội dung được commit vào `content/`, site tĩnh trên GitHub Pages tự cập nhật.
4. Người bán vào trang, copy kịch bản, quay theo khung gợi ý, đăng.

## Chất lượng nội dung

- **Không API key (mặc định):** bộ mẫu tiếng Việt được viết sẵn theo công thức
  viral TikTok Shop, luân phiên determinstic theo ngày — miễn phí vĩnh viễn.
- **Có `GEMINI_API_KEY`** (repo secret): Gemini 2.0 Flash viết lại từng script
  theo đúng sản phẩm/khán giả của ngách — vẫn miễn phí trong free tier. Lỗi API
  tự fallback về bộ mẫu, cron không bao giờ chết vì LLM.

## Chạy tay

```bash
python generator/generate.py            # gói hôm nay
python generator/generate.py 2026-10-29 # gói ngày bất kỳ
```

Chỉ dùng thư viện chuẩn Python, không cần cài gì.

## Kiếm tiền (theo lớp)

1. **Affiliate** — nhúng link Shopee/TikTok affiliate vào trang (đăng ký miễn phí).
2. **Ủng hộ** — QR chuyển khoản cho người được bot giúp có đơn đầu tiên.
3. **Gói Pro 99k** — kho nội dung 30 ngày viết riêng theo sản phẩm (mở khi có 1.000 người dùng/tháng).

## Tự giám sát & tự đóng (kill-switch)

Workflow **Giám sát sống còn** chạy 9:30 sáng thứ Hai hàng tuần (`generator/healthcheck.py`):

- **Đo người dùng thật**: số người truy cập duy nhất 7 ngày qua (GitHub traffic API, cần secret `GH_PAT` — PAT cá nhân có scope `repo`; thiếu PAT thì tuần đó tính KÉM theo fail-safe).
- **Đo ngân sách duy trì**: `vốn + doanh thu tích lũy - chi phí × số tháng` ghi trong `config/sustain.json`.
- **Tự đóng khi**: ngân sách < 0đ, hoặc ≤ 20 người dùng/tuần kéo dài 8 tuần liên tiếp (đếm theo ngày phân biệt — chạy tay nhiều lần không đếm ảo).
- **Khi tự đóng**: trang chủ đổi thành trang tạm biệt (`goodbye.html`), tắt cron sinh nội dung + tắt workflow giám sát, tạo issue "🛑 Dự án tự đóng" gửi email cho chủ repo. Nhật ký sức khoẻ lưu tại `config/vitality_log.jsonl`.
- **Mở lại**: bật lại 2 workflow trong tab Actions, `git revert` commit đóng dự án, đặt `trang_thai: dang_chay` trong `config/sustain.json`.

Nguyên tắc: mọi hạ tầng đều dùng bậc miễn phí vĩnh viễn → bot **không thể "cháy" vốn**;

## Cấu trúc

```
data/niches.json        # 12 ngách bán hàng (khán giả, nỗi đau, hashtag, mẹo quay)
generator/generate.py   # bot sinh nội dung (Python stdlib + Gemini tuỳ chọn)
content/                # gói nội dung theo ngày (bot tự commit)
index.html / archive.html  # site tĩnh người dùng thấy
.github/workflows/daily.yml  # cron 8:30 VN mỗi ngày
```
