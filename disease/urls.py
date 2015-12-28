from django.conf.urls import include, url

from disease import views as disease_views

urlpatterns = [
    url(r'^$', disease_views.index, name="disease_index"),
    url(r'^diabetes/$', disease_views.diabetes, name="diabetes"),
    url(r'^cancer/$', disease_views.cancer, name="cancer"),
]
