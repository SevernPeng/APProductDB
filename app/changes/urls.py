from django.urls import path

from . import views

app_name = "changes"

urlpatterns = [
    path("", views.my_changes, name="mine"),
    path("mine/", views.my_changes, name="mine-alias"),
    path("new/<int:product_pk>/", views.suggest_change, name="suggest"),
    path("<int:pk>/", views.change_detail, name="detail"),
    path("<int:pk>/attachment/", views.change_attachment, name="attachment"),
]
