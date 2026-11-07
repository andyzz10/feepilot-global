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
    ("shopify", "Shopify Payments", "E-Commerce", 2.9, 0.30, 1.0, "https://shopify.com"),
    ("square", "Square", "Payment Processor", 3.3, 0.30, 1.0, "https://squareup.com"),
    ("lemonsqueezy", "Lemon Squeezy", "SaaS & Merchant of Record", 5.0, 0.50, 1.5, "https://lemonsqueezy.com"),
    ("paddle", "Paddle", "SaaS & Merchant of Record", 5.0, 0.50, 0.0, "https://paddle.com"),
    ("gumroad", "Gumroad", "Creator Economy", 10.0, 0.50, 0.0, "https://gumroad.com"),
    ("patreon", "Patreon", "Creator Economy", 12.9, 0.30, 0.0, "https://patreon.com"),
    ("upwork", "Upwork", "Freelance Marketplace", 10.0, 0.00, 0.0, "https://upwork.com"),
    ("fiverr", "Fiverr", "Freelance Marketplace", 20.0, 0.00, 0.0, "https://fiverr.com"),
    ("etsy", "Etsy", "E-Commerce", 9.5, 0.25, 0.0, "https://etsy.com"),
    ("ebay", "eBay Managed Payments", "E-Commerce", 13.25, 0.40, 1.65, "https://ebay.com"),
    ("amazon", "Amazon Seller Referral", "E-Commerce", 15.0, 0.00, 0.0, "https://sell.amazon.com"),
    ("tiktokshop", "TikTok Shop", "E-Commerce", 6.0, 0.00, 0.0, "https://seller.tiktok.com"),
    ("revolut", "Revolut Business", "Global Transfers", 1.0, 0.20, 0.0, "https://revolut.com"),
    ("mercury", "Mercury Wire & ACH", "Business Banking", 0.0, 0.00, 0.0, "https://mercury.com"),
    ("deel", "Deel Contractor", "Global Payroll & Freelance", 1.0, 0.00, 0.0, "https://deel.com"),
    ("skrill", "Skrill", "Payment Processor", 2.99, 0.00, 0.0, "https://skrill.com"),
    ("venmo", "Venmo Business", "Payment Processor", 1.9, 0.10, 0.0, "https://venmo.com"),
    ("cashapp", "Cash App Business", "Payment Processor", 2.75, 0.00, 0.0, "https://cash.app"),
    ("kofi", "Ko-fi", "Creator Economy", 7.9, 0.30, 0.0, "https://ko-fi.com"),
    ("substack", "Substack", "Creator Economy", 12.9, 0.30, 0.0, "https://substack.com"),
    ("coinbase", "Coinbase Business", "Crypto Payments", 1.0, 0.00, 0.0, "https://www.coinbase.com/business"),
]

# ── Datos contrastados (solo lo que realmente se comprobó en la revisión) ─────────────
# level            → "verified" (página oficial) | "cross-checked" (fuentes independientes)
# fx_extra_percent → recargo SEPARADO por conversión de divisa (distinto al de tarjeta internacional)
# rate_options     → planes / regiones con tarifa propia (la primera = tarifa por defecto de la ficha)
# limits / faqs    → texto específico de la plataforma (en/es); solo hechos comprobados
DETAILS = {
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
        "level": "verified",
        "source_url": "https://www.paypal.com/us/business/paypal-business-fees",
        "fx_extra_percent": 3.0,
        "rate_options": [
            {"id": "checkout", "label_en": "US · PayPal Checkout / invoices", "label_es": "EE. UU. · PayPal Checkout / facturas", "percent_fee": 3.49, "fixed_fee": 0.49, "currency": "USD"},
            {"id": "card",     "label_en": "US · standard card payments",     "label_es": "EE. UU. · pagos estándar con tarjeta", "percent_fee": 2.99, "fixed_fee": 0.49, "currency": "USD"},
            {"id": "qr",       "label_en": "US · QR code payments", "label_es": "EE. UU. · pagos con código QR", "percent_fee": 2.29, "fixed_fee": 0.49, "currency": "USD"},
            {"id": "paylater", "label_en": "US · Pay Later options", "label_es": "EE. UU. · opciones Pay Later", "percent_fee": 4.99, "fixed_fee": 0.49, "currency": "USD"},
        ],
        "note_en": "US merchant rates from PayPal's own business fees page: PayPal Checkout, Guest Checkout and Pay with Venmo 3.49% + $0.49, standard credit and debit card payments 2.99% + $0.49, QR code payments 2.29% + $0.49 and Pay Later options 4.99% + $0.49. International commercial payments add 1.5%. PayPal's currency conversion spread is roughly 3%–4% on top of the exchange rate according to independent sources; the calculator uses 3%.",
        "note_es": "Tarifas comerciales de EE. UU. de la propia página de comisiones de PayPal: PayPal Checkout, Guest Checkout y Pay with Venmo 3,49% + $0,49, pagos estándar con tarjeta de crédito y débito 2,99% + $0,49, pagos con código QR 2,29% + $0,49 y opciones Pay Later 4,99% + $0,49. Los pagos comerciales internacionales suman 1,5%. Según fuentes independientes, el margen de conversión de divisa de PayPal ronda el 3%–4% sobre el tipo de cambio; la calculadora usa 3%.",
        "limits_en": [
            "The 3% conversion spread comes from independent sources (the low end of a 3%–4% range), not from PayPal's fee page; the real spread depends on the currency and the account.",
            "Fees for disputes, chargebacks and other PayPal products are not modelled.",
        ],
        "limits_es": [
            "El margen de conversión del 3% proviene de fuentes independientes (el extremo bajo de un rango de 3%–4%), no de la página de comisiones de PayPal; el margen real depende de la moneda y de la cuenta.",
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
        "note_en": "US online standard-card rates by plan: Basic 2.9% + 30¢, Grow 2.7% + 30¢, Advanced 2.5% + 30¢ (premium cards cost more). International cards add 1% according to independent 2026 sources. The monthly plan fee is not included.",
        "note_es": "Tarifas de tarjetas estándar online en EE. UU. por plan: Basic 2,9% + 30¢, Grow 2,7% + 30¢, Advanced 2,5% + 30¢ (las tarjetas premium cuestan más). Las tarjetas internacionales suman 1% según fuentes independientes de 2026. No incluye la cuota mensual del plan.",
        "limits_en": [
            "Premium cards cost more than the standard-card rates shown.",
            "The monthly Shopify plan fee is not modelled. If you use an outside payment provider instead of Shopify Payments, Shopify adds its own fee of 2% on Basic, 1% on Grow or 0.6% on Advanced on top of the provider's charges.",
        ],
        "limits_es": [
            "Las tarjetas premium cuestan más que las tarifas de tarjeta estándar mostradas.",
            "La cuota mensual del plan de Shopify no se modela. Si usas un proveedor de pago externo en lugar de Shopify Payments, Shopify añade su propia comisión de 2% en Basic, 1% en Grow o 0,6% en Advanced, además de los cargos del proveedor.",
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
    # ───────── Revisión de octubre de 2026: Patreon, Etsy, Gumroad (y eBay como estimación mejorada) ─────────
    "patreon": {
        "level": "verified",
        "source_url": "https://support.patreon.com/hc/articles/11111747095181",
        "fx_extra_percent": 2.5,
        "rate_options": [
            {"id": "std",   "label_en": "New creators · pledges over $3 (10% platform + 2.9% + $0.30)", "label_es": "Creadores nuevos · aportes de más de $3 (10% plataforma + 2,9% + $0,30)", "percent_fee": 12.9, "fixed_fee": 0.30, "currency": "USD"},
            {"id": "small", "label_en": "Pledges of $3 or less (10% platform + 5% + $0.10)", "label_es": "Aportes de $3 o menos (10% plataforma + 5% + $0,10)", "percent_fee": 15.0, "fixed_fee": 0.10, "currency": "USD"},
        ],
        "note_en": "Creators who published their page after August 4, 2025 pay a 10% platform fee (Patreon's creator fees page), plus card processing of 2.9% + $0.30 on pledges over $3. Pledges of $3 or less use a higher processing rate (5% + $0.10 according to independent sources). The calculator combines both into 12.9% + $0.30. Currency conversion adds about 2.5%.",
        "note_es": "Los creadores que publicaron su página después del 4 de agosto de 2025 pagan una comisión de plataforma del 10% (página de comisiones de Patreon), más el procesamiento de tarjeta de 2,9% + $0,30 en aportes de más de $3. Los aportes de $3 o menos usan una tarifa de procesamiento mayor (5% + $0,10 según fuentes independientes). La calculadora suma ambos en 12,9% + $0,30. La conversión de divisa añade cerca de 2,5%.",
        "limits_en": [
            "Creators who published before August 4, 2025 may be on a legacy plan with a different platform fee, and unpublishing the page moves you to the 10% plan.",
            "Payout fees and taxes on creator fees are not included. The 2.5% currency-conversion figure and the rate for pledges of $3 or less come from independent sources, not from Patreon's page.",
        ],
        "limits_es": [
            "Los creadores que publicaron antes del 4 de agosto de 2025 pueden tener un plan antiguo con otra comisión de plataforma, y despublicar la página te pasa al plan del 10%.",
            "No se incluyen las comisiones de retiro ni los impuestos sobre las comisiones. La cifra de 2,5% por conversión de divisa y la tarifa de aportes de $3 o menos provienen de fuentes independientes, no de la página de Patreon.",
        ],
        "faqs_en": [
            ("What does Patreon take from a new creator?",
             "A 10% platform fee plus card processing. On a US card pledge over $3 that is 10% + 2.9% + $0.30 = 12.9% + $0.30, so on $10 Patreon and the processor keep $1.59 and you receive $8.41."),
            ("Do I pay less if I joined Patreon before August 2025?",
             "Possibly. Creators who published before August 4, 2025 may remain on a legacy plan with a different platform fee, but unpublishing your page moves you to the standard 10% plan. Check your own account settings."),
        ],
        "faqs_es": [
            ("¿Cuánto retiene Patreon a un creador nuevo?",
             "Una comisión de plataforma del 10% más el procesamiento de la tarjeta. En un aporte de más de $3 con tarjeta de EE. UU. son 10% + 2,9% + $0,30 = 12,9% + $0,30, así que sobre $10 se quedan $1,59 y recibes $8,41."),
            ("¿Pago menos si me uní a Patreon antes de agosto de 2025?",
             "Posiblemente. Los creadores que publicaron antes del 4 de agosto de 2025 pueden seguir en un plan antiguo con otra comisión de plataforma, pero despublicar tu página te pasa al plan estándar del 10%. Revisa los ajustes de tu propia cuenta."),
        ],
    },
    "etsy": {
        "level": "verified",
        "source_url": "https://www.etsy.com/legal/fees",
        "fx_extra_percent": 2.5,
        "rate_options": [
            {"id": "us",         "label_en": "US sellers · transaction fee + payment processing", "label_es": "Vendedores de EE. UU. · comisión por transacción + procesamiento", "percent_fee": 9.5, "fixed_fee": 0.25, "currency": "USD"},
            {"id": "us_listing", "label_en": "US sellers · including the $0.20 listing fee",       "label_es": "Vendedores de EE. UU. · incluida la tarifa de publicación de $0,20", "percent_fee": 9.5, "fixed_fee": 0.45, "currency": "USD"},
            {"id": "uk",         "label_en": "UK sellers · transaction fee + payment processing", "label_es": "Vendedores del Reino Unido · comisión por transacción + procesamiento", "percent_fee": 10.5, "fixed_fee": 0.20, "currency": "GBP"},
        ],
        "note_en": "For US sellers Etsy charges a 6.5% transaction fee plus payment processing of 3% + $0.25, which is 9.5% + $0.25 per sale. Each listing also costs $0.20 when it is published or renewed (the second option adds it). UK sellers pay 4% + £0.20 processing, so 10.5% + £0.20 with the transaction fee. Currency conversion adds 2.5% when the listing currency differs from your payment account currency.",
        "note_es": "Para vendedores de EE. UU., Etsy cobra una comisión por transacción del 6,5% más el procesamiento de pagos de 3% + $0,25, es decir 9,5% + $0,25 por venta. Cada publicación cuesta además $0,20 al publicarse o renovarse (la segunda opción la suma). Los vendedores del Reino Unido pagan 4% + £0,20 de procesamiento, así que 10,5% + £0,20 con la comisión por transacción. La conversión de divisa suma 2,5% cuando la moneda del anuncio difiere de la de tu cuenta de pagos.",
        "limits_en": [
            "The fees apply to the whole order total: item price plus shipping, gift wrapping and personalization. Enter the full amount the buyer pays.",
            "Offsite Ads (15% for shops under $10,000 in yearly sales), subscriptions, shipping labels and the UK regulatory operating fee are not modelled.",
            "Etsy states that payment processing varies by bank country. The US figures come from Etsy's own pages; the UK option and the 2.5% currency-conversion fee come from independent sources.",
        ],
        "limits_es": [
            "Las comisiones se aplican al total del pedido: precio del artículo más envío, envoltorio de regalo y personalización. Introduce el monto completo que paga el comprador.",
            "No se modelan Offsite Ads (15% para tiendas con menos de $10.000 de ventas anuales), suscripciones, etiquetas de envío ni la tarifa regulatoria del Reino Unido.",
            "Etsy indica que el procesamiento de pagos varía según el país del banco. Las cifras de EE. UU. vienen de las propias páginas de Etsy; la opción del Reino Unido y la comisión de conversión del 2,5% vienen de fuentes independientes.",
        ],
        "faqs_en": [
            ("Why is Etsy's fee higher than the 6.5% transaction fee?",
             "The 6.5% transaction fee is only one part. Etsy Payments adds 3% + $0.25 for US sellers, so a sale costs 9.5% + $0.25 before the $0.20 listing fee. On a $100 order that is $9.75, or $9.95 with the listing fee."),
            ("Does the Etsy fee include shipping?",
             "Yes. The transaction fee and the payment processing fee are calculated on the full order total, including shipping, gift wrapping and personalization, so enter what the buyer actually pays."),
        ],
        "faqs_es": [
            ("¿Por qué la comisión de Etsy es mayor que el 6,5% de transacción?",
             "El 6,5% de transacción es solo una parte. Etsy Payments suma 3% + $0,25 para vendedores de EE. UU., así que una venta cuesta 9,5% + $0,25 antes de la tarifa de publicación de $0,20. En un pedido de $100 son $9,75, o $9,95 con la tarifa de publicación."),
            ("¿La comisión de Etsy incluye el envío?",
             "Sí. La comisión por transacción y la de procesamiento se calculan sobre el total del pedido, con envío, envoltorio de regalo y personalización, así que introduce lo que paga realmente el comprador."),
        ],
    },
    "gumroad": {
        "level": "cross-checked",
        "source_url": "https://gumroad.com/pricing",
        "fx_extra_percent": 0.0,
        "rate_options": [
            {"id": "direct",   "label_en": "Direct sales · Gumroad's own fee",            "label_es": "Ventas directas · comisión propia de Gumroad", "percent_fee": 10.0, "fixed_fee": 0.50, "currency": "USD"},
            {"id": "direct_cp", "label_en": "Direct sales · including card processing",  "label_es": "Ventas directas · incluido el procesamiento de tarjeta", "percent_fee": 12.9, "fixed_fee": 0.80, "currency": "USD"},
            {"id": "discover", "label_en": "Gumroad Discover sales (processing included)", "label_es": "Ventas por Gumroad Discover (procesamiento incluido)", "percent_fee": 30.0, "fixed_fee": 0.0, "currency": "USD"},
        ],
        "note_en": "Direct sales (your own link or profile) cost 10% + $0.50 with no monthly fee. According to independent 2026 sources, card processing of about 2.9% + $0.30 is charged on top, which brings a card sale to roughly 12.9% + $0.80 (second option). Sales that come through Gumroad Discover cost a flat 30% with processing included.",
        "note_es": "Las ventas directas (tu propio enlace o perfil) cuestan 10% + $0,50 sin cuota mensual. Según fuentes independientes de 2026, el procesamiento de tarjeta de aproximadamente 2,9% + $0,30 se cobra aparte, lo que lleva una venta con tarjeta a cerca de 12,9% + $0,80 (segunda opción). Las ventas que llegan por Gumroad Discover cuestan un 30% fijo con el procesamiento incluido.",
        "limits_en": [
            "Gumroad does not refund its fees when you refund a buyer.",
            "The card-processing figure comes from independent sources, not from Gumroad's own page, so confirm it in your payout reports.",
        ],
        "limits_es": [
            "Gumroad no devuelve sus comisiones cuando reembolsas a un comprador.",
            "La cifra de procesamiento de tarjeta proviene de fuentes independientes y no de la página de Gumroad, así que confírmala en tus informes de pagos.",
        ],
        "faqs_en": [
            ("Is Gumroad's 10% + $0.50 the total cost of a sale?",
             "It is Gumroad's own cut on direct sales. Independent sources report card processing of about 2.9% + $0.30 on top, so a card sale costs roughly 12.9% + $0.80. Sales that come through Discover cost a flat 30% with processing included."),
        ],
        "faqs_es": [
            ("¿El 10% + $0,50 de Gumroad es el costo total de una venta?",
             "Es la parte propia de Gumroad en ventas directas. Fuentes independientes indican un procesamiento de tarjeta de cerca de 2,9% + $0,30 adicional, así que una venta con tarjeta cuesta aproximadamente 12,9% + $0,80. Las ventas por Discover cuestan un 30% fijo con el procesamiento incluido."),
        ],
    },
    "ebay": {
        "level": "estimate",
        "source_url": "https://www.ebay.com/help/selling/fees-credits-invoices/selling-fees?id=4822",
        "fx_extra_percent": 0.0,
        "rate_options": [
            {"id": "over10", "label_en": "Most categories · orders over $10",  "label_es": "La mayoría de categorías · pedidos de más de $10", "percent_fee": 13.25, "fixed_fee": 0.40, "currency": "USD"},
            {"id": "upto10", "label_en": "Most categories · orders of $10 or less", "label_es": "La mayoría de categorías · pedidos de $10 o menos", "percent_fee": 13.25, "fixed_fee": 0.30, "currency": "USD"},
        ],
        "note_en": "eBay charges one final value fee as a percentage of the total sale (item price plus shipping and tax) plus a per-order fee: $0.40 on orders over $10 and $0.30 on orders of $10 or less. The percentage depends on the category and your store plan; 13.25% is the figure most sources give for most categories, but some 2026 sources quote 13.6%, so this stays an estimate.",
        "note_es": "eBay cobra una sola comisión de valor final como porcentaje de la venta total (precio del artículo más envío e impuestos) más una tarifa por pedido: $0,40 en pedidos de más de $10 y $0,30 en pedidos de $10 o menos. El porcentaje depende de la categoría y de tu plan de tienda; 13,25% es la cifra que dan la mayoría de las fuentes para la mayoría de categorías, pero algunas fuentes de 2026 citan 13,6%, por eso sigue siendo una estimación.",
        "limits_en": [
            "The final value fee changes by category (typically 12.9%–15%) and by store subscription, and sellers below standard performance pay more.",
            "Optional promoted-listing fees and insertion fees are not included. The international add-on is an estimate.",
        ],
        "limits_es": [
            "La comisión de valor final cambia según la categoría (normalmente 12,9%–15%) y la suscripción de tienda, y los vendedores por debajo del estándar pagan más.",
            "No se incluyen las tarifas opcionales de anuncios promocionados ni las de publicación. El recargo internacional es una estimación.",
        ],
        "faqs_en": [
            ("Why does eBay show two different per-order fees?",
             "eBay's per-order fee is $0.30 on orders of $10 or less and $0.40 on orders over $10 (increased from $0.30 in March 2024). The calculator defaults to the $0.40 case; pick the other option for small orders."),
        ],
        "faqs_es": [
            ("¿Por qué eBay muestra dos tarifas por pedido distintas?",
             "La tarifa por pedido de eBay es de $0,30 en pedidos de $10 o menos y de $0,40 en pedidos de más de $10 (subió de $0,30 en marzo de 2024). La calculadora usa por defecto el caso de $0,40; elige la otra opción para pedidos pequeños."),
        ],
    },
    # ───────── Segunda tanda de revisión: Paddle, Lemon Squeezy y Fiverr (contrastadas con fuentes independientes) ─────────
    "paddle": {
        "level": "cross-checked",
        "source_url": "https://www.paddle.com/pricing",
        "fx_extra_percent": 0.0,
        "note_en": "Paddle is a merchant of record: it sells on your behalf and handles tax collection and remittance. It charges 5% + $0.50 per checkout transaction, all-inclusive, with no monthly platform fee and no separate international surcharge. Larger businesses can negotiate custom pricing.",
        "note_es": "Paddle es un merchant of record: vende en tu nombre y se encarga de cobrar y remitir los impuestos. Cobra 5% + $0,50 por transacción de checkout, todo incluido, sin cuota mensual de plataforma y sin recargo internacional aparte. Las empresas más grandes pueden negociar precios personalizados.",
        "limits_en": ["Payout and chargeback fees are not modelled, and custom enterprise pricing can differ from the standard rate."],
        "limits_es": ["No se modelan las comisiones de retiro ni de contracargos, y el precio personalizado para empresas grandes puede diferir de la tarifa estándar."],
        "faqs_en": [("Does Paddle charge extra for international customers?",
                     "Not as a separate surcharge: 5% + $0.50 applies whatever the customer's country, because Paddle handles the tax compliance inside that fee. Lemon Squeezy, by contrast, adds 1.5% on international transactions.")],
        "faqs_es": [("¿Paddle cobra más por clientes internacionales?",
                     "No como recargo aparte: 5% + $0,50 se aplica sea cual sea el país del cliente, porque Paddle incluye el cumplimiento fiscal dentro de esa comisión. Lemon Squeezy, en cambio, suma 1,5% en transacciones internacionales.")],
    },
    "lemonsqueezy": {
        "level": "cross-checked",
        "source_url": "https://www.lemonsqueezy.com/pricing",
        "fx_extra_percent": 0.0,
        "note_en": "Lemon Squeezy is a merchant of record (owned by Stripe since July 2024). It charges 5% + $0.50 per transaction, plus 1.5% on international transactions, 1.5% on PayPal payments and 0.5% on subscription payments. Payout fees apply separately.",
        "note_es": "Lemon Squeezy es un merchant of record (propiedad de Stripe desde julio de 2024). Cobra 5% + $0,50 por transacción, más 1,5% en transacciones internacionales, 1,5% en pagos con PayPal y 0,5% en pagos de suscripciones. Las comisiones de retiro se aplican aparte.",
        "limits_en": ["The PayPal (+1.5%) and subscription (+0.5%) surcharges are not modelled: add them with the custom-rate option. Payout fees, for example 1% to a non-US bank account, are not included."],
        "limits_es": ["Los recargos de PayPal (+1,5%) y de suscripciones (+0,5%) no se modelan: añádelos con la opción de tarifa personalizada. No se incluyen las comisiones de retiro, por ejemplo 1% a una cuenta bancaria fuera de EE. UU."],
        "faqs_en": [("Why does Lemon Squeezy cost more than 5% + $0.50?",
                     "The base rate is 5% + $0.50, but international transactions add 1.5%, PayPal payments add 1.5% and subscription payments add 0.5%. A US customer buying a one-off product by card pays only the base rate.")],
        "faqs_es": [("¿Por qué Lemon Squeezy cuesta más que 5% + $0,50?",
                     "La tarifa base es 5% + $0,50, pero las transacciones internacionales suman 1,5%, los pagos con PayPal 1,5% y los pagos de suscripciones 0,5%. Un cliente de EE. UU. que compra un producto único con tarjeta paga solo la tarifa base.")],
    },
    "fiverr": {
        "level": "cross-checked",
        "source_url": "https://www.fiverr.com",
        "fx_extra_percent": 0.0,
        "note_en": "Fiverr keeps a flat 20% of every order, including extras and tips, at every seller level. Buyers pay their own separate service fee on top of the gig price, which does not reduce what you earn.",
        "note_es": "Fiverr se queda un 20% fijo de cada pedido, incluidos extras y propinas, en todos los niveles de vendedor. Los compradores pagan aparte su propia comisión de servicio sobre el precio del gig, que no reduce lo que ganas.",
        "limits_en": ["Withdrawal fees depend on the method (PayPal, Payoneer or bank transfer) and currency conversion can add more; neither is included."],
        "limits_es": ["Las comisiones de retiro dependen del método (PayPal, Payoneer o transferencia bancaria) y la conversión de divisa puede sumar más; ninguna está incluida."],
        "faqs_en": [("Does the buyer's service fee reduce what I earn on Fiverr?",
                     "No. Buyers pay a separate service fee on top of the gig price (independent sources report 5.5% plus a small-order fee), and your 20% is calculated on the gig price. Withdrawal and currency-conversion costs are what take a further share.")],
        "faqs_es": [("¿La comisión de servicio del comprador reduce lo que gano en Fiverr?",
                     "No. Los compradores pagan una comisión de servicio aparte sobre el precio del gig (fuentes independientes indican 5,5% más una tarifa por pedidos pequeños), y tu 20% se calcula sobre el precio del gig. Lo que resta una parte adicional son los costos de retiro y de conversión de divisa.")],
    },
    # ───────── Tercera tanda: Venmo, Cash App, Substack, Ko-fi y Amazon ─────────
    "venmo": {
        "level": "verified",
        "source_url": "https://help.venmo.com/hc/en-us/articles/1500003204302-Business-Profile-Fees-",
        "fx_extra_percent": 0.0,
        "rate_options": [
            {"id": "direct", "label_en": "Payments from another Venmo account", "label_es": "Pagos desde otra cuenta de Venmo", "percent_fee": 1.9, "fixed_fee": 0.10, "currency": "USD"},
            {"id": "tap",    "label_en": "Tap to Pay (contactless)",            "label_es": "Tap to Pay (sin contacto)",         "percent_fee": 2.29, "fixed_fee": 0.10, "currency": "USD"},
        ],
        "note_en": "Venmo's help center says business profiles pay 1.9% + $0.10 on direct payments from another Venmo account, and 2.29% + $0.10 on contactless payments taken with Tap to Pay. The fee applies to payments of $1.00 or more, comes out of the amount your customer sends and is not refunded.",
        "note_es": "El centro de ayuda de Venmo indica que los perfiles de negocio pagan 1,9% + $0,10 en pagos directos desde otra cuenta de Venmo y 2,29% + $0,10 en pagos sin contacto con Tap to Pay. La comisión se aplica a pagos de $1,00 o más, se descuenta del monto que envía tu cliente y no se reembolsa.",
        "limits_en": ["Instant transfers to a bank or debit card cost extra (about 1.75% according to an independent source) and are not included.", "Checkout payments made inside an app or website through PayPal's Venmo button follow different rates."],
        "limits_es": ["Las transferencias instantáneas a un banco o tarjeta de débito cuestan aparte (cerca de 1,75% según una fuente independiente) y no están incluidas.", "Los pagos de checkout dentro de una app o sitio web con el botón de Venmo de PayPal siguen otras tarifas."],
        "faqs_en": [("Who pays Venmo's business fee, the customer or me?",
                     "You do. The fee is deducted from the payment your customer sends, so on a $100 payment you receive $98.00 after 1.9% + $0.10. Customers who pay with a credit card do not pay a separate Venmo fee when paying a business profile.")],
        "faqs_es": [("¿Quién paga la comisión de negocio de Venmo, el cliente o yo?",
                     "La pagas tú. La comisión se descuenta del pago que envía tu cliente, así que en un pago de $100 recibes $98,00 tras 1,9% + $0,10. Los clientes que pagan con tarjeta de crédito no pagan una comisión aparte de Venmo al pagar a un perfil de negocio.")],
    },
    "cashapp": {
        "level": "cross-checked",
        "source_url": "https://cash.app/help",
        "fx_extra_percent": 0.0,
        "rate_options": [
            {"id": "credit", "label_en": "Credit card payments", "label_es": "Pagos con tarjeta de crédito", "percent_fee": 2.75, "fixed_fee": 0.0, "currency": "USD"},
            {"id": "debit",  "label_en": "Debit card and Cash App balance payments", "label_es": "Pagos con tarjeta de débito y saldo de Cash App", "percent_fee": 2.5, "fixed_fee": 0.0, "currency": "USD"},
        ],
        "note_en": "Cash App for Business charges a flat percentage with no per-transaction fixed fee: 2.75% on credit card payments and 2.5% on payments made with a debit card or the customer's Cash App balance, according to independent 2026 sources. Instant deposits are reported as free.",
        "note_es": "Cash App for Business cobra un porcentaje plano sin cargo fijo por transacción: 2,75% en pagos con tarjeta de crédito y 2,5% en pagos con tarjeta de débito o saldo de Cash App del cliente, según fuentes independientes de 2026. Los depósitos instantáneos se indican como gratuitos.",
        "limits_en": ["Cash App limits which kinds of businesses can use Cash for Business, and chargeback terms are set in its business terms, which are not modelled."],
        "limits_es": ["Cash App limita qué tipos de negocio pueden usar Cash for Business, y las condiciones de contracargos están en sus términos de negocio, que no se modelan."],
        "faqs_en": [("Which Cash App rate should I use, 2.75% or 2.5%?",
                     "Use 2.75% when customers pay by credit card and 2.5% when they pay with a debit card or their Cash App balance. On a $100 payment you receive $97.25 or $97.50.")],
        "faqs_es": [("¿Qué tarifa de Cash App debo usar, 2,75% o 2,5%?",
                     "Usa 2,75% cuando el cliente paga con tarjeta de crédito y 2,5% cuando paga con tarjeta de débito o con su saldo de Cash App. En un pago de $100 recibes $97,25 o $97,50.")],
    },
    "substack": {
        "level": "verified",
        "source_url": "https://faq.substack.com/p/how-do-paid-subscriptions-on-substack",
        "fx_extra_percent": 0.0,
        "rate_options": [
            {"id": "paid",      "label_en": "Paid subscription · Substack 10% + Stripe 2.9% + $0.30", "label_es": "Suscripción de pago · Substack 10% + Stripe 2,9% + $0,30", "percent_fee": 12.9, "fixed_fee": 0.30, "currency": "USD"},
            {"id": "recurring", "label_en": "Recurring billing · adds Stripe Billing (about 0.7%)", "label_es": "Cobro recurrente · suma Stripe Billing (cerca de 0,7%)", "percent_fee": 13.6, "fixed_fee": 0.30, "currency": "USD"},
        ],
        "note_en": "Substack's own help page says its platform fee is 10% on paid subscriptions, and that Stripe charges 2.9% + $0.30 per card transaction plus a billing fee on recurring subscriptions. Substack's page names 0.5% for that billing fee, while recent independent sources report about 0.7%, so the second option uses 0.7%. The calculator combines platform and card fees into 12.9% + $0.30.",
        "note_es": "La propia página de ayuda de Substack indica que su comisión de plataforma es del 10% en suscripciones de pago, y que Stripe cobra 2,9% + $0,30 por transacción con tarjeta más una comisión de facturación en las suscripciones recurrentes. La página de Substack menciona 0,5% para esa comisión de facturación, mientras que fuentes independientes recientes indican cerca de 0,7%, por eso la segunda opción usa 0,7%. La calculadora combina la comisión de plataforma y la de tarjeta en 12,9% + $0,30.",
        "limits_en": ["The 10% platform fee applies to paid subscriptions only; free newsletters cost nothing.", "Stripe's international card and currency-conversion surcharges may also apply and are not modelled."],
        "limits_es": ["La comisión de plataforma del 10% se aplica solo a suscripciones de pago; los boletines gratuitos no cuestan nada.", "También pueden aplicarse los recargos de Stripe por tarjeta internacional y conversión de divisa, que no se modelan."],
        "faqs_en": [("How much of a $10 Substack subscription do I keep?",
                     "Substack takes 10% ($1.00) and Stripe takes 2.9% + $0.30 ($0.59), so you receive $8.41 on a $10 payment before any recurring-billing fee.")],
        "faqs_es": [("¿Cuánto me queda de una suscripción de $10 en Substack?",
                     "Substack se queda el 10% ($1,00) y Stripe 2,9% + $0,30 ($0,59), así que recibes $8,41 en un pago de $10 antes de cualquier comisión de cobro recurrente.")],
    },
    "kofi": {
        "level": "cross-checked",
        "source_url": "https://ko-fi.com",
        "fx_extra_percent": 0.0,
        "rate_options": [
            {"id": "shop",  "label_en": "Free plan · shop, membership and commission sales (5% + processing)", "label_es": "Plan gratuito · ventas de tienda, membresías y comisiones (5% + procesamiento)", "percent_fee": 7.9, "fixed_fee": 0.30, "currency": "USD"},
            {"id": "tips",  "label_en": "Tips and donations (0% platform fee + processing)", "label_es": "Propinas y donaciones (0% de plataforma + procesamiento)", "percent_fee": 2.9, "fixed_fee": 0.30, "currency": "USD"},
        ],
        "note_en": "Ko-fi charges 0% on one-time tips and donations, and 5% on shop sales, memberships and commissions on the free plan. Ko-fi Gold removes the platform fee. Stripe or PayPal processing of 2.9% + $0.30 applies on every plan, so a free-plan shop sale costs 7.9% + $0.30 in total. Independent sources disagree on the Gold price ($6 or $12 per month).",
        "note_es": "Ko-fi cobra 0% en propinas y donaciones únicas, y 5% en ventas de tienda, membresías y comisiones en el plan gratuito. Ko-fi Gold elimina la comisión de plataforma. El procesamiento de Stripe o PayPal de 2,9% + $0,30 se aplica en todos los planes, así que una venta de tienda en el plan gratuito cuesta 7,9% + $0,30 en total. Las fuentes independientes no coinciden en el precio de Gold ($6 o $12 al mes).",
        "limits_en": ["With Ko-fi Gold the platform fee is 0%, so use the tips option (2.9% + $0.30) to estimate it. The monthly Gold price is not included."],
        "limits_es": ["Con Ko-fi Gold la comisión de plataforma es 0%, así que usa la opción de propinas (2,9% + $0,30) para estimarla. No se incluye el precio mensual de Gold."],
        "faqs_en": [("Does Ko-fi really charge 0%?",
                     "Only on one-time tips and donations. Shop sales, memberships and commissions pay 5% on the free plan, and Stripe or PayPal processing of 2.9% + $0.30 applies to everything. A $10 shop sale leaves you $8.91 on the free plan.")],
        "faqs_es": [("¿Ko-fi cobra realmente 0%?",
                     "Solo en propinas y donaciones únicas. Las ventas de tienda, membresías y comisiones pagan 5% en el plan gratuito, y el procesamiento de Stripe o PayPal de 2,9% + $0,30 se aplica a todo. Una venta de tienda de $10 te deja $8,91 en el plan gratuito.")],
    },
    "amazon": {
        "level": "cross-checked",
        "source_url": "https://sell.amazon.com/pricing",
        "fx_extra_percent": 0.0,
        "note_en": "Amazon's referral fee is a percentage of the total sale price (item plus shipping and gift wrap) that depends on the category. Most categories pay 15%, with a minimum of $0.30 per item. The calculator uses 15% and no fixed fee.",
        "note_es": "La comisión por referencia de Amazon es un porcentaje del precio total de la venta (artículo más envío y envoltorio de regalo) que depende de la categoría. La mayoría de las categorías pagan 15%, con un mínimo de $0,30 por artículo. La calculadora usa 15% y ningún cargo fijo.",
        "limits_en": ["Rates range from about 5% to 45% by category, and some categories (for example clothing and grocery) change with the item price. Media items add a $1.80 closing fee.", "FBA fulfillment, storage, advertising and the monthly Professional plan fee are not included."],
        "limits_es": ["Las tarifas van de cerca de 5% a 45% según la categoría, y algunas categorías (por ejemplo ropa y alimentos) cambian con el precio del artículo. Los artículos de medios añaden una tarifa de cierre de $1,80.", "No se incluyen la logística de FBA, el almacenamiento, la publicidad ni la cuota mensual del plan Profesional."],
        "faqs_en": [("Why is my Amazon referral fee different from 15%?",
                     "The percentage depends on the category (about 5% to 45%) and some categories change with the item price. There is also a $0.30 minimum per item, so a $1.50 item pays $0.30 (20%) instead of $0.225. Check your category in Seller Central and use the custom rate for an exact result.")],
        "faqs_es": [("¿Por qué mi comisión por referencia de Amazon es distinta del 15%?",
                     "El porcentaje depende de la categoría (de cerca de 5% a 45%) y algunas categorías cambian con el precio del artículo. Además hay un mínimo de $0,30 por artículo, así que uno de $1,50 paga $0,30 (20%) en lugar de $0,225. Revisa tu categoría en Seller Central y usa la tarifa personalizada para un resultado exacto.")],
    },
    # ───────── Cuarta tanda: Payoneer y TikTok Shop (las fuentes no coinciden: se quedan como estimación, con la explicación) ─────────
    "payoneer": {
        "level": "estimate",
        "source_url": "https://www.payoneer.com/about/pricing/",
        "fx_extra_percent": 0.0,
        "rate_options": [
            {"id": "convert", "label_en": "Marketplace payout + withdrawal in another currency (about 1% + 2%)", "label_es": "Pago de marketplace + retiro en otra moneda (cerca de 1% + 2%)", "percent_fee": 3.0, "fixed_fee": 0.0, "currency": "USD"},
            {"id": "local",   "label_en": "Marketplace payout + same-currency local bank withdrawal (about 1% + $1.50)", "label_es": "Pago de marketplace + retiro bancario local en la misma moneda (cerca de 1% + $1,50)", "percent_fee": 1.0, "fixed_fee": 1.50, "currency": "USD"},
        ],
        "note_en": "Payoneer has no single percentage-plus-fixed rate: the cost depends on how money arrives and how it leaves. Payoneer's pricing pages and independent sources agree on roughly 1% for some incoming payments, a flat $1.50 for a local bank withdrawal in the same currency, and up to about 3% for withdrawals that need currency conversion. The 3% default models a payout that needs conversion; the second option models a same-currency withdrawal. Treat both as estimates.",
        "note_es": "Payoneer no tiene una tarifa única de porcentaje más cargo fijo: el costo depende de cómo llega y cómo sale el dinero. Las páginas de precios de Payoneer y las fuentes independientes coinciden en cerca de 1% en algunos cobros entrantes, $1,50 fijos por un retiro bancario local en la misma moneda y hasta cerca de 3% en retiros que requieren conversión de divisa. El 3% por defecto modela un pago que requiere conversión; la segunda opción modela un retiro en la misma moneda. Considera ambas como estimaciones.",
        "limits_en": ["Some regions add an annual account fee of about $29.95, and sources disagree on the volume that waives it. It is not included.", "Fees differ by country, currency and payment source, so use the custom-rate option with the numbers Payoneer shows for your own transfer."],
        "limits_es": ["Algunas regiones añaden una cuota anual de cerca de $29,95 y las fuentes no coinciden en el volumen que la exime. No está incluida.", "Las comisiones cambian según el país, la moneda y el origen del pago, así que usa la tarifa personalizada con las cifras que Payoneer muestra para tu transferencia."],
        "faqs_en": [("Why is Payoneer not a single percentage?",
                     "Because each step is priced separately: receiving a payment, converting currency and withdrawing to a bank. A same-currency local withdrawal can cost a flat $1.50, while a conversion can cost up to about 3%. Pick the option that matches your transfer or enter your own rate.")],
        "faqs_es": [("¿Por qué Payoneer no tiene un porcentaje único?",
                     "Porque cada paso tiene su propio precio: recibir un pago, convertir divisa y retirar a un banco. Un retiro local en la misma moneda puede costar $1,50 fijos, mientras que una conversión puede costar hasta cerca de 3%. Elige la opción que coincide con tu transferencia o introduce tu propia tarifa.")],
    },
    "tiktokshop": {
        "level": "estimate",
        "source_url": "https://seller.tiktok.com",
        "fx_extra_percent": 0.0,
        "rate_options": [
            {"id": "std",       "label_en": "Referral fee 6% (rate listed in TikTok's fee pages)", "label_es": "Comisión por referencia 6% (tarifa de las páginas de TikTok)", "percent_fee": 6.0, "fixed_fee": 0.0, "currency": "USD"},
            {"id": "reported8", "label_en": "Referral fee 8% (reported since August 2026)",        "label_es": "Comisión por referencia 8% (según informes desde agosto de 2026)", "percent_fee": 8.0, "fixed_fee": 0.0, "currency": "USD"},
            {"id": "proc",      "label_en": "6% + processing charged separately (3.5% + $0.30 in some sources)", "label_es": "6% + procesamiento cobrado aparte (3,5% + $0,30 en algunas fuentes)", "percent_fee": 9.5, "fixed_fee": 0.30, "currency": "USD"},
        ],
        "note_en": "TikTok Shop charges a referral fee on each completed order: 6% for most US categories according to its fee pages (some categories pay 5%). Independent trade reports say it rose to 8% for most non-food categories in August 2026, although the published table still lists 6%. Sources also disagree on whether payment processing is included in the referral fee or charged separately, so the three options cover each case. Check your settlement statements in Seller Center.",
        "note_es": "TikTok Shop cobra una comisión por referencia en cada pedido completado: 6% en la mayoría de las categorías de EE. UU. según sus páginas de tarifas (algunas categorías pagan 5%). Informes independientes del sector indican que subió a 8% en la mayoría de las categorías no alimentarias en agosto de 2026, aunque la tabla publicada sigue mostrando 6%. Las fuentes tampoco coinciden en si el procesamiento de pagos está incluido en la comisión por referencia o se cobra aparte, por eso las tres opciones cubren cada caso. Revisa tus extractos de liquidación en Seller Center.",
        "limits_en": ["Refunds cost an administration fee of 20% of the original referral fee, capped at $5 per SKU, and fulfillment, advertising and creator affiliate commissions (often 10%–20%) are not included.", "New US sellers may get a reduced referral rate for their first 30 days."],
        "limits_es": ["Los reembolsos tienen una tarifa administrativa del 20% de la comisión por referencia original, con tope de $5 por SKU, y no se incluyen la logística, la publicidad ni las comisiones de afiliados creadores (a menudo 10%–20%).", "Los vendedores nuevos de EE. UU. pueden tener una tarifa de referencia reducida durante sus primeros 30 días."],
        "faqs_en": [("Is TikTok Shop's referral fee 6% or 8%?",
                     "TikTok's published fee pages list 6% for most US categories, while trade reports from August 2026 say the rate for most non-food categories rose to 8%. Look at the rate on your own settlement statements and pick the matching option, or enter it as a custom rate.")],
        "faqs_es": [("¿La comisión por referencia de TikTok Shop es 6% o 8%?",
                     "Las páginas de tarifas publicadas por TikTok indican 6% para la mayoría de las categorías de EE. UU., mientras que informes del sector de agosto de 2026 dicen que la tarifa de la mayoría de las categorías no alimentarias subió a 8%. Mira la tarifa de tus propios extractos de liquidación y elige la opción correspondiente, o introdúcela como tarifa personalizada.")],
    },
    # ───────── Quinta tanda: Mercury (verificada en mercury.com) y Deel (modelo distinto: cuota mensual) ─────────
    "mercury": {
        "level": "verified",
        "source_url": "https://mercury.com/start",
        "fx_extra_percent": 1.0,
        "note_en": "Mercury's own pricing pages list free ACH transfers, free domestic wires and free USD international wires, and no monthly fee on its free accounts. International wires in a currency other than USD carry a 1% currency exchange fee (tick \"Currency conversion required\"). Optional paid plans start at $35 per month for advanced payment workflows.",
        "note_es": "Las propias páginas de precios de Mercury indican transferencias ACH gratuitas, giros (wires) nacionales gratuitos y giros internacionales en USD gratuitos, y sin cuota mensual en sus cuentas gratuitas. Los giros internacionales en una moneda distinta del USD llevan una comisión de cambio de divisa del 1% (marca \"Requiere conversión de divisa\"). Los planes de pago opcionales empiezan en $35 al mes para flujos de pago avanzados.",
        "limits_en": ["Mercury is a business bank account, not a card processor: the 0% applies to ACH transfers and wires, not to card payments.", "Mercury accounts are for companies formed and registered in the United States or a US territory."],
        "limits_es": ["Mercury es una cuenta bancaria de negocio, no un procesador de tarjetas: el 0% se aplica a transferencias ACH y giros, no a pagos con tarjeta.", "Las cuentas de Mercury son para empresas constituidas y registradas en Estados Unidos o en un territorio de EE. UU."],
        "faqs_en": [("Does Mercury charge to receive an ACH or wire payment?",
                     "No. ACH transfers, domestic wires and USD international wires are free to send and receive. Only international wires in a currency other than USD carry a 1% currency exchange fee, and the sending bank may charge its own fees.")],
        "faqs_es": [("¿Mercury cobra por recibir un pago ACH o un giro?",
                     "No. Las transferencias ACH, los giros nacionales y los giros internacionales en USD son gratuitos al enviar y recibir. Solo los giros internacionales en una moneda distinta del USD llevan una comisión de cambio del 1%, y el banco que envía puede cobrar sus propias comisiones.")],
    },
    "deel": {
        "level": "estimate",
        "source_url": "https://www.deel.com/pricing/",
        "fx_extra_percent": 0.0,
        "rate_options": [
            {"id": "contractor", "label_en": "Contractor side · illustrative withdrawal and FX cost (about 1%)", "label_es": "Lado del contratista · costo ilustrativo de retiro y cambio (cerca de 1%)", "percent_fee": 1.0, "fixed_fee": 0.0, "currency": "USD"},
            {"id": "employer",   "label_en": "Employer side · $49 per contractor per month, on one monthly payment", "label_es": "Lado del empleador · $49 por contratista al mes, sobre un pago mensual", "percent_fee": 0.0, "fixed_fee": 49.0, "currency": "USD"},
        ],
        "note_en": "Deel does not charge a percentage per payment. Its published Contractor Management price, repeated by several 2026 sources that read deel.com/pricing, is $49 per contractor per month paid by the employer. Contractors pay their own withdrawal fees and an FX spread that Deel markets as 0.6%–2%, which vary by method and country. The 1% default is only an illustrative contractor-side figure, so treat the result as an estimate.",
        "note_es": "Deel no cobra un porcentaje por pago. Su precio publicado de Contractor Management, que repiten varias fuentes de 2026 que leyeron deel.com/pricing, es de $49 por contratista al mes y lo paga el empleador. Los contratistas pagan sus propias comisiones de retiro y un margen de cambio que Deel anuncia como 0,6%–2%, y que varían según el método y el país. El 1% por defecto es solo una cifra ilustrativa del lado del contratista, así que considera el resultado como una estimación.",
        "limits_en": ["Contractor of Record ($325 per contractor per month) and Employer of Record (from $599 per employee per month) are different products and are not modelled.", "Withdrawal fees depend on the method, for example a SWIFT withdrawal can cost around $15 according to an independent source."],
        "limits_es": ["Contractor of Record ($325 por contratista al mes) y Employer of Record (desde $599 por empleado al mes) son productos distintos y no se modelan.", "Las comisiones de retiro dependen del método; por ejemplo, un retiro SWIFT puede costar cerca de $15 según una fuente independiente."],
        "faqs_en": [("Does Deel take a percentage of my payments?",
                     "Not as a published fee. Employers pay $49 per contractor per month for Contractor Management, and contractors pay withdrawal fees and an FX spread that depend on the method and country. Use the employer option to see the monthly fee on one payment, or enter your own rate.")],
        "faqs_es": [("¿Deel se queda con un porcentaje de mis pagos?",
                     "No como comisión publicada. Los empleadores pagan $49 por contratista al mes por Contractor Management, y los contratistas pagan comisiones de retiro y un margen de cambio que dependen del método y del país. Usa la opción del empleador para ver la cuota mensual sobre un pago, o introduce tu propia tarifa.")],
    },
    # ───────── Sexta tanda: Coinbase (Commerce cerró en marzo de 2026) y Revolut Business ─────────
    "coinbase": {
        "level": "verified",
        "source_url": "https://help.coinbase.com/transitioning-from-coinbase-commerce-to-coinbase-business",
        "fx_extra_percent": 1.0,
        "note_en": "Coinbase Commerce closed on March 31, 2026 and its merchants moved to Coinbase Business, which is available only to US and Singapore businesses. Coinbase's help page lists a 1% transaction fee for merchants migrating from Commerce. Pricing for other new businesses is not published (enterprise rates come through sales). Converting crypto to cash adds roughly 0.5%–1.5% according to independent sources, so the calculator uses 1% for the currency-conversion box.",
        "note_es": "Coinbase Commerce cerró el 31 de marzo de 2026 y sus comercios pasaron a Coinbase Business, disponible solo para empresas de EE. UU. y Singapur. La página de ayuda de Coinbase indica una comisión del 1% por transacción para los comercios que migran desde Commerce. El precio para otras empresas nuevas no está publicado (las tarifas de empresa se acuerdan con ventas). Convertir cripto a efectivo suma aproximadamente 0,5%–1,5% según fuentes independientes, así que la calculadora usa 1% en la casilla de conversión de divisa.",
        "limits_en": ["The 1% rate is confirmed for merchants migrating from Coinbase Commerce; other businesses may be quoted different pricing.", "Network (gas) fees are usually paid by the customer and are not modelled. Crypto payments are final, so there are no chargebacks."],
        "limits_es": ["La tarifa del 1% está confirmada para los comercios que migran desde Coinbase Commerce; otras empresas pueden recibir un precio distinto.", "Las comisiones de red (gas) las suele pagar el cliente y no se modelan. Los pagos en cripto son definitivos, así que no hay contracargos."],
        "faqs_en": [("Is Coinbase Commerce still available?",
                     "No. Coinbase Commerce closed on March 31, 2026. Its merchants moved to Coinbase Business, which is open to US and Singapore businesses only. This page uses the 1% fee Coinbase lists for migrating merchants.")],
        "faqs_es": [("¿Coinbase Commerce sigue disponible?",
                     "No. Coinbase Commerce cerró el 31 de marzo de 2026. Sus comercios pasaron a Coinbase Business, abierto solo a empresas de EE. UU. y Singapur. Esta página usa la comisión del 1% que Coinbase indica para los comercios que migran.")],
    },
    "revolut": {
        "level": "estimate",
        "source_url": "https://www.revolut.com/legal/business-grow-fees/",
        "fx_extra_percent": 0.6,
        "note_en": "Revolut Business prices most things by plan and by type of payment. Its fee documents say incoming transfers in USD, GBP, EUR and CHF are always free, local transfers beyond the plan allowance cost 0.20 and international transfers beyond it cost 5 (in the account's currency), and payment processing is listed at 1% of the transaction plus a flat 0.20 in pounds or euros. The calculator's 1% + $0.20 follows that payment-processing line, but the excerpt I could read did not state exactly which product it covers, so it stays an estimate. Currency exchange is free at the interbank rate within the plan allowance and costs about 0.6% beyond it (UK, independent source).",
        "note_es": "Revolut Business fija la mayoría de precios según el plan y el tipo de pago. Sus documentos de comisiones indican que las transferencias entrantes en USD, GBP, EUR y CHF son siempre gratuitas, que las transferencias locales por encima de la cuota del plan cuestan 0,20 y las internacionales 5 (en la moneda de la cuenta), y que el procesamiento de pagos figura como 1% de la transacción más 0,20 fijos en libras o euros. El 1% + $0,20 de la calculadora sigue esa línea de procesamiento de pagos, pero el extracto que pude leer no precisaba qué producto cubre exactamente, por eso sigue siendo una estimación. El cambio de divisa es gratis al tipo interbancario dentro de la cuota del plan y cuesta cerca de 0,6% por encima (Reino Unido, fuente independiente).",
        "limits_en": ["Monthly plan fees (for example about £10, £35 and £125 in the UK) and ACH transfers to the US (0.2%, minimum 0.50) are not included.", "Weekend currency exchange costs about 1% according to an independent source."],
        "limits_es": ["No se incluyen las cuotas mensuales del plan (por ejemplo cerca de £10, £35 y £125 en el Reino Unido) ni las transferencias ACH a EE. UU. (0,2%, mínimo 0,50).", "El cambio de divisa en fin de semana cuesta cerca de 1% según una fuente independiente."],
        "faqs_en": [("Does Revolut Business charge to receive money?",
                     "Incoming transfers in USD, GBP, EUR and CHF are always free according to Revolut's fee documents. Costs appear when you send money beyond your plan's free transfers, exchange currency beyond the free allowance, or take card payments through its payment-processing products.")],
        "faqs_es": [("¿Revolut Business cobra por recibir dinero?",
                     "Según los documentos de comisiones de Revolut, las transferencias entrantes en USD, GBP, EUR y CHF son siempre gratuitas. Los costos aparecen al enviar dinero por encima de las transferencias gratuitas de tu plan, al cambiar divisa por encima de la cuota gratuita o al cobrar con tarjeta mediante sus productos de procesamiento de pagos.")],
    },
    # ───────── Séptima tanda: Skrill (precios de skrill.com; la cifra de 2,99% es la del que ENVÍA, no la del que recibe) ─────────
    "skrill": {
        "level": "verified",
        "source_url": "https://www.skrill.com/en/skrill-money-transfer/",
        "fx_extra_percent": 3.99,
        "rate_options": [
            {"id": "send",    "label_en": "Skrill to Skrill transfer · standard account (paid by the sender)", "label_es": "Transferencia Skrill a Skrill · cuenta estándar (la paga quien envía)", "percent_fee": 2.99, "fixed_fee": 0.0, "currency": "EUR"},
            {"id": "true",    "label_en": "Skrill to Skrill transfer · True Skriller account (paid by the sender)", "label_es": "Transferencia Skrill a Skrill · cuenta True Skriller (la paga quien envía)", "percent_fee": 1.45, "fixed_fee": 0.0, "currency": "EUR"},
            {"id": "receive", "label_en": "Receiving money into your Skrill account (no currency conversion)", "label_es": "Recibir dinero en tu cuenta Skrill (sin conversión de divisa)", "percent_fee": 0.0, "fixed_fee": 0.0, "currency": "EUR"},
        ],
        "note_en": "Skrill's own fee pages show that sending money from one Skrill account to another costs 2.99% for a standard account and 1.45% for a True Skriller account (minimum 0.50), and that receiving money is free when no currency conversion is involved. The 2.99% is therefore charged to the sender, not to the person receiving. Currency conversion adds 3.99% according to independent sources. Fees for taking payments as a business, and for withdrawing to a bank or card, are separate and depend on the method and country.",
        "note_es": "Las páginas de comisiones de Skrill muestran que enviar dinero de una cuenta Skrill a otra cuesta 2,99% en una cuenta estándar y 1,45% en una cuenta True Skriller (mínimo 0,50), y que recibir dinero es gratis cuando no hay conversión de divisa. Por eso el 2,99% lo paga quien envía, no quien recibe. La conversión de divisa suma 3,99% según fuentes independientes. Las comisiones por cobrar como negocio y por retirar a un banco o tarjeta son aparte y dependen del método y del país.",
        "limits_en": ["The 0.50 minimum fee on Skrill-to-Skrill transfers is not modelled, so very small transfers cost more than the percentage suggests.", "Merchant processing, withdrawals (for example a bank transfer or a Swift withdrawal) and card deposits have their own fees by country and method and are not included."],
        "limits_es": ["La comisión mínima de 0,50 en transferencias Skrill a Skrill no se modela, así que las transferencias muy pequeñas cuestan más de lo que sugiere el porcentaje.", "El procesamiento para negocios, los retiros (por ejemplo a un banco o por Swift) y los depósitos con tarjeta tienen comisiones propias según el país y el método, y no se incluyen."],
        "faqs_en": [("Who pays Skrill's 2.99%, the sender or the receiver?",
                     "The sender. Skrill's fee pages list 2.99% (or 1.45% for True Skriller accounts) for sending to another Skrill account, while receiving money is free as long as no currency conversion is involved. If a conversion is needed, about 3.99% is added.")],
        "faqs_es": [("¿Quién paga el 2,99% de Skrill, quien envía o quien recibe?",
                     "Quien envía. Las páginas de comisiones de Skrill indican 2,99% (o 1,45% en cuentas True Skriller) por enviar a otra cuenta Skrill, mientras que recibir dinero es gratis siempre que no haya conversión de divisa. Si hace falta convertir, se suma cerca de 3,99%.")],
    },
}

# ── Estimaciones con matices conocidos (tarifa base sin cambios, pero con explicación honesta) ──
_ESTIMATE_DETAILS = {
    "wise": {
        "note_en": "Wise does not publish a single percentage-plus-fixed rate for receiving money. Receiving USD by ACH is free, a USD wire costs a fixed $6.11, and currency conversion is a variable percentage that depends on the currency pair (typically under 1%). 0.65% + $0.45 is an illustrative blended estimate, not an official Wise price.",
        "note_es": "Wise no publica una tarifa única de porcentaje más cargo fijo para recibir dinero. Recibir USD por ACH es gratis, un giro (wire) en USD cuesta $6,11 fijos y la conversión de divisa es un porcentaje variable según el par de monedas (normalmente menos de 1%). 0,65% + $0,45 es una estimación combinada ilustrativa, no un precio oficial de Wise.",
        "source_url": "https://wise.com/us/pricing/business/receive",
        "rate_options": [
            {"id": "blend", "label_en": "Illustrative blended estimate (not an official Wise price)", "label_es": "Estimación combinada ilustrativa (no es un precio oficial de Wise)", "percent_fee": 0.65, "fixed_fee": 0.45, "currency": "USD"},
            {"id": "ach",   "label_en": "Receiving USD by ACH (published as free)", "label_es": "Recibir USD por ACH (publicado como gratis)", "percent_fee": 0.0, "fixed_fee": 0.0, "currency": "USD"},
            {"id": "wire",  "label_en": "Receiving a USD wire (published fixed fee of $6.11)", "label_es": "Recibir un giro (wire) en USD (cargo fijo publicado de $6,11)", "percent_fee": 0.0, "fixed_fee": 6.11, "currency": "USD"},
        ],
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

for _k, _v in _ESTIMATE_DETAILS.items():
    _v.setdefault('level', 'estimate')
    DETAILS.setdefault(_k, _v)

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
        c = DETAILS.get(key, {})
        confidence = c.get("level", "estimate")
        checked = REVIEW_DATE[:7] if confidence != "estimate" else None
        source_url = c.get("source_url", url)
        fx = c.get("fx_extra_percent", 0.0)
        options = c.get("rate_options", [])
        note_en = c.get("note_en", GENERIC_NOTE_EN.format(month=REVIEW_MONTH))
        note_es = c.get("note_es", GENERIC_NOTE_ES.format(month=REVIEW_MONTH))
        limits_en, limits_es = c.get("limits_en", []), c.get("limits_es", [])
        extra_en, extra_es = c.get("faqs_en", []), c.get("faqs_es", [])
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