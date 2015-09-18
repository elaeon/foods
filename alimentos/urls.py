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
from nutrientes import views as nutr_views
from news import views as news_views
from news.api import router

urlpatterns = [
    url(r'^$', nutr_views.index, name="index"),
    url(r'^ajax_search/$', nutr_views.ajax_search, name="ajax_search"),
    url(r'^food/(?P<ndb_no>\w+)/$', nutr_views.food, name="view_food"),
    url(r'^romega/$', nutr_views.romega, name="view_romega"),
    url(r'^set_comparation/(?P<ndb_no>\w+)/(?P<operation>\w+)/$', nutr_views.set_comparation, name="view_set_comparation"),
    url(r'^food_compare/$', nutr_views.food_compare, name="food_compare"),
    url(r'^analyze_food/$', nutr_views.analyze_food, name="analyze_food"),
    url(r'^category_food/(?P<category_id>\w+)/(?P<order>\w+)/$', nutr_views.list_food_category, name="list_food_category"),
    url(r'^best_of_nutrients/$', nutr_views.best_of_nutrients, name="best_of_nutrients"),
    url(r'^about/$', nutr_views.about, name="about"),
    url(r'^nutrient_selection/$', nutr_views.nutrient_selection, name="nutrient_selection"),
    url(r'^ranking_list/(?P<order>\w+)/$', nutr_views.ranking_list, name="ranking_list"),
    url(r'^result_long_search/$', nutr_views.result_long_search, name="result_long_search"),
    url(r'^graph_all_nutr/$', nutr_views.graph_all_nutr, name="graph_all_nutr"),
    url(r'^equivalents/(?P<ndb_no>\w+)/$', nutr_views.equivalents, name="equivalents"),
    url(r'^principal_nutrients_graph/$', nutr_views.principal_nutrients_graph, name="principal_nutrients_graph"),
    url(r'^contact/$', nutr_views.contact, name="contact"),
    url(r'^recipes/$', nutr_views.recipes, name="recipes"),
    url(r'^share_recipe/$', nutr_views.share_recipe, name="share_recipe"),
    url(r'^analyze_menu/$', nutr_views.analyze_menu, name="analyze_menu"),
    url(r'^change_perfil/$', nutr_views.change_perfil, name="change_perfil"),
    url(r'^complex_intake_nutrients/$', nutr_views.complex_intake_nutrients, name="complex_intake_nutrients"),
    url(r'^best_menu/$', nutr_views.best_menu, name="best_menu"),
    url(r'^news/$', nutr_views.news, name="nutr_news")
]

urlpatterns += [
    url(r'^api/news/', include(router.urls)),
]


