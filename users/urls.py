# users/urls.py

from django.urls import path
from . import views
from . import views_user_management as um_views

app_name = "users"

urlpatterns = [

    # =========================================
    # AUTHENTICATION
    # =========================================
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("redirect/", views.role_redirect, name="role_redirect"),

    # =========================================
    # DASHBOARDS
    # =========================================
    path("dashboard/admin/", views.dashboard_administrator, name="dashboard_administrator"),
    path("dashboard/staff/", views.dashboard_staff, name="dashboard_staff"),
    path("dashboard/custodian/", views.dashboard_custodian, name="dashboard_custodian"),
    path("dashboard/inspection/", views.dashboard_inspection, name="dashboard_inspection"),
    path("dashboard/supply/", views.dashboard_supply, name="dashboard_supply"),

    # =========================================
    # SYSTEM ADMIN
    # =========================================
    path("entity/create/", um_views.create_entity_and_admin, name="create_entity_admin"),

    # =========================================
    # USER MANAGEMENT (ADMINISTRATOR)
    # =========================================
    path("management/users/", um_views.user_list, name="user_list"),
    path("management/users/create/", um_views.create_user, name="create_user"),
    path(
        "management/users/<int:user_id>/deactivate/",
        um_views.deactivate_user,
        name="deactivate_user",
    ),
]