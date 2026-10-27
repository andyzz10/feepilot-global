import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# FeePilot Global · catálogo de plataformas
#
# Regla de honestidad de datos (tres niveles):
#   confidence = "verified"       → la tarifa se comprobó en la página oficial del proveedor en REVIEW_DATE.
#   confidence = "cross-checked"  → coincide en varias fuentes independientes de 2026, pero NO se abrió la página oficial.
#   confidence = "estimate"       → aproximada / sin comprobar; la interfaz lo dice de forma visible.
# Nunca subas el nivel sin haber hecho la comprobación ese mismo mes.
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

# ── Datos contrastados (solo lo que realmente se comprobó en la revisión) ─────────────
# level            → "verified" (página oficial) | "cross-checked" (fuentes independientes)
# fx_extra_percent → recargo SEPARADO por conversión de divisa (distinto al de tarjeta internacional)
# rate_options     → planes / regiones con tarifa propia (la primera = tarifa por defecto de la ficha)
# limits / faqs    → texto específico de la plataforma (en/es); solo hechos comprobados
CHECKED = {
    "stripe": {
        "level": "cross-checked",
        "source_url": "https://stripe.com/pricing",
        "fx_extra_percent": 1.0,
        "rate_options": [
            {"id": "us",  "label_en": "United States · online cards", "label_es": "Estados Unidos · tarjetas online", "percent_fee": 2.9, "fixed_fee": 0.30, "currency": "USD"},
            {"id": "uk",  "label_en": "United Kingdom · UK cards",    "label_es": "Reino Unido · tarjetas del RU",    "percent_fee": 1.5, "fixed_fee": 0.20, "currency": "GBP"},
            {"id": "eea", "label_en": "EEA · standard European cards", "label_es": "EEE · tarjetas europeas estándar", "percent_fee": 1.5, "fixed_fee": 0.25, "currency": "EUR"},
        ],
        "note_en": "US online card rate. International cards add 1.5%; if the customer pays in a different currency, currency conversion adds another 1% on US accounts (higher on some other regions). UK and EEA accounts have their own rates (see the region selector).",
        "note_es": "Tarifa de tarjetas online en EE. UU. Las tarjetas internacionales suman 1,5%; si el cliente paga en otra moneda, la conversión de divisa suma otro 1% en cuentas de EE. UU. (más en algunas regiones). Las cuentas del Reino Unido y del EEE tienen tarifas propias (selector de región).",
        "limits_en": [
            "Only card processing is modelled. ACH Direct Debit is priced differently (0.8%, capped at $5), cards entered by hand cost an extra 0.5%, and a dispute costs $15.",
            "UK and EEA fixed fees are in pounds and euros; the calculator uses the number as entered and does not convert currencies.",
        ],
        "limits_es": [
            "Solo se modela el procesamiento de tarjetas. El débito directo ACH tiene otra tarifa (0,8% con tope de $5), las tarjetas introducidas a mano cuestan un 0,5% adicional y una disputa cuesta $15.",
            "Los cargos fijos del Reino Unido y del EEE están en libras y euros; la calculadora usa la cifra tal cual y no convierte monedas.",
        ],
        "faqs_en": [
            ("Do international cards and currency conversion both apply to the same payment?",
             "They are separate surcharges and they add up. For a US account, an international card adds 1.5% and a currency conversion adds 1%, so a payment with both is charged 2.9% + 1.5% + 1% = 5.4% plus $0.30. Tick both boxes in the calculator to see it."),
            ("Which rate should I pick if my Stripe account is in the UK or the EEA?",
             "Choose the region in the Plan / Region selector: 1.5% + £0.20 for UK cards or 1.5% + €0.25 for standard European cards. Cards from other regions cost more, so treat these as the lowest standard rates."),
        ],
        "faqs_es": [
            ("¿Se aplican a la vez la tarjeta internacional y la conversión de divisa?",
             "Son recargos separados y se suman. En una cuenta de EE. UU., una tarjeta internacional añade 1,5% y la conversión de divisa 1%, así que un pago con ambos paga 2,9% + 1,5% + 1% = 5,4% más $0,30. Marca las dos casillas en la calculadora para verlo."),
            ("¿Qué tarifa elijo si mi cuenta de Stripe está en el Reino Unido o el EEE?",
             "Elige la región en el selector Plan / Región: 1,5% + £0,20 para tarjetas del Reino Unido o 1,5% + €0,25 para tarjetas europeas estándar. Las tarjetas de otras regiones cuestan más, así que son las tarifas estándar más bajas."),
        ],
    },
    "paypal": {
        "level": "cross-checked",
        "source_url": "https://www.paypal.com/us/business/paypal-business-fees",
        "fx_extra_percent": 3.0,
        "rate_options": [
            {"id": "checkout", "label_en": "US · PayPal Checkout / invoices", "label_es": "EE. UU. · PayPal Checkout / facturas", "percent_fee": 3.49, "fixed_fee": 0.49, "currency": "USD"},
            {"id": "card",     "label_en": "US · standard card payments",     "label_es": "EE. UU. · pagos estándar con tarjeta", "percent_fee": 2.99, "fixed_fee": 0.49, "currency": "USD"},
        ],
        "note_en": "US merchant rate for PayPal Checkout and invoices (standard card payments are 2.99% + $0.49). International commercial payments add 1.5%. PayPal's currency conversion spread is roughly 3%–4% on top of the exchange rate; the calculator uses 3%.",
        "note_es": "Tarifa comercial de EE. UU. para PayPal Checkout y facturas (los pagos estándar con tarjeta son 2,99% + $0,49). Los pagos comerciales internacionales suman 1,5%. El margen de conversión de divisa de PayPal ronda el 3%–4% sobre el tipo de cambio; la calculadora usa 3%.",
        "limits_en": [
            "The 3% conversion spread is the low end of the 3%–4% range found in sources; the real spread depends on the currency and the account.",
            "Fees for disputes, chargebacks and other PayPal products are not modelled.",
        ],
        "limits_es": [
            "El margen de conversión del 3% es el extremo bajo del rango 3%–4% que aparece en las fuentes; el margen real depende de la moneda y de la cuenta.",
            "No se modelan las comisiones por disputas, contracargos ni otros productos de PayPal.",
        ],
        "faqs_en": [
            ("Why are there two PayPal rates in the selector?",
             "PayPal Checkout and invoices are charged 3.49% + $0.49, while standard card payments are charged 2.99% + $0.49. Pick the one that matches how your customers pay."),
            ("Is PayPal's currency conversion part of the fee?",
             "No. It is a separate spread of roughly 3%–4% on top of the exchange rate. Tick \"Currency conversion required\" to add the 3% used by this calculator."),
        ],
        "faqs_es": [
            ("¿Por qué hay dos tarifas de PayPal en el selector?",
             "PayPal Checkout y las facturas cobran 3,49% + $0,49, mientras que los pagos estándar con tarjeta cobran 2,99% + $0,49. Elige la que corresponda a cómo te pagan tus clientes."),
            ("¿La conversión de divisa de PayPal forma parte de la comisión?",
             "No. Es un margen aparte de aproximadamente 3%–4% sobre el tipo de cambio. Marca \"Requiere conversión de divisa\" para añadir el 3% que usa esta calculadora."),
        ],
    },
    "square": {
        "level": "verified",
        "source_url": "https://squareup.com/us/en/pricing",
        "fx_extra_percent": 0.0,
        "rate_options": [
            {"id": "free", "label_en": "Square Free · online & invoices", "label_es": "Square Free · online y facturas", "percent_fee": 3.3, "fixed_fee": 0.30, "currency": "USD"},
            {"id": "plus", "label_en": "Square Plus / Premium · online & invoices", "label_es": "Square Plus / Premium · online y facturas", "percent_fee": 2.9, "fixed_fee": 0.30, "currency": "USD"},
        ],
        "note_en": "US rates. Square Free charges 3.3% + 30¢ for online sales and invoices; Square Plus and Premium (paid plans) charge 2.9% + 30¢. The online API is 2.9% + 30¢ on every plan. The international add-on is an estimate.",
        "note_es": "Tarifas de EE. UU. Square Free cobra 3,3% + 30¢ en ventas online y facturas; Square Plus y Premium (planes de pago) cobran 2,9% + 30¢. La API online es 2,9% + 30¢ en todos los planes. El recargo internacional es una estimación.",
        "limits_en": [
            "Only online sales and invoices are modelled. In-person card payments have different rates.",
            "The monthly cost of the paid plans is not included in the fee.",
        ],
        "limits_es": [
            "Solo se modelan las ventas online y las facturas. Los pagos con tarjeta en persona tienen otras tarifas.",
            "El costo mensual de los planes de pago no está incluido en la comisión.",
        ],
        "faqs_en": [
            ("Should I use the Square Free or the Plus rate?",
             "Square Free charges 3.3% + $0.30 for online sales and invoices; Plus and Premium charge 2.9% + $0.30 but are paid plans with a monthly fee. Use the Plus rate only if you already pay for that plan."),
        ],
        "faqs_es": [
            ("¿Debo usar la tarifa de Square Free o la de Plus?",
             "Square Free cobra 3,3% + $0,30 en ventas online y facturas; Plus y Premium cobran 2,9% + $0,30 pero son planes de pago con cuota mensual. Usa la tarifa Plus solo si ya pagas ese plan."),
        ],
    },
    "shopify": {
        "level": "cross-checked",
        "source_url": "https://www.shopify.com/pricing",
        "fx_extra_percent": 0.0,
        "rate_options": [
            {"id": "basic",    "label_en": "Basic plan · online standard cards",    "label_es": "Plan Basic · tarjetas estándar online",    "percent_fee": 2.9, "fixed_fee": 0.30, "currency": "USD"},
            {"id": "grow",     "label_en": "Grow plan · online standard cards",     "label_es": "Plan Grow · tarjetas estándar online",     "percent_fee": 2.7, "fixed_fee": 0.30, "currency": "USD"},
            {"id": "advanced", "label_en": "Advanced plan · online standard cards", "label_es": "Plan Advanced · tarjetas estándar online", "percent_fee": 2.5, "fixed_fee": 0.30, "currency": "USD"},
        ],
        "note_en": "US online standard-card rates by plan: Basic 2.9% + 30¢, Grow 2.7% + 30¢, Advanced 2.5% + 30¢ (premium cards cost more). The monthly plan fee is not included. The international add-on is an estimate.",
        "note_es": "Tarifas de tarjetas estándar online en EE. UU. por plan: Basic 2,9% + 30¢, Grow 2,7% + 30¢, Advanced 2,5% + 30¢ (las tarjetas premium cuestan más). No incluye la cuota mensual del plan. El recargo internacional es una estimación.",
        "limits_en": [
            "Premium cards cost more than the standard-card rates shown.",
            "The monthly Shopify plan fee, and any extra fee charged when you use a third-party payment gateway, are not modelled.",
        ],
        "limits_es": [
            "Las tarjetas premium cuestan más que las tarifas de tarjeta estándar mostradas.",
            "La cuota mensual del plan de Shopify y cualquier cargo adicional por usar una pasarela de pago de terceros no se modelan.",
        ],
        "faqs_en": [
            ("Does my Shopify plan change the card rate?",
             "Yes. For online standard cards in the US, Basic is 2.9% + $0.30, Grow is 2.7% + $0.30 and Advanced is 2.5% + $0.30. Pick your plan in the Plan / Region selector."),
        ],
        "faqs_es": [
            ("¿Mi plan de Shopify cambia la tarifa de tarjetas?",
             "Sí. Para tarjetas estándar online en EE. UU., Basic es 2,9% + $0,30, Grow 2,7% + $0,30 y Advanced 2,5% + $0,30. Elige tu plan en el selector Plan / Región."),
        ],
    },
}

# ── Estimaciones con matices conocidos (tarifa base sin cambios, pero con explicación honesta) ──
ESTIMATE_NOTES = {
    "wise": {
        "note_en": "Wise does not publish a single percentage-plus-fixed rate for receiving money. Receiving USD by ACH is free, a USD wire costs a fixed $6.11, and currency conversion is a variable percentage that depends on the currency pair (typically under 1%). 0.65% + $0.45 is an illustrative blended estimate, not an official Wise price.",
        "note_es": "Wise no publica una tarifa única de porcentaje más cargo fijo para recibir dinero. Recibir USD por ACH es gratis, un giro (wire) en USD cuesta $6,11 fijos y la conversión de divisa es un porcentaje variable según el par de monedas (normalmente menos de 1%). 0,65% + $0,45 es una estimación combinada ilustrativa, no un precio oficial de Wise.",
        "source_url": "https://wise.com/us/pricing/business/receive",
        "limits_en": ["Wise is not a card processor: the fee you pay depends on how the money arrives (ACH, wire or conversion), so a single percentage cannot describe it."],
        "limits_es": ["Wise no es un procesador de tarjetas: la comisión depende de cómo llega el dinero (ACH, giro o conversión), por lo que un solo porcentaje no puede describirla."],
        "faqs_en": [("Why doesn't Wise have a single fee percentage?",
                     "Receiving USD by ACH is free, a USD wire costs a fixed $6.11, and conversions carry a variable percentage by currency pair. The 0.65% + $0.45 used here is an illustrative blend, so check the amount Wise shows before you send or receive.")],
        "faqs_es": [("¿Por qué Wise no tiene un porcentaje único?",
                     "Recibir USD por ACH es gratis, un giro (wire) en USD cuesta $6,11 fijos y las conversiones llevan un porcentaje variable según el par de monedas. El 0,65% + $0,45 que se usa aquí es una mezcla ilustrativa; revisa el importe que muestra Wise antes de enviar o recibir.")],
    },
    "upwork": {
        "note_en": "Since May 2025 Upwork charges freelancers a variable service fee of 0%–15% per contract (shown before you submit a proposal). 10% is a typical value, not a fixed price.",
        "note_es": "Desde mayo de 2025 Upwork cobra a los freelancers una comisión variable de 0%–15% por contrato (se muestra antes de enviar la propuesta). 10% es un valor típico, no un precio fijo.",
        "source_url": "https://upwork.com",
        "limits_en": ["The fee changes by contract, so your real rate can be anywhere between 0% and 15%."],
        "limits_es": ["La comisión cambia según el contrato, así que tu tarifa real puede estar entre 0% y 15%."],
        "faqs_en": [("Is Upwork's fee fixed at 10%?",
                     "No. Upwork now applies a variable fee between 0% and 15% per contract. Use the custom-rate option with the percentage Upwork shows on your contract for an exact result.")],
        "faqs_es": [("¿La comisión de Upwork es fija del 10%?",
                     "No. Upwork aplica ahora una comisión variable de entre 0% y 15% por contrato. Usa la tarifa personalizada con el porcentaje que Upwork muestra en tu contrato para un resultado exacto.")],
    },
}

GENERIC_NOTE_EN = "Estimated rate: not independently re-checked in the {month} review. Platforms change fees often and many depend on plan, category or country. Confirm on the official pricing page before relying on it."
GENERIC_NOTE_ES = "Tarifa estimada: no se volvió a comprobar de forma independiente en la revisión de {month}. Las plataformas cambian sus tarifas con frecuencia y muchas dependen del plan, la categoría o el país. Confírmala en la página oficial de precios antes de usarla."

# Una frase por categoría: quién paga y cuándo (solo descripción general, sin cifras)
CATEGORY_HOW = {
    "Payment Processor": ("The fee is deducted from each payment before the money reaches you.", "La comisión se descuenta de cada pago antes de que el dinero llegue a ti."),
    "Global Transfers": ("The cost depends on how the money arrives and on any currency conversion.", "El costo depende de cómo llega el dinero y de si hay conversión de divisa."),
    "E-Commerce": ("The fee is taken from each sale; listing, shipping or advertising costs may be charged separately.", "La comisión se descuenta de cada venta; los costos de publicación, envío o publicidad pueden cobrarse aparte."),
    "SaaS & Merchant of Record": ("A merchant of record sells on your behalf and keeps its fee from each sale.", "Un merchant of record vende en tu nombre y retiene su comisión de cada venta."),
    "Creator Economy": ("The platform keeps its share of each payment; check which parts of the fee your rate includes.", "La plataforma retiene su parte de cada pago; comprueba qué partes de la comisión incluye tu tarifa."),
    "Freelance Marketplace": ("The marketplace keeps a share of what you earn on each contract.", "El marketplace retiene una parte de lo que ganas en cada contrato."),
    "Business Banking": ("Costs depend on the type of transfer (ACH, wire or international).", "Los costos dependen del tipo de transferencia (ACH, giro o internacional)."),
    "Global Payroll & Freelance": ("Costs depend on the plan and on how each contractor is paid.", "Los costos dependen del plan y de cómo se paga a cada contratista."),
    "Crypto Payments": ("The fee is taken from each payment received.", "La comisión se descuenta de cada pago recibido."),
}


def r2(x):
    """Redondeo a centavos 'half up' (igual que Math.round del JavaScript de la calculadora)."""
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def worked(amount, pct, fix):
    """Cálculo con la misma fórmula que usa la calculadora."""
    p = Decimal(str(pct)) / 100
    fee = r2(Decimal(str(amount)) * p + Decimal(str(fix)))
    net = r2(max(Decimal(0), Decimal(str(amount)) - Decimal(str(fee))))
    reverse = r2((Decimal(str(amount)) + Decimal(str(fix))) / (1 - p)) if p < 1 else amount
    return fee, net, reverse


STATUS = {
    "verified":      ("checked on the provider's official pricing page in {m}", "contrastada en la página oficial de precios del proveedor en {m}"),
    "cross-checked": ("cross-checked in {m} against several independent sources; the official page is linked but was not opened directly", "contrastada en {m} con varias fuentes independientes; la página oficial está enlazada pero no se abrió directamente"),
    "estimate":      ("an estimate that has not been verified against the official site; confirm it before relying on it", "una estimación que no se ha verificado en el sitio oficial; confírmala antes de fiarte de ella"),
}


def build_catalog():
    platforms = {}
    counts = {"verified": 0, "cross-checked": 0, "estimate": 0}
    for key, name, cat, pct, fix, intl, url in RAW_PLATFORMS:
        c = CHECKED.get(key)
        e = ESTIMATE_NOTES.get(key, {})
        if c:
            confidence, checked = c["level"], REVIEW_DATE[:7]
            source_url, fx = c["source_url"], c["fx_extra_percent"]
            options = c["rate_options"]
            note_en, note_es = c["note_en"], c["note_es"]
            limits_en, limits_es = c["limits_en"], c["limits_es"]
            extra_en, extra_es = c["faqs_en"], c["faqs_es"]
        else:
            confidence, checked = "estimate", None
            fx, options = 0.0, []
            note_en = e.get("note_en", GENERIC_NOTE_EN.format(month=REVIEW_MONTH))
            note_es = e.get("note_es", GENERIC_NOTE_ES.format(month=REVIEW_MONTH))
            source_url = e.get("source_url", url)
            limits_en, limits_es = e.get("limits_en", []), e.get("limits_es", [])
            extra_en, extra_es = e.get("faqs_en", []), e.get("faqs_es", [])
        counts[confidence] += 1

        fee1000, net1000, rev1000 = worked(1000, pct, fix)
        fee_on_rev, net_on_rev, _ = worked(rev1000, pct, fix)
        st_en, st_es = STATUS[confidence]
        st_en, st_es = st_en.format(m=REVIEW_MONTH), st_es.format(m=REVIEW_MONTH)
        how_en, how_es = CATEGORY_HOW.get(cat, ("", ""))

        faqs_en = [
            {"q": f"What rate does this calculator use for {name}, and how reliable is it?",
             "a": f"It uses {pct}% + ${fix:.2f} per transaction, {st_en}." + (f" International cards add {intl}%" + (f" and currency conversion about {fx}%." if fx else ".") if intl else (f" Currency conversion adds about {fx}%." if fx else " No separate international surcharge is modelled."))},
            {"q": f"How much should I invoice to receive exactly $1,000 on {name}?",
             "a": f"Invoice ${rev1000:,.2f}. The formula is (desired amount + ${fix:.2f}) ÷ (1 − {pct / 100:.4f}), so (1,000 + {fix:.2f}) ÷ {1 - pct / 100:.4f} = ${rev1000:,.2f}. {name} then deducts ${fee_on_rev:,.2f} and you receive ${net_on_rev:,.2f}."},
        ] + [{"q": q, "a": a} for q, a in extra_en]
        faqs_es = [
            {"q": f"¿Qué tarifa usa esta calculadora para {name} y qué tan fiable es?",
             "a": f"Usa {pct}% + ${fix:.2f} por transacción, {st_es}." + (f" Las tarjetas internacionales suman {intl}%" + (f" y la conversión de divisa cerca de {fx}%." if fx else ".") if intl else (f" La conversión de divisa suma cerca de {fx}%." if fx else " No se modela ningún recargo internacional por separado."))},
            {"q": f"¿Cuánto debo facturar para recibir exactamente $1,000 en {name}?",
             "a": f"Factura ${rev1000:,.2f}. La fórmula es (monto deseado + ${fix:.2f}) ÷ (1 − {pct / 100:.4f}), es decir (1,000 + {fix:.2f}) ÷ {1 - pct / 100:.4f} = ${rev1000:,.2f}. {name} descuenta entonces ${fee_on_rev:,.2f} y recibes ${net_on_rev:,.2f}."},
        ] + [{"q": q, "a": a} for q, a in extra_es]

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
            "limits": {"en": limits_en, "es": limits_es},
            "category_how": {"en": how_en, "es": how_es},
            "seo": {
                "en": {
                    "title": f"{name} Fee Calculator (2026) - Net Payout & Invoice Calculator",
                    "h1": f"{name} Fee Calculator",
                    "desc": f"Calculate exact {name} fees ({pct}% + ${fix:.2f}). See your net payout on any amount and how much to invoice to avoid losing money to processing costs.",
                    "guide": f"{how_en} {note_en}".strip(),
                    "faqs": faqs_en,
                },
                "es": {
                    "title": f"Calculadora de Comisiones {name} (2026) - Neto Exacto y Facturación",
                    "h1": f"Calculadora de Comisiones de {name}",
                    "desc": f"Calcula al instante las comisiones de {name} ({pct}% + ${fix:.2f}). Descubre cuánto recibes neto y cuánto debes cobrar para no perder dinero.",
                    "guide": f"{how_es} {note_es}".strip(),
                    "faqs": faqs_es,
                },
            },
        }

    out_path = Path(__file__).resolve().parent / "engine" / "data" / "platforms.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "last_reviewed": REVIEW_DATE,
            "review_month": REVIEW_MONTH,
            "verified_count": counts["verified"],
            "crosschecked_count": counts["cross-checked"],
            "estimate_count": counts["estimate"],
            "total_count": len(platforms),
        },
        "platforms": platforms,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Exito: {len(platforms)} plataformas en {out_path} ({counts['verified']} verificadas en fuente oficial, {counts['cross-checked']} contrastadas con fuentes independientes, {counts['estimate']} estimadas)")


if __name__ == "__main__":
    build_catalog()
