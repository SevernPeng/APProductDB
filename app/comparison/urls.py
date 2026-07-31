from django.urls import path

from . import views

app_name = "comparison"

urlpatterns = [
    path("", views.benchmark, name="benchmark"),
    path("compare/", views.compare, name="compare"),
    path("compare/export/", views.export_comparison, name="export"),
]
