from django.urls import path

from .apis import Login, Logout, Register

urlpatterns = [
    path("register/", Register.as_view(), name="users-register"),
    path("login/", Login.as_view(), name="users-login"),
    path("logout/", Logout.as_view(), name="users-logout"),
]
