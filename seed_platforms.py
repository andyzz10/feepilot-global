import json
from pathlib import Path

# 25 Plataformas Globales de Alto CPC (Fintech, Freelance, SaaS, E-Commerce, Creator Economy)
RAW_PLATFORMS = [
    # key, Name, Category, % Fee, Fixed $, Intl Extra %, Official/Affiliate URL
    ("stripe", "Stripe", "Payment Processor", 2.9, 0.30, 1.5, "https://stripe.com"),
    ("paypal", "PayPal", "Payment Processor", 3.49, 0.49, 1.5, "https://paypal.com"),
    ("wise", "Wise", "Global Transfers", 0.65, 0.45, 0.0, "https://wise.com/invite/dic/andya788"),
    ("payoneer", "Payoneer", "Global Transfers", 3.0, 0.00, 1.0, "https://payoneer.com"),
    ("shopify", "Shopify Payments", "E-Commerce", 2.9, 0.30, 2.0, "https://shopify.com"),
    ("square", "Square", "Payment Processor", 2.9, 0.30, 1.0, "https://squareup.com"),
    ("lemonsqueezy", "Lemon Squeezy", "SaaS & Merchant of Record", 5.0, 0.50, 1.5, "https://lemonsqueezy.com"),
    ("paddle", "Paddle", "SaaS & Merchant of Record", 5.0, 0.50, 0.0, "https://paddle.com"),
    ("gumroad", "Gumroad", "Creator Economy", 10.0, 0.50, 0.0, "https://gumroad.com"),
    ("patreon", "Patreon", "Creator Economy", 8.0, 0.30, 1.0, "https://patreon.com"),
    ("upwork", "Upwork", "Freelance Marketplace", 10.0, 0.00, 0.0, "https://upwork.com"),
    ("fiverr", "Fiverr", "Freelance Marketplace", 20.0, 0.00, 0.0, "https://fiverr.com"),
    ("etsy", "Etsy Payments", "E-Commerce", 6.5, 0.25, 1.5, "https://etsy.com"),
    ("ebay", "eBay Managed Payments", "E-Commerce", 13.25, 0.30, 1.65, "https://ebay.com"),
    ("amazon", "Amazon Seller Referral", "E-Commerce", 15.0, 0.00, 0.0, "https://sell.amazon.com"),
    ("tiktokshop", "TikTok Shop", "E-Commerce", 6.0, 0.30, 0.0, "https://seller.tiktok.com"),
    ("revolut", "Revolut Business", "Global Transfers", 1.0, 0.20, 0.5, "https://revolut.com"),
    ("mercury", "Mercury Wire & ACH", "Business Banking", 0.0, 0.00, 1.0, "https://mercury.com"),
    ("deel", "Deel Contractor", "Global Payroll & Freelance", 1.0, 0.00, 0.5, "https://deel.com"),
    ("skrill", "Skrill", "Payment Processor", 2.99, 0.00, 1.99, "https://skrill.com"),
    ("venmo", "Venmo Business", "Payment Processor", 1.9, 0.10, 0.0, "https://venmo.com"),
    ("cashapp", "Cash App Business", "Payment Processor", 2.75, 0.00, 0.0, "https://cash.app"),
    ("kofi", "Ko-fi", "Creator Economy", 5.0, 0.30, 1.0, "https://ko-fi.com"),
    ("substack", "Substack", "Creator Economy", 10.0, 0.30, 1.5, "https://substack.com"),
    ("coinbase", "Coinbase Commerce", "Crypto Payments", 1.0, 0.00, 0.0, "https://commerce.coinbase.com"),
]

def build_catalog():
    platforms = {}
    for key, name, cat, pct, fix, intl, url in RAW_PLATFORMS:
        ex_100_fee = round((100 * (pct / 100)) + fix, 2)
        ex_100_net = round(100 - ex_100_fee, 2)
        ex_1000_fee = round((1000 * (pct / 100)) + fix, 2)
        ex_1000_net = round(1000 - ex_1000_fee, 2)

        platforms[key] = {
            "name": name,
            "category": cat,
            "percent_fee": pct,
            "fixed_fee": fix,
            "intl_extra_percent": intl,
            "affiliate_url": url,
            "seo": {
                "en": {
                    "title": f"{name} Fee Calculator (2026) - Net Payout & Invoice Calculator",
                    "h1": f"{name} Fee Calculator",
                    "desc": f"Calculate exact {name} fees ({pct}% + ${fix:.2f}). See your net payout on any amount and how much to invoice to avoid losing money to processing costs.",
                    "guide": (
                        f"{name} operates in the {cat} sector with a standard transaction rate of {pct}% plus a fixed fee of ${fix:.2f} per transaction. "
                        f"For example, on a $100.00 payment, {name} deducts ${ex_100_fee:.2f}, leaving you with a net payout of ${ex_100_net:.2f}. "
                        f"On a $1,000.00 transaction, your net payout is ${ex_1000_net:.2f} after the ${ex_1000_fee:.2f} processing fee. "
                        f"If you accept international payments or currency conversions, an additional {intl}% cross-border fee may apply."
                    ),
                    "faqs": [
                        {
                            "q": f"How much does {name} charge per transaction in 2026?",
                            "a": f"The standard {name} processing fee is {pct}% + ${fix:.2f} per domestic transaction. International or currency conversion transactions add roughly {intl}%."
                        },
                        {
                            "q": f"How much is the {name} fee on $1,000?",
                            "a": f"For a $1,000 USD payment, {name} charges ${ex_1000_fee:.2f} in standard fees, meaning you receive ${ex_1000_net:.2f} net in your account."
                        },
                        {
                            "q": f"How do I pass {name} fees to my client?",
                            "a": f"To receive the exact net amount after {name} deducts its {pct}% + ${fix:.2f} fee, use the Reverse Invoice formula: (Desired Amount + ${fix:.2f}) / (1 - {pct/100:.4f})."
                        }
                    ]
                },
                "es": {
                    "title": f"Calculadora de Comisiones {name} (2026) - Neto Exacto y Facturación",
                    "h1": f"Calculadora de Comisiones de {name}",
                    "desc": f"Calcula al instante las comisiones de {name} ({pct}% + ${fix:.2f}). Descubre cuánto recibes neto y cuánto debes cobrar para no perder dinero.",
                    "guide": (
                        f"{name} es una plataforma líder en la categoría de {cat} que aplica una tarifa estándar de {pct}% más un cargo fijo de ${fix:.2f} USD por operación. "
                        f"Por ejemplo, en un cobro de $100.00 USD, la comisión de {name} es de ${ex_100_fee:.2f}, dejándote ${ex_100_net:.2f} libres. "
                        f"En una venta o transferencia de $1,000.00 USD, recibirás ${ex_1000_net:.2f} netos tras descontar ${ex_1000_fee:.2f}. "
                        f"En pagos internacionales o con cambio de divisa, se suma un {intl}% adicional."
                    ),
                    "faqs": [
                        {
                            "q": f"¿Cuánto cobra {name} de comisión en 2026?",
                            "a": f"La comisión estándar de {name} es del {pct}% más ${fix:.2f} USD fijos por transacción nacional, con un recargo aproximado del {intl}% en pagos internacionales."
                        },
                        {
                            "q": f"¿Cuánto me descuenta {name} por $1,000 dólares?",
                            "a": f"En un cobro de $1,000 USD, {name} retiene ${ex_1000_fee:.2f} de comisión estándar, por lo que recibes ${ex_1000_net:.2f} netos."
                        },
                        {
                            "q": f"¿Cómo calcular cuánto cobrar en {name} para recibir el monto exacto?",
                            "a": f"Usa el cálculo inverso de nuestra herramienta: suma el cargo fijo (${fix:.2f}) al monto deseado y divídelo entre (1 - {pct/100:.4f})."
                        }
                    ]
                }
            }
        }

    out_path = Path(__file__).resolve().parent / "engine" / "data" / "platforms.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"platforms": platforms}, f, indent=2, ensure_ascii=False)
    print(f"Exito: {len(platforms)} plataformas generadas en {out_path}")

if __name__ == "__main__":
    build_catalog()