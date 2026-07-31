from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.product_list, name="product-list"),
    path("products/<int:pk>/", views.product_detail, name="product-detail"),
    path(
        "products/<int:pk>/datasheet/",
        views.product_datasheet,
        name="product-datasheet",
    ),
    path(
        "products/<int:pk>/datasheet/upload/",
        views.upload_datasheet,
        name="product-datasheet-upload",
    ),
    path(
        "products/<int:pk>/datasheet/url/",
        views.submit_datasheet_url,
        name="product-datasheet-url",
    ),
    path(
        "products/<int:pk>/datasheet/reprocess/",
        views.reprocess_datasheet_url,
        name="product-datasheet-reprocess",
    ),
    path("health/", views.health, name="health"),
]
