from django.urls import path
from . import views

app_name = 'approvals'

urlpatterns = [
    path('', views.ApprovalDashboardView.as_view(), name='dashboard'),
    path('request/<int:pk>/', views.ApprovalRequestDetailView.as_view(), name='request_detail'),
    path('create/<int:submission_pk>/', views.CreateApprovalRequestView.as_view(), name='create_request'),
    path('request/<int:pk>/approve/', views.ApproveRequestView.as_view(), name='approve_request'),
    path('request/<int:pk>/reject/', views.RejectRequestView.as_view(), name='reject_request'),
    path('compare/', views.CompareVersionsView.as_view(), name='compare_versions'),
]