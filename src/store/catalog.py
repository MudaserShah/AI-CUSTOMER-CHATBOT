from decimal import Decimal


PRODUCTS = [
    {
        "id": "airpods-pro-2",
        "name": "AirPods Pro 2",
        "description": "Premium wireless earbuds with active noise cancellation.",
        "category": "Audio",
        "unit_price": Decimal("249.00"),
        "currency": "USD",
        "image_emoji": "🎧",
    },
    {
        "id": "mechanical-keyboard",
        "name": "Mechanical Keyboard",
        "description": "Hot-swappable 75% keyboard with tactile switches.",
        "category": "Accessories",
        "unit_price": Decimal("129.00"),
        "currency": "USD",
        "image_emoji": "⌨️",
    },
    {
        "id": "ultrabook-14",
        "name": "UltraBook 14",
        "description": "Lightweight 14-inch laptop built for daily productivity.",
        "category": "Computers",
        "unit_price": Decimal("899.00"),
        "currency": "USD",
        "image_emoji": "💻",
    },
    {
        "id": "smartwatch-x",
        "name": "SmartWatch X",
        "description": "AMOLED smartwatch with fitness and notification tracking.",
        "category": "Wearables",
        "unit_price": Decimal("199.00"),
        "currency": "USD",
        "image_emoji": "⌚",
    },
    {
        "id": "usb-c-hub",
        "name": "USB-C Hub Pro",
        "description": "7-in-1 hub with HDMI, USB 3.0, SD and power delivery.",
        "category": "Accessories",
        "unit_price": Decimal("59.00"),
        "currency": "USD",
        "image_emoji": "🔌",
    },
    {
        "id": "desk-speakers",
        "name": "Desk Speakers",
        "description": "Compact stereo speakers tuned for a clean desktop setup.",
        "category": "Audio",
        "unit_price": Decimal("89.00"),
        "currency": "USD",
        "image_emoji": "🔊",
    },
]

_PRODUCT_INDEX = {product["id"]: product for product in PRODUCTS}


def list_products() -> list[dict]:
    return [dict(product) for product in PRODUCTS]


def get_product(product_id: str) -> dict | None:
    product = _PRODUCT_INDEX.get(product_id)
    return dict(product) if product else None
