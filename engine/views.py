import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from itertools import combinations
from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse

DATA_PATH = Path(__file__).resolve().parent / 'data' / 'platforms.json'
TIER_AMOUNTS = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

# Indexación: False = solo se indexan las 25 páginas principales (x2 idiomas = 50 URLs).
# Las páginas "A vs B" siguen funcionando para los visitantes, pero llevan noindex y salen del sitemap.
# Para volver a indexarlas todas, cambia esto a True.
INDEX_COMPARISONS = False

def load_data():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)['platforms']

ES_MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

def load_meta():
    """Fecha de revisión, recuentos y nº de URLs en el sitemap (viene de seed_platforms.py)."""
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        meta = json.load(f).get('meta', {})
    total = meta.get('total_count', 0)
    meta['checked_count'] = meta.get('verified_count', 0) + meta.get('crosschecked_count', 0)
    pairs = total * (total - 1) // 2
    meta['indexed_urls'] = 2 * total + (2 * pairs if INDEX_COMPARISONS else 0)
    try:
        year, month, _ = meta.get('last_reviewed', '').split('-')
        meta['review_month_es'] = f"{ES_MONTHS[int(month) - 1]} {year}"
    except (ValueError, IndexError):
        meta['review_month_es'] = meta.get('review_month', '')
    return meta

def r2(x):
    """Redondeo a centavos 'half up': igual que Math.round del JavaScript de la calculadora."""
    return Decimal(str(x)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calc_amounts(amount, pct, fixed):
    """Misma fórmula que calcPlatform() en calculator.html: comisión, neto y monto a facturar."""
    p = Decimal(str(pct)) / 100
    amt, fx = Decimal(str(amount)), Decimal(str(fixed))
    fee = r2(amt * p + fx)
    net = r2(max(Decimal(0), amt - fee))
    reverse = r2((amt + fx) / (1 - p)) if p < 1 else amt
    return fee, net, reverse

def compute_row(amount, p):
    fee, net, reverse = calc_amounts(amount, p['percent_fee'], p['fixed_fee'])
    return {'amount': amount, 'fee': f"{fee:.2f}", 'net': f"{net:.2f}", 'reverse': f"{reverse:.2f}"}

CURRENCY_SYMBOLS = {'USD': '$', 'GBP': '£', 'EUR': '€'}

def build_info(p, lang, amount=1000):
    """Datos para las secciones informativas: ejemplo resuelto, planes/regiones y limitaciones."""
    base, intl, fx = Decimal(str(p['percent_fee'])), Decimal(str(p['intl_extra_percent'])), Decimal(str(p.get('fx_extra_percent', 0)))
    fixed = p['fixed_fee']
    scenarios = [('standard', base)]
    if intl:
        scenarios.append(('intl', base + intl))
    if fx:
        scenarios.append(('intl_fx', base + intl + fx))
    rows = []
    for kind, pct in scenarios:
        fee, net, reverse = calc_amounts(amount, pct, fixed)
        rows.append({'kind': kind, 'pct': f"{pct.normalize():f}", 'fee': f"{fee:.2f}", 'net': f"{net:.2f}", 'reverse': f"{reverse:,.2f}"})
    options = []
    for o in p.get('rate_options', []):
        fee, net, _ = calc_amounts(amount, o['percent_fee'], o['fixed_fee'])
        options.append({
            'label': o['label_' + lang], 'pct': o['percent_fee'], 'fixed': f"{o['fixed_fee']:.2f}",
            'symbol': CURRENCY_SYMBOLS.get(o['currency'], '$'), 'currency': o['currency'],
            'fee': f"{fee:.2f}", 'net': f"{net:.2f}",
        })
    return {
        'name': p['name'], 'category': p['category'], 'pct': p['percent_fee'], 'fixed': f"{fixed:.2f}",
        'intl': p['intl_extra_percent'], 'fx': p.get('fx_extra_percent', 0),
        'confidence': p['confidence'], 'checked': p.get('checked'), 'source_url': p['source_url'],
        'note': p['rate_note'][lang], 'limits': p.get('limits', {}).get(lang, []),
        'how': p.get('category_how', {}).get(lang, ''),
        'amount': amount, 'amount_fmt': f"{amount:,}", 'rows': rows, 'options': options,
    }

def calculator_view(request, lang='en', slug='stripe'):
    platforms = load_data()
    if lang not in ['en', 'es']:
        lang = 'en'

    is_comparison = '-vs-' in slug
    if is_comparison:
        parts = slug.split('-vs-')
        p1_key, p2_key = parts[0], parts[1]
        if p1_key not in platforms or p2_key not in platforms:
            raise Http404("Comparison not found")
        primary = platforms[p1_key]
        secondary = platforms[p2_key]

        if lang == 'en':
            title = f"{primary['name']} vs {secondary['name']} Fees (2026) - Side-by-Side Calculator"
            h1 = f"{primary['name']} vs {secondary['name']} Fee Calculator"
            desc = f"Compare {primary['name']} ({primary['percent_fee']}% + ${primary['fixed_fee']}) vs {secondary['name']} ({secondary['percent_fee']}% + ${secondary['fixed_fee']}) processing fees side by side."
            guide = f"{primary['seo']['en']['guide']} Meanwhile, {secondary['seo']['en']['guide']}"
        else:
            title = f"{primary['name']} vs {secondary['name']} (2026) - Comparador de Comisiones"
            h1 = f"Comparativa: {primary['name']} vs {secondary['name']}"
            desc = f"Compara las comisiones de {primary['name']} ({primary['percent_fee']}%) contra {secondary['name']} ({secondary['percent_fee']}%) en tiempo real."
            guide = f"{primary['seo']['es']['guide']} Por su parte, {secondary['seo']['es']['guide']}"
        faqs = primary['seo'][lang]['faqs'] + [secondary['seo'][lang]['faqs'][0]]
    else:
        if slug not in platforms:
            raise Http404("Calculator not found")
        p1_key = slug
        primary = platforms[p1_key]
        p2_key = 'wise' if slug != 'wise' else 'stripe'
        secondary = platforms[p2_key]
        title = primary['seo'][lang]['title']
        h1 = primary['seo'][lang]['h1']
        desc = primary['seo'][lang]['desc']
        guide = primary['seo'][lang]['guide']
        faqs = primary['seo'][lang]['faqs']

    # Tabla pre-calculada para SEO y valor de usuario
    fee_table = [compute_row(amt, primary) for amt in TIER_AMOUNTS]

    # Enlaces de comparativas relevantes para esta plataforma (Interlinking inteligente)
    related_comparisons = []
    for other_key, other_p in platforms.items():
        if other_key != p1_key:
            related_comparisons.append({
                'slug': f"{p1_key}-vs-{other_key}",
                'label': f"{primary['name']} vs {other_p['name']}"
            })

    context = {
        'lang': lang,
        'slug': slug,
        'is_comparison': is_comparison,
        'title': title,
        'h1': h1,
        'desc': desc,
        'guide': guide,
        'faqs': faqs,
        'fee_table': fee_table,
        'p1_key': p1_key,
        'p2_key': p2_key,
        'primary': primary,
        'secondary': secondary,
        'platforms_json': json.dumps(platforms),
        'all_platforms': platforms,
        'related_comparisons': related_comparisons[:16],
        'meta': load_meta(),
        'noindex': is_comparison and not INDEX_COMPARISONS,
        'info_platforms': [build_info(primary, lang)] + ([build_info(secondary, lang)] if is_comparison else []),
    }
    return render(request, 'calculator.html', context)

LEGAL_PAGES = {
    'privacy': {
        'en': ('Privacy Policy - FeePilot',
               'Fee calculations run locally in your browser: the amounts you type are not sent to our servers. '
               'We do use Google Analytics 4 and Microsoft Clarity to understand how the site is used (the amount field is masked in Clarity session recordings), '
               'and advertising partners such as Google AdSense may use cookies to serve ads based on prior visits to this or other websites. '
               'You can opt out of personalized advertising in Google Ads Settings.'),
        'es': ('Política de privacidad - FeePilot',
               'Los cálculos de comisiones se ejecutan en tu navegador: los montos que escribes no se envían a nuestros servidores. '
               'Usamos Google Analytics 4 y Microsoft Clarity para entender cómo se usa el sitio (el campo del monto está enmascarado en las grabaciones de Clarity), '
               'y socios publicitarios como Google AdSense pueden usar cookies para mostrar anuncios según visitas anteriores a este u otros sitios. '
               'Puedes desactivar la publicidad personalizada en la Configuración de anuncios de Google.'),
    },
    'terms': {
        'en': ('Terms of Service & Disclaimer - FeePilot',
               'FeePilot provides payment-processing fee estimates for informational and educational purposes only. '
               'Rates change often and depend on your country, plan, card type and currency, so always confirm the final fee in your own merchant dashboard.'),
        'es': ('Términos del servicio y descargo de responsabilidad - FeePilot',
               'FeePilot ofrece estimaciones de comisiones de procesamiento de pagos solo con fines informativos y educativos. '
               'Las tarifas cambian con frecuencia y dependen de tu país, plan, tipo de tarjeta y moneda; confirma siempre la comisión final en el panel de tu plataforma.'),
    },
    'about': {
        'en': ('About FeePilot Global',
               'FeePilot is an independent fee-comparison utility for freelancers, e-commerce merchants and SaaS founders. '
               'Each rate is labelled as checked against an official source (with the month) or as an estimate, so you can see how much to trust it.'),
        'es': ('Acerca de FeePilot Global',
               'FeePilot es una herramienta independiente para comparar comisiones, pensada para freelancers, comercios electrónicos y fundadores de SaaS. '
               'Cada tarifa indica si fue contrastada con una fuente oficial (con el mes) o si es una estimación, para que sepas cuánto fiarte.'),
    },
}

def legal_view(request, page='privacy', lang=None):
    """Páginas legales renderizadas en el servidor en inglés (/legal/x/) y español (/es/legal/x/)."""
    if page not in LEGAL_PAGES:
        raise Http404()
    if lang is None:
        # Enlaces antiguos: /legal/privacy/?lang=es  ->  /es/legal/privacy/
        if request.GET.get('lang') == 'es':
            return redirect(f'/es/legal/{page}/', permanent=True)
        lang = 'en'
    if lang == 'en' and request.path.startswith('/en/'):
        return redirect(f'/legal/{page}/', permanent=True)
    if lang not in ('en', 'es'):
        raise Http404()

    title, body = LEGAL_PAGES[page][lang]
    en_path, es_path = f'/legal/{page}/', f'/es/legal/{page}/'
    return render(request, 'legal.html', {
        'lang': lang,
        'page': page,
        'title': title,
        'content': body,
        'body': body,
        'meta': load_meta(),
        'prefix': '/es' if lang == 'es' else '',
        'site_url': request.build_absolute_uri('/')[:-1],
        'en_path': en_path,
        'es_path': es_path,
        'self_path': es_path if lang == 'es' else en_path,
    })

def ads_txt(request):
    """Archivo ads.txt de Google AdSense (tu ID de editor)"""
    linea_ads = "google.com, pub-8913212577365986, DIRECT, f08c47fec0942fa0"
    return HttpResponse(linea_ads, content_type="text/plain")

def sitemap_xml(request):
    platforms = load_data()
    host = request.build_absolute_uri('/')[:-1]
    lastmod = load_meta().get('last_reviewed')
    urls = []

    for lang in ['en', 'es']:
        for key in platforms.keys():
            urls.append(f"{host}/{lang}/{key}-fee-calculator/")
        if INDEX_COMPARISONS:
            for k1, k2 in combinations(platforms.keys(), 2):
                urls.append(f"{host}/{lang}/{k1}-vs-{k2}-fees/")

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        mod = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
        xml.append(f"  <url><loc>{u}</loc>{mod}<changefreq>weekly</changefreq><priority>0.8</priority></url>")
    xml.append('</urlset>')
    return HttpResponse("\n".join(xml), content_type="application/xml")
def robots_txt(request):
    host = request.build_absolute_uri('/')[:-1]
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {host}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")