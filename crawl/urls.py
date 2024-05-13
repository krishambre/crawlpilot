from django.urls import path
from . import views

urlpatterns = [
    path('results/<str:request_id>/', views.get_scrape_results, name='get_scrape_results'),
    path('cosine/<str:request_id>/', views.get_cosine_similarity, name='get_cosine_similarity'),
    path('bulkScrape/', views.bulk_scrape, name='bulk_scrape'),
    path('report/', views.ReportView.as_view(), name='report'),
    path('scrape/', views.scrape_url, name='scrape_url'),
    path('all/', views.get_all_results, name='scrape_result_list'),
    path('request_status/', views.get_request_status, name='get_request_status'),
]