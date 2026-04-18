"""
BREW & BOND - Cafe Loyalty System
Backend: Python Flask
"""

import os
import json
import uuid
import string
import random
import io
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session

import qrcode
from qrcode.image.styledpil import StyledPilImage
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ─── In-Memory Database (replace with real DB in production) ───
customers_db = {}
orders_db = {}

FREE_AFTER = 7  # Free drink after every 7 purchases

DRINKS = [
    {"id": 1,  "name": "قهوة عربية",      "name_en": "Arabic Coffee",      "price": 15, "emoji": "☕", "category": "hot"},
    {"id": 2,  "name": "لاتيه",           "name_en": "Latte",              "price": 22, "emoji": "🥛", "category": "hot"},
    {"id": 3,  "name": "كابتشينو",        "name_en": "Cappuccino",         "price": 20, "emoji": "☕", "category": "hot"},
    {"id": 4,  "name": "إسبريسو",         "name_en": "Espresso",           "price": 12, "emoji": "⚡", "category": "hot"},
    {"id": 5,  "name": "موكا",            "name_en": "Mocha",              "price": 25, "emoji": "🍫", "category": "hot"},
    {"id": 6,  "name": "شاي أخضر",        "name_en": "Green Tea",          "price": 14, "emoji": "🍵", "category": "hot"},
    {"id": 7,  "name": "آيس لاتيه",       "name_en": "Iced Latte",         "price": 25, "emoji": "🧊", "category": "cold"},
    {"id": 8,  "name": "فرابتشينو",       "name_en": "Frappuccino",        "price": 28, "emoji": "🥤", "category": "cold"},
    {"id": 9,  "name": "آيس أمريكانو",    "name_en": "Iced Americano",     "price": 20, "emoji": "🧊", "category": "cold"},
    {"id": 10, "name": "سموذي مانجو",     "name_en": "Mango Smoothie",     "price": 22, "emoji": "🥭", "category": "cold"},
    {"id": 11, "name": "عصير برتقال",     "name_en": "Orange Juice",       "price": 18, "emoji": "🍊", "category": "cold"},
    {"id": 12, "name": "ماتشا لاتيه",     "name_en": "Matcha Latte",       "price": 26, "emoji": "🍵", "category": "special"},
    {"id": 13, "name": "كراميل ماكياتو",  "name_en": "Caramel Macchiato",  "price": 27, "emoji": "🍯", "category": "special"},
    {"id": 14, "name": "هوت شوكولت",      "name_en": "Hot Chocolate",      "price": 20, "emoji": "🍫", "category": "special"},
]


def generate_customer_id():
    """Generate unique customer ID like CF-A3K7NP"""
    chars = string.ascii_uppercase.replace('I', '').replace('O', '') + "23456789"
    code = ''.join(random.choices(chars, k=6))
    return f"CF-{code}"


def generate_qr_base64(data_str):
    """Generate QR code as base64 PNG string"""
    qr = qrcode.QRCode(
        version=3,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a0f08", back_color="#f5efe8")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


# ═══════════════════ ROUTES ═══════════════════

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/drinks", methods=["GET"])
def get_drinks():
    """Return all available drinks"""
    category = request.args.get("category", "all")
    if category == "all":
        return jsonify(DRINKS)
    return jsonify([d for d in DRINKS if d["category"] == category])


@app.route("/api/register", methods=["POST"])
def register():
    """Register a new customer"""
    data = request.json
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()

    if not name:
        return jsonify({"error": "الرجاء إدخال الاسم"}), 400

    customer_id = generate_customer_id()
    while customer_id in customers_db:
        customer_id = generate_customer_id()

    customer = {
        "id": customer_id,
        "name": name,
        "phone": phone,
        "stamps": 0,
        "total_stamps": 0,
        "free_earned": 0,
        "created_at": datetime.now().isoformat(),
    }
    customers_db[customer_id] = customer
    orders_db[customer_id] = []

    # Generate QR code
    qr_data = json.dumps({"id": customer_id, "name": name})
    qr_base64 = generate_qr_base64(qr_data)

    return jsonify({
        "customer": customer,
        "qr_code": qr_base64,
        "message": f"مرحباً {name}! رقم عضويتك: {customer_id}"
    })


@app.route("/api/customer/<customer_id>", methods=["GET"])
def get_customer(customer_id):
    """Lookup customer by ID"""
    customer = customers_db.get(customer_id.upper())
    if not customer:
        return jsonify({"error": "لم يتم العثور على العميل"}), 404

    qr_data = json.dumps({"id": customer["id"], "name": customer["name"], "stamps": customer["stamps"]})
    qr_base64 = generate_qr_base64(qr_data)

    return jsonify({
        "customer": customer,
        "orders": orders_db.get(customer["id"], []),
        "qr_code": qr_base64
    })


@app.route("/api/order", methods=["POST"])
def place_order():
    """Place an order and update stamps"""
    data = request.json
    customer_id = data.get("customer_id", "").upper()
    items = data.get("items", [])

    if not customer_id or customer_id not in customers_db:
        return jsonify({"error": "عميل غير موجود"}), 404
    if not items:
        return jsonify({"error": "السلة فارغة"}), 400

    customer = customers_db[customer_id]

    # Calculate order
    order_items = []
    total_price = 0
    total_qty = 0
    for item in items:
        drink = next((d for d in DRINKS if d["id"] == item["id"]), None)
        if drink:
            qty = item.get("qty", 1)
            order_items.append({
                "name": drink["name"],
                "name_en": drink["name_en"],
                "emoji": drink["emoji"],
                "price": drink["price"],
                "qty": qty,
            })
            total_price += drink["price"] * qty
            total_qty += qty

    # Update stamps
    new_stamps = customer["stamps"] + total_qty
    free_this_order = 0
    while new_stamps >= FREE_AFTER:
        new_stamps -= FREE_AFTER
        free_this_order += 1

    customer["stamps"] = new_stamps
    customer["total_stamps"] += total_qty
    customer["free_earned"] += free_this_order

    # Save order
    order = {
        "id": f"ORD-{uuid.uuid4().hex[:8].upper()}",
        "items": order_items,
        "total": total_price,
        "free_earned": free_this_order,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    orders_db[customer_id].insert(0, order)

    # Updated QR
    qr_data = json.dumps({"id": customer_id, "stamps": customer["stamps"], "name": customer["name"]})
    qr_base64 = generate_qr_base64(qr_data)

    remaining = FREE_AFTER - customer["stamps"]
    if free_this_order > 0:
        message = f"🎉 مبروك! حصلت على {free_this_order} مشروب مجاني!"
    else:
        message = f"تم الطلب! باقي {remaining} مشروبات للمجاني"

    return jsonify({
        "order": order,
        "customer": customer,
        "qr_code": qr_base64,
        "free_this_order": free_this_order,
        "message": message,
    })


@app.route("/api/qr/<customer_id>")
def get_qr_image(customer_id):
    """Return QR code as downloadable PNG"""
    customer = customers_db.get(customer_id.upper())
    if not customer:
        return jsonify({"error": "عميل غير موجود"}), 404

    qr_data = json.dumps({
        "id": customer["id"],
        "name": customer["name"],
        "stamps": customer["stamps"],
    })

    qr = qrcode.QRCode(version=3, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=12, border=3)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a0f08", back_color="#f5efe8")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return send_file(buffer, mimetype="image/png", download_name=f"loyalty-{customer_id}.png")


@app.route("/api/wallet/<customer_id>")
def generate_wallet_card(customer_id):
    """Generate a wallet-style card image for Apple/Samsung Pay"""
    customer = customers_db.get(customer_id.upper())
    if not customer:
        return jsonify({"error": "عميل غير موجود"}), 404

    # Create card image
    width, height = 1050, 600
    card = Image.new("RGB", (width, height), "#1a0f08")
    draw = ImageDraw.Draw(card)

    # Gradient background
    for y in range(height):
        r = int(26 + (44 - 26) * (y / height))
        g = int(15 + (24 - 15) * (y / height))
        b = int(8 + (16 - 8) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Header line
    draw.rectangle([0, 0, width, 4], fill="#c8956c")

    # Text (using default font since custom fonts may not be available)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Brand
    draw.text((40, 30), "BREW & BOND", fill="#e8d5c0", font=font_large)
    draw.text((40, 80), "SPECIALTY COFFEE", fill="#a0724e", font=font_small)

    # Customer info
    draw.text((40, 150), f"MEMBER: {customer['name']}", fill="#e8d5c0", font=font_medium)
    draw.text((40, 195), f"ID: {customer['id']}", fill="#c8956c", font=font_medium)
    draw.text((40, 240), f"STAMPS: {customer['stamps']} / {FREE_AFTER}", fill="#c8956c", font=font_medium)

    # Progress bar
    bar_x, bar_y, bar_w, bar_h = 40, 300, 500, 20
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=10, fill="#2c1810")
    fill_w = int(bar_w * (customer["stamps"] / FREE_AFTER))
    if fill_w > 0:
        draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + bar_h], radius=10, fill="#c8956c")

    # QR code on card
    qr_data = json.dumps({"id": customer["id"], "name": customer["name"], "stamps": customer["stamps"]})
    qr = qrcode.QRCode(version=3, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=8, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1a0f08", back_color="#f5efe8").convert("RGB")
    qr_img = qr_img.resize((220, 220))

    # White background for QR
    qr_bg = Image.new("RGB", (240, 240), "#f5efe8")
    qr_bg.paste(qr_img, (10, 10))
    card.paste(qr_bg, (760, 180))

    # Free drinks earned
    draw.text((40, 360), f"Free Drinks Earned: {customer['free_earned']}", fill="#e8b88a", font=font_small)

    # Footer
    draw.rectangle([0, height - 60, width, height], fill="#0d0705")
    draw.text((40, height - 45), f"Buy {FREE_AFTER}, Get 1 Free!", fill="#a0724e", font=font_small)

    buffer = io.BytesIO()
    card.save(buffer, format="PNG")
    buffer.seek(0)

    return send_file(buffer, mimetype="image/png", download_name=f"wallet-card-{customer_id}.png")


# ═══════════════════ ADMIN ═══════════════════

@app.route("/api/admin/customers", methods=["GET"])
def admin_list_customers():
    """List all customers (admin)"""
    return jsonify(list(customers_db.values()))


@app.route("/api/admin/add-stamp", methods=["POST"])
def admin_add_stamp():
    """Manually add stamp to customer (admin/cashier)"""
    data = request.json
    customer_id = data.get("customer_id", "").upper()
    count = data.get("count", 1)

    if customer_id not in customers_db:
        return jsonify({"error": "عميل غير موجود"}), 404

    customer = customers_db[customer_id]
    new_stamps = customer["stamps"] + count
    free_earned = 0
    while new_stamps >= FREE_AFTER:
        new_stamps -= FREE_AFTER
        free_earned += 1

    customer["stamps"] = new_stamps
    customer["total_stamps"] += count
    customer["free_earned"] += free_earned

    return jsonify({
        "customer": customer,
        "free_earned": free_earned,
        "message": f"تمت إضافة {count} ختم"
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
