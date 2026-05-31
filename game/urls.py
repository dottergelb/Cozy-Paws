from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("play/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("settings/", views.settings, name="settings"),
    path("pets/new/", views.create_pet, name="create_pet"),
    path("pets/<int:pet_id>/select/", views.select_pet, name="select_pet"),
    path("pets/action/<str:action>/", views.pet_action, name="pet_action"),
    path("shop/", views.shop, name="shop"),
    path("shop/buy/<int:item_id>/", views.buy_item, name="buy_item"),
    path("inventory/", views.inventory, name="inventory"),
    path("inventory/use/<int:inventory_id>/", views.use_item, name="use_item"),
    path("quests/", views.quests, name="quests"),
    path("quests/claim/<int:progress_id>/", views.claim_quest, name="claim_quest"),
    path("rating/", views.rating, name="rating"),
]
