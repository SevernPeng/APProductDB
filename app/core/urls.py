from django.urls import path

from . import views

urlpatterns = [
    path("", views.product_list, name="home"),
    path("products/", views.product_list, name="product-list"),
    path("products/<int:pk>/", views.product_detail, name="product-detail"),
    path("products/<int:pk>/image/", views.product_image, name="product-image"),
    path(
        "products/<slug:family_slug>/<slug:subcategory_slug>/",
        views.product_list,
        name="product-subcategory",
    ),
    path(
        "products/<slug:family_slug>/",
        views.product_list,
        name="product-family",
    ),
    path("health/", views.health, name="health"),
]
