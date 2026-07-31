from django.urls import path

from . import views

app_name = "imports"

urlpatterns = [
    path("", views.upload, name="upload"),
    path(
        "templates/<int:product_type_id>/",
        views.download_template,
        name="download_template",
    ),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/source/", views.source_file, name="source_file"),
    path("<int:pk>/errors/", views.error_report, name="error_report"),
]
