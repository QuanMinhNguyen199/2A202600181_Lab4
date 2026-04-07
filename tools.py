from langchain_core.tools import tool
import difflib
import unicodedata

# --- MOCK DATA: Dữ liệu giả lập hệ thống du lịch ---
FLIGHTS_DB = {
    ("Hà Nội", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20", "price": 1450000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "14:00", "arrival": "15:20", "price": 2800000, "class": "business"},
        {"airline": "VietJet Air", "departure": "08:30", "arrival": "09:50", "price": 890000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "11:00", "arrival": "12:20", "price": 1200000, "class": "economy"},
    ],
    ("Hà Nội", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:15", "price": 2100000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "10:00", "arrival": "12:15", "price": 1350000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "16:00", "arrival": "18:15", "price": 1100000, "class": "economy"},
    ],
    ("Hà Nội", "Hồ Chí Minh"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "08:10", "price": 1600000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "07:30", "arrival": "09:40", "price": 950000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "12:00", "arrival": "14:10", "price": 1300000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "18:00", "arrival": "20:10", "price": 3200000, "class": "business"},
    ],
    ("Hồ Chí Minh", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "09:00", "arrival": "10:20", "price": 1300000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "13:00", "arrival": "14:20", "price": 780000, "class": "economy"},
    ],
    ("Hồ Chí Minh", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "08:00", "arrival": "09:00", "price": 1100000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "15:00", "arrival": "16:00", "price": 650000, "class": "economy"},
    ],
}

HOTELS_DB = {
    "Đà Nẵng": [
        {"name": "Mường Thanh Luxury", "stars": 5, "price_per_night": 1800000, "area": "Mỹ Khê", "rating": 4.5},
        {"name": "Sala Danang Beach", "stars": 4, "price_per_night": 1200000, "area": "Mỹ Khê", "rating": 4.3},
        {"name": "Fivitel Danang", "stars": 3, "price_per_night": 650000, "area": "Sơn Trà", "rating": 4.1},
        {"name": "Memory Hostel", "stars": 2, "price_per_night": 250000, "area": "Hải Châu", "rating": 4.6},
        {"name": "Christina's Homestay", "stars": 2, "price_per_night": 350000, "area": "An Thượng", "rating": 4.7},
    ],
    "Phú Quốc": [
        {"name": "Vinpearl Resort", "stars": 5, "price_per_night": 3500000, "area": "Bãi Dài", "rating": 4.5},
        {"name": "Sol by Meliá", "stars": 4, "price_per_night": 1500000, "area": "Bãi Trường", "rating": 4.2},
        {"name": "Lahana Resort", "stars": 3, "price_per_night": 800000, "area": "Dương Đông", "rating": 4.0},
        {"name": "9Station Hostel", "stars": 2, "price_per_night": 200000, "area": "Dương Đông", "rating": 4.5},
    ],
    "Hồ Chí Minh": [
        {"name": "Rex Hotel", "stars": 5, "price_per_night": 2800000, "area": "Quận 1", "rating": 4.3},
        {"name": "Liberty Central", "stars": 4, "price_per_night": 1400000, "area": "Quận 1", "rating": 4.1},
        {"name": "Cochin Zen Hotel", "stars": 3, "price_per_night": 550000, "area": "Quận 3", "rating": 4.4},
        {"name": "The Common Room", "stars": 2, "price_per_night": 180000, "area": "Quận 1", "rating": 4.6},
    ],
}

# --- IMPLEMENTATION ---

def normalize_place(name: str) -> str:
    text = name.strip().lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = ''.join(ch if ch.isalnum() or ch.isspace() else ' ' for ch in text)
    return ' '.join(text.split())


def fuzzy_match_place(name: str, choices: list[str], cutoff: float = 0.6) -> tuple[str | None, str]:
    normalized_name = normalize_place(name)
    normalized_choices = {normalize_place(choice): choice for choice in choices}
    if normalized_name in normalized_choices:
        return normalized_choices[normalized_name], name

    best = None
    best_ratio = 0.0
    for norm_choice, original_choice in normalized_choices.items():
        ratio = difflib.SequenceMatcher(a=normalized_name, b=norm_choice).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best = original_choice

    if best and best_ratio >= cutoff:
        return best, name
    return None, name


@tool
def search_flights(origin: str, destination: str) -> str:
    """Tra cứu chuyến bay dựa trên route tuple, chuẩn hóa tên và thử tìm chiều ngược lại nếu cần."""
    known_origins = {route[0] for route in FLIGHTS_DB}
    known_destinations = {route[1] for route in FLIGHTS_DB}

    origin_match, origin_input = fuzzy_match_place(origin, list(known_origins))
    destination_match, destination_input = fuzzy_match_place(destination, list(known_destinations))

    note = []
    if origin_match is None or destination_match is None:
        return f"Không tìm thấy chuyến bay cho {origin} → {destination}. Vui lòng kiểm tra lại tên thành phố."

    if origin_match != origin_input:
        note.append(f"Đã chuẩn hóa '{origin}' thành '{origin_match}'.")
    if destination_match != destination_input:
        note.append(f"Đã chuẩn hóa '{destination}' thành '{destination_match}'.")

    route = (origin_match, destination_match)
    flights = FLIGHTS_DB.get(route)
    reverse_note = ""

    if not flights:
        reversed_route = (destination_match, origin_match)
        flights = FLIGHTS_DB.get(reversed_route)
        if flights:
            reverse_note = (
                f"Lưu ý: chỉ có dữ liệu chuyến bay cho chiều {destination_match} → {origin_match}; "
                "kết quả này hiển thị theo chiều ngược lại.\n"
            )

    if not flights:
        return f"Không tìm thấy chuyến bay từ {origin_match} đến {destination_match}."

    result = ''
    if note:
        result += ' '.join(note) + '\n'
    result += f"{reverse_note}Tìm thấy {len(flights)} chuyến bay cụ thể:\n"
    for i, f in enumerate(flights, 1):
        result += f"Lựa chọn {i}: {f['airline']} - Khởi hành: {f['departure']} - Giá: {f['price']:,}₫ ({f['class']})\n"

    prices = [f['price'] for f in flights]
    result += f"Giá rẻ nhất: {min(prices):,}₫, Giá cao nhất: {max(prices):,}₫.\n"
    return result

@tool
def search_hotels(city: str, max_price_per_night: int = 99999999) -> str:
    """Tìm kiếm khách sạn tại một thành phố với cơ chế sửa lỗi chính tả."""
    # Lấy danh sách các thành phố hiện có trong DB khách sạn
    known_cities = list(HOTELS_DB.keys())
    
    # Sử dụng hàm fuzzy_match_place bạn đã viết
    city_match, _ = fuzzy_match_place(city, known_cities)

    if not city_match:
        return f"Không tìm thấy dữ liệu khách sạn tại {city}."

    hotels = HOTELS_DB.get(city_match, [])
    filtered_hotels = [h for h in hotels if h["price_per_night"] <= max_price_per_night]
    filtered_hotels.sort(key=lambda x: (-x["rating"], x["price_per_night"]))

    if not filtered_hotels:
        return f"Không tìm thấy khách sạn tại {city} với giá dưới {max_price_per_night:,}₫/đêm. Hãy thử tăng ngân sách hoặc đổi địa điểm."

    result = f"Khách sạn tại {city} phù hợp ngân sách (sắp xếp theo rating và giá):\n"
    for h in filtered_hotels:
        result += f"- {h['name']} ({h['stars']}*): {h['price_per_night']:,}₫/đêm - Khu vực: {h['area']} - Rating: {h['rating']}\n"
    return result

@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """Tính toán ngân sách còn lại sau khi trừ các khoản chi phí.
    expenses: chuỗi 'tên khoản: số tiền', cách nhau bởi dấu phẩy hoặc chấm phẩy."""
    import re

    def parse_amount(amount_text: str) -> int:
        text = amount_text.strip().lower()
        if not text:
            raise ValueError("Số tiền trống")

        text = text.replace("₫", "").replace("vnd", "").replace("đ", "")
        text = text.replace(" ", "").replace(",", ".")

        multiplier = 1
        if re.search(r"triệu|m|million", text):
            multiplier = 1_000_000
        elif re.search(r"nghìn|k|thousand", text):
            multiplier = 1_000

        match = re.search(r"(\d+(?:\.\d+)?)", text)
        if not match:
            raise ValueError(f"Không phân tích được số tiền từ '{amount_text}'")

        value = float(match.group(1))
        return int(value * multiplier)

    try:
        items = [item.strip() for item in re.split(r"[;,]", expenses) if item.strip()]
        if not items:
            raise ValueError("Không có khoản chi phí nào được cung cấp.")

        total_spent = 0
        detail_lines = []
        for item in items:
            if ":" not in item:
                raise ValueError(f"Khoản chi không đúng định dạng: '{item}'")
            name, price_text = item.split(":", 1)
            price_val = parse_amount(price_text)
            total_spent += price_val
            detail_lines.append(f"{name.strip().capitalize()}: {price_val:,}₫")

        remaining = total_budget - total_spent
        result = "Bảng chi phí:\n" + "\n".join(detail_lines)
        result += f"\n\nTổng chi: {total_spent:,}₫"
        result += f"\nNgân sách: {total_budget:,}₫"
        result += f"\nCòn lại: {remaining:,}₫" if remaining >= 0 else f"\nVượt ngân sách {abs(remaining):,}₫! Cần điều chỉnh."
        return result

    except ValueError as exc:
        return f"Lỗi định dạng chi phí: {exc}. Vui lòng dùng 'tên khoản: số tiền, tên khoản: số tiền'."
    except Exception:
        return "Lỗi: Vui lòng nhập chi phí đúng định dạng 'tên khoản: số tiền, tên khoản: số tiền'."