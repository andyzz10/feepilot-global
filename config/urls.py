"""
URL configuration for config project.

Cambios: rutas legales en inglés (/legal/<página>/) y en español (/es/legal/<página>/).
Las rutas legales van ANTES de las de las calculadoras.
"""
from django.contrib import admin
from django.urls import path
from engine.views import calculator_view, sitemap_xml, legal_view, ads_txt, robots_txt

urlpatterns = [
    path('', calculator_view, {'lang': 'en', 'slug': 'stripe'}, name='home'),
    path('sitemap.xml', sitemap_xml, name='sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('ads.txt', ads_txt, name='ads_txt'),
    path('legal/<slug:page>/', legal_view, name='legal'),
    path('<str:lang>/legal/<slug:page>/', legal_view, name='legal_lang'),
    path('<str:lang>/<slug:slug>-fee-calculator/', calculator_view, name='calc_single'),
    path('<str:lang>/<slug:slug>-fees/', calculator_view, name='calc_vs'),
]
