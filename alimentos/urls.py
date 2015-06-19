"""alimentos URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
#from django.contrib import admin
from nutrientes import views

urlpatterns = [
    #url(r'^admin/', include(admin.site.urls)),
    url(r'^$', views.index, name="index"),
    url(r'^ajax_search/$', views.ajax_search, name="ajax_search"),
    url(r'^food/(?P<ndb_no>\w+)/$', views.food, name="view_food"),
    url(r'^romega/$', views.romega, name="view_romega"),
    url(r'^set_comparation/(?P<ndb_no>\w+)/(?P<operation>\w+)/$', views.set_comparation, name="view_set_comparation"),
    url(r'^food_compare/$', views.food_compare, name="food_compare"),
    url(r'^category_food/(?P<category_id>\w+)/(?P<order>\w+)/$', views.list_food_category, name="list_food_category"),
    url(r'^best_of_nutrients/$', views.best_of_nutrients, name="best_of_nutrients"),
    url(r'^about/$', views.about, name="about"),
    url(r'^nutrient_selection/$', views.nutrient_selection, name="nutrient_selection"),
    url(r'^ranking_list/$', views.ranking_list, name="ranking_list"),
    url(r'^result_long_search/$', views.result_long_search, name="result_long_search"),
    url(r'^graph_all_nutr/$', views.graph_all_nutr, name="graph_all_nutr"),
    url(r'^equivalents/(?P<ndb_no>\w+)/$', views.equivalents, name="equivalents"),
    url(r'^principal_nutrients_graph/$', views.principal_nutrients_graph, name="principal_nutrients_graph"),
    url(r'^contact/$', views.contact, name="contact")
]
