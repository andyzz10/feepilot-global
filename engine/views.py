import json
from pathlib import Path
from itertools import combinations
from django.shortcuts import render
from django.http import Http404, HttpResponse

DATA_PATH = Path(__file__).resolve().parent / 'data' / 'platforms.json'
TIER_AMOUNTS = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

def load_data():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)['platforms']

def compute_row(amount, p):
    pct = p['percent_fee'] / 100.0
    fee = round((amount * pct) + p['fixed_fee'], 2)
    net = round(max(0, amount - fee), 2)
    reverse = round((amount + p['fixed_fee']) / (1.0 - pct), 2) if pct < 1 else amount
    return {'amount': amount, 'fee': f"{fee:.2f}", 'net': f"{net:.2f}", 'reverse': f"{reverse:.2f}"}

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
    }
    return render(request, 'calculator.html', context)

def legal_view(request, page='privacy'):
    pages = {
        'privacy': (
            'Privacy Policy - FeePilot',
            'We respect your privacy. All fee calculations on FeePilot happen locally in your browser. We do not store financial transactions or personal banking data. Third-party vendors, including Google AdSense, use cookies to serve ads based on prior visits to this or other websites. Users may opt out of personalized advertising by visiting Google Ads Settings.'
        ),
        'terms': (
            'Terms of Service & Disclaimer - FeePilot',
            'FeePilot provides financial and payment processing fee estimates for informational and educational purposes only. While we update our platform database regularly, actual fees may vary depending on your country, merchant tier, or currency conversion rates.'
        ),
        'about': (
            'About FeePilot Global',
            'FeePilot is an independent financial technology utility built for freelancers, e-commerce merchants, and SaaS founders worldwide to transparently compare payment processing costs and maximize net revenue.'
        )
    }
    if page not in pages:
        raise Http404()
    title, body = pages[page]
    return render(request, 'legal.html', {'title': title, 'body': body})

def ads_txt(request):
    """Archivo obligatorio para verificar tu cuenta de Google AdSense"""
    content = "google.com, pub-0000000000000000, DIRECT, f08c47fec0942fa0"
    return HttpResponse(content, content_type="text/plain")

def sitemap_xml(request):
    platforms = load_data()
    host = request.build_absolute_uri('/')[:-1]
    urls = []

    for lang in ['en', 'es']:
        for key in platforms.keys():
            urls.append(f"{host}/{lang}/{key}-fee-calculator/")
        for k1, k2 in combinations(platforms.keys(), 2):
            urls.append(f"{host}/{lang}/{k1}-vs-{k2}-fees/")

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml.append(f"  <url><loc>{u}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>")
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

def ads_txt(request):
    linea_ads = "google.com, pub-8913212577365986, DIRECT, f08c47fec0942fa0"
    return HttpResponse(linea_ads, content_type="text/plain")