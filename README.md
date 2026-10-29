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

Nguyên tắc: mọi hạ tầng đều dùng bậc miễn phí vĩnh viễn → bot **không thể "cháy" vốn**.

## Cấu trúc

```
data/niches.json        # 12 ngách bán hàng (khán giả, nỗi đau, hashtag, mẹo quay)
generator/generate.py   # bot sinh nội dung (Python stdlib + Gemini tuỳ chọn)
content/                # gói nội dung theo ngày (bot tự commit)
index.html / archive.html  # site tĩnh người dùng thấy
.github/workflows/daily.yml  # cron 8:30 VN mỗi ngày
```
