from django.urls import path
from . import views


app_name = 'main'  # here for namespacing of urls.

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path('api/trades/', views.trades, name='trades'),
    path('api/last-modified/', views.last_modified, name='last_modified'),
    path('api/current_holdings/', views.current_holdings, name='current_holdings'),
    path('api/history_data/', views.history_data, name='history_data'),
]