import json
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# FeePilot Global · catálogo de plataformas
#
# Regla de honestidad de datos:
#   confidence = "verified"  → la tarifa base fue contrastada con la página oficial en REVIEW_DATE.
#   confidence = "estimate"  → tarifa aproximada / no re-verificada; la interfaz lo dice de forma visible.
# Nunca marques "verified" sin haber comprobado la fuente oficial ese mismo mes.
# ──────────────────────────────────────────────────────────────────────────────
REVIEW_DATE = "2026-10-25"      # fecha de la última revisión de tarifas
REVIEW_MONTH = "Oct 2026"

# 25 Plataformas Globales (Fintech, Freelance, SaaS, E-Commerce, Creator Economy)
RAW_PLATFORMS = [
    # key, Name, Category, % Fee, Fixed $, Intl Extra %, Official/Affiliate URL
    ("stripe", "Stripe", "Payment Processor", 2.9, 0.30, 1.5, "https://stripe.com"),
    ("paypal", "PayPal", "Payment Processor", 3.49, 0.49, 1.5, "https://paypal.com"),
    ("wise", "Wise", "Global Transfers", 0.65, 0.45, 0.0, "https://wise.com/invite/dic/andya788"),
    ("payoneer", "Payoneer", "Global Transfers", 3.0, 0.00, 1.0, "https://payoneer.com"),
    ("shopify", "Shopify Payments", "E-Commerce", 2.9, 0.30, 2.0, "https://shopify.com"),
    ("square", "Square", "Payment Processor", 3.3, 0.30, 1.0, "https://squareup.com"),
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

# ── Fuentes y metadatos verificados (solo lo que se contrastó en la revisión) ─────────────
# fx_extra_percent  → recargo SEPARADO por conversión de divisa (distinto al recargo por tarjeta internacional)
# rate_options      → planes / regiones con tarifa propia (la primera = tarifa por defecto de la ficha)
VERIFIED = {
    "stripe": {
        "source_url": "https://stripe.com/pricing",
        "fx_extra_percent": 1.0,
        "rate_options": [
            {"id": "us",  "label_en": "United States · online cards", "label_es": "Estados Unidos · tarjetas online", "percent_fee": 2.9, "fixed_fee": 0.30, "currency": "USD"},
            {"id": "uk",  "label_en": "United Kingdom · UK cards",    "label_es": "Reino Unido · tarjetas del RU",    "percent_fee": 1.5, "fixed_fee": 0.20, "currency": "GBP"},
            {"id": "eea", "label_en": "EEA · standard European cards", "label_es": "EEE · tarjetas europeas estándar", "percent_fee": 1.5, "fixed_fee": 0.25, "currency": "EUR"},
        ],
        "note_en": "US online card rate. International cards add 1.5%; if the customer pays in a different currency, currency conversion adds another 1% on US accounts (higher on some other regions). UK and EEA accounts have their own rates (see the region selector).",
        "note_es": "Tarifa de tarjetas online en EE. UU. Las tarjetas internacionales suman 1,5%; si el cliente paga en otra moneda, la conversión de divisa suma otro 1% en cuentas de EE. UU. (más en algunas regiones). Las cuentas del Reino Unido y del EEE tienen tarifas propias (selector de región).",
    },
    "paypal": {
        "source_url": "https://www.paypal.com/us/business/paypal-business-fees",
        "fx_extra_percent": 3.0,
        "rate_options": [
            {"id": "checkout", "label_en": "US · PayPal Checkout / invoices", "label_es": "EE. UU. · PayPal Checkout / facturas", "percent_fee": 3.49, "fixed_fee": 0.49, "currency": "USD"},
            {"id": "card",     "label_en": "US · standard card payments",     "label_es": "EE. UU. · pagos estándar con tarjeta", "percent_fee": 2.99, "fixed_fee": 0.49, "currency": "USD"},
        ],
        "note_en": "US merchant rate for PayPal Checkout and invoices (standard card payments are 2.99% + $0.49). International commercial payments add 1.5%. PayPal's currency conversion spread is roughly 3%–4% on top of the exchange rate; the calculator uses 3%.",
        "note_es": "Tarifa comercial de EE. UU. para PayPal Checkout y facturas (los pagos estándar con tarjeta son 2,99% + $0,49). Los pagos comerciales internacionales suman 1,5%. El margen de conversión de divisa de PayPal ronda el 3%–4% sobre el tipo de cambio; la calculadora usa 3%.",
    },
    "square": {
        "source_url": "https://squareup.com/us/en/pricing",
        "fx_extra_percent": 0.0,
        "rate_options": [
            {"id": "free", "label_en": "Square Free · online & invoices", "label_es": "Square Free · online y facturas", "percent_fee": 3.3, "fixed_fee": 0.30, "currency": "USD"},
            {"id": "plus", "label_en": "Square Plus / Premium · online & invoices", "label_es": "Square Plus / Premium · online y facturas", "percent_fee": 2.9, "fixed_fee": 0.30, "currency": "USD"},
        ],
        "note_en": "US rates. Square Free charges 3.3% + 30¢ for online sales and invoices; Square Plus and Premium (paid plans) charge 2.9% + 30¢. The online API is 2.9% + 30¢ on every plan. The international add-on is an estimate.",
        "note_es": "Tarifas de EE. UU. Square Free cobra 3,3% + 30¢ en ventas online y facturas; Square Plus y Premium (planes de pago) cobran 2,9% + 30¢. La API online es 2,9% + 30¢ en todos los planes. El recargo internacional es una estimación.",
    },
    "shopify": {
        "source_url": "https://www.shopify.com/pricing",
        "fx_extra_percent": 0.0,
        "rate_options": [
            {"id": "basic",    "label_en": "Basic plan · online standard cards",    "label_es": "Plan Basic · tarjetas estándar online",    "percent_fee": 2.9, "fixed_fee": 0.30, "currency": "USD"},
            {"id": "grow",     "label_en": "Grow plan · online standard cards",     "label_es": "Plan Grow · tarjetas estándar online",     "percent_fee": 2.7, "fixed_fee": 0.30, "currency": "USD"},
            {"id": "advanced", "label_en": "Advanced plan · online standard cards", "label_es": "Plan Advanced · tarjetas estándar online", "percent_fee": 2.5, "fixed_fee": 0.30, "currency": "USD"},
        ],
        "note_en": "US online standard-card rates by plan: Basic 2.9% + 30¢, Grow 2.7% + 30¢, Advanced 2.5% + 30¢ (premium cards cost more). The monthly plan fee is not included. The international add-on is an estimate.",
        "note_es": "Tarifas de tarjetas estándar online en EE. UU. por plan: Basic 2,9% + 30¢, Grow 2,7% + 30¢, Advanced 2,5% + 30¢ (las tarjetas premium cuestan más). No incluye la cuota mensual del plan. El recargo internacional es una estimación.",
    },
}

# ── Estimaciones con matices conocidos (tarifa base sin cambios, pero con explicación honesta) ──
ESTIMATE_NOTES = {
    "wise": (
        "Wise does not publish a single percentage-plus-fixed rate for receiving money. Receiving USD by ACH is free, a USD wire costs a fixed $6.11, and currency conversion is a variable percentage that depends on the currency pair (typically under 1%). 0.65% + $0.45 is an illustrative blended estimate, not an official Wise price.",
        "Wise no publica una tarifa única de porcentaje más cargo fijo para recibir dinero. Recibir USD por ACH es gratis, un giro (wire) en USD cuesta $6,11 fijos y la conversión de divisa es un porcentaje variable según el par de monedas (normalmente menos de 1%). 0,65% + $0,45 es una estimación combinada ilustrativa, no un precio oficial de Wise.",
        "https://wise.com/us/pricing/business/receive",
    ),
    "upwork": (
        "Since May 2025 Upwork charges freelancers a variable service fee of 0%–15% per contract (shown before you submit a proposal). 10% is a typical value, not a fixed price.",
        "Desde mayo de 2025 Upwork cobra a los freelancers una comisión variable de 0%–15% por contrato (se muestra antes de enviar la propuesta). 10% es un valor típico, no un precio fijo.",
        "https://upwork.com",
    ),
}

GENERIC_NOTE_EN = "Estimated rate: not independently re-checked in the {month} review. Platforms change fees often and many depend on plan, category or country. Confirm on the official pricing page before relying on it."
GENERIC_NOTE_ES = "Tarifa estimada: no se volvió a comprobar de forma independiente en la revisión de {month}. Las plataformas cambian sus tarifas con frecuencia y muchas dependen del plan, la categoría o el país. Confírmala en la página oficial de precios antes de usarla."


def build_catalog():
    platforms = {}
    verified_count = 0
    for key, name, cat, pct, fix, intl, url in RAW_PLATFORMS:
        ex_100_fee = round((100 * (pct / 100)) + fix, 2)
        ex_100_net = round(100 - ex_100_fee, 2)
        ex_1000_fee = round((1000 * (pct / 100)) + fix, 2)
        ex_1000_net = round(1000 - ex_1000_fee, 2)

        v = VERIFIED.get(key)
        if v:
            confidence, checked = "verified", REVIEW_DATE[:7]
            source_url, fx = v["source_url"], v["fx_extra_percent"]
            options = v["rate_options"]
            note_en, note_es = v["note_en"], v["note_es"]
            verified_count += 1
        else:
            confidence, checked = "estimate", None
            fx, options = 0.0, []
            if key in ESTIMATE_NOTES:
                note_en, note_es, source_url = ESTIMATE_NOTES[key]
            else:
                note_en = GENERIC_NOTE_EN.format(month=REVIEW_MONTH)
                note_es = GENERIC_NOTE_ES.format(month=REVIEW_MONTH)
                source_url = url

        if key == "wise":      # el enlace de afiliado de Wise nunca se presenta como "fuente oficial"
            source_url = ESTIMATE_NOTES["wise"][2]

        platforms[key] = {
            "name": name,
            "category": cat,
            "percent_fee": pct,
            "fixed_fee": fix,
            "intl_extra_percent": intl,
            "fx_extra_percent": fx,
            "affiliate_url": url,
            "source_url": source_url,
            "confidence": confidence,
            "checked": checked,
            "rate_options": options,
            "rate_note": {"en": note_en, "es": note_es},
            "seo": {
                "en": {
                    "title": f"{name} Fee Calculator (2026) - Net Payout & Invoice Calculator",
                    "h1": f"{name} Fee Calculator",
                    "desc": f"Calculate exact {name} fees ({pct}% + ${fix:.2f}). See your net payout on any amount and how much to invoice to avoid losing money to processing costs.",
                    "guide": (
                        f"{name} operates in the {cat} sector with a standard transaction rate of {pct}% plus a fixed fee of ${fix:.2f} per transaction. "
                        f"For example, on a $100.00 payment, {name} deducts ${ex_100_fee:.2f}, leaving you with a net payout of ${ex_100_net:.2f}. "
                        f"On a $1,000.00 transaction, your net payout is ${ex_1000_net:.2f} after the ${ex_1000_fee:.2f} processing fee. "
                        f"If you accept international payments or currency conversions, an additional {intl}% cross-border fee may apply"
                        + (f", and currency conversion can add {fx}% more. " if fx else ". ")
                        + note_en
                    ),
                    "faqs": [
                        {
                            "q": f"How much does {name} charge per transaction in 2026?",
                            "a": f"The standard {name} processing fee used in this calculator is {pct}% + ${fix:.2f} per domestic transaction. International cards add roughly {intl}%" + (f" and currency conversion adds about {fx}%." if fx else ".") + (" This rate was checked against the official pricing source in " + REVIEW_MONTH + "." if v else " This rate is an estimate; confirm it on the official site.")
                        },
                        {
                            "q": f"How much is the {name} fee on $1,000?",
                            "a": f"For a $1,000 USD payment at {pct}% + ${fix:.2f}, {name} charges ${ex_1000_fee:.2f} in fees, meaning you receive ${ex_1000_net:.2f} net in your account."
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
                        f"{name} es una plataforma de la categoría {cat} que aplica una tarifa estándar de {pct}% más un cargo fijo de ${fix:.2f} USD por operación. "
                        f"Por ejemplo, en un cobro de $100.00 USD, la comisión de {name} es de ${ex_100_fee:.2f}, dejándote ${ex_100_net:.2f} libres. "
                        f"En una venta o transferencia de $1,000.00 USD, recibirás ${ex_1000_net:.2f} netos tras descontar ${ex_1000_fee:.2f}. "
                        f"En pagos internacionales o con cambio de divisa, se suma un {intl}% adicional"
                        + (f" y la conversión de divisa puede añadir otro {fx}%. " if fx else ". ")
                        + note_es
                    ),
                    "faqs": [
                        {
                            "q": f"¿Cuánto cobra {name} de comisión en 2026?",
                            "a": f"La comisión estándar de {name} que usa esta calculadora es del {pct}% más ${fix:.2f} USD fijos por transacción nacional, con un recargo aproximado del {intl}% en pagos internacionales" + (f" y cerca de {fx}% por conversión de divisa." if fx else ".") + (" Esta tarifa se contrastó con la fuente oficial en " + REVIEW_MONTH + "." if v else " Esta tarifa es una estimación; confírmala en el sitio oficial.")
                        },
                        {
                            "q": f"¿Cuánto me descuenta {name} por $1,000 dólares?",
                            "a": f"En un cobro de $1,000 USD al {pct}% + ${fix:.2f}, {name} retiene ${ex_1000_fee:.2f} de comisión, por lo que recibes ${ex_1000_net:.2f} netos."
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
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "last_reviewed": REVIEW_DATE,
            "review_month": REVIEW_MONTH,
            "verified_count": verified_count,
            "total_count": len(platforms),
        },
        "platforms": platforms,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Exito: {len(platforms)} plataformas generadas en {out_path} ({verified_count} verificadas, {len(platforms) - verified_count} estimadas)")


if __name__ == "__main__":
    build_catalog()
