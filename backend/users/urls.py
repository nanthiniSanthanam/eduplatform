from django.urls import path
from . import views

urlpatterns = [
    path('enrollments/', views.UserEnrollmentsView.as_view(),
         name='user-enrollments'),
]
