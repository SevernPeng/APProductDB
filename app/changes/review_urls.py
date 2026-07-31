from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path("", views.review_list, name="list"),
    path("<int:pk>/", views.review_detail, name="detail"),
    path("<int:pk>/approve/", views.review_approve, name="approve"),
    path("<int:pk>/reject/", views.review_reject, name="reject"),
]
