from django.urls import path
from . import views
from .views import stats_regions

urlpatterns = [
    path('hello/', views.hello_world),
    path('search-def/', views.simple_scrapy_test, name='search_def'),
    path('stats/regions', stats_regions, name="stats_regions"),
    path('stats/diseases', views.stats_diseases, name="stats_diseases")
]
