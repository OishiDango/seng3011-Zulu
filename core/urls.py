from django.urls import path
from . import views
from .views import stats_regions, stats_timeseries

urlpatterns = [
    path('search-def/', views.simple_scrapy_test, name='search_def'),
    path('alerts', views.get_alerts),
    path('stats/regions', stats_regions, name="stats_regions"),
    path('stats/timeseries', stats_timeseries, name="stats_timeseries"),
]
