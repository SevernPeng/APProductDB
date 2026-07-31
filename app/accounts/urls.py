from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("manage/", views.account_list, name="list"),
    path("manage/<int:pk>/role/", views.update_role, name="update-role"),
]
