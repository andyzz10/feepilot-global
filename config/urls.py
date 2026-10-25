"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import path
from engine.views import calculator_view, sitemap_xml, legal_view, ads_txt

from django.urls import path
from engine.views import calculator_view, sitemap_xml, legal_view, ads_txt, robots_txt

urlpatterns = [
    path('', calculator_view, {'lang': 'en', 'slug': 'stripe'}, name='home'),
    path('sitemap.xml', sitemap_xml, name='sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('ads.txt', ads_txt, name='ads_txt'),
    path('legal/<slug:page>/', legal_view, name='legal'),
    path('<str:lang>/<slug:slug>-fee-calculator/', calculator_view, name='calc_single'),
    path('<str:lang>/<slug:slug>-fees/', calculator_view, name='calc_vs'),
]