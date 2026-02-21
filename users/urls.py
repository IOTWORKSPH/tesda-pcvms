#user urls.py codes 
from django.urls import path
from . import views

app_name = "users"

from django.urls import path
from . import views

app_name = "users"   # THIS IS VERY IMPORTANT

urlpatterns = [

    # Authentication
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("redirect/", views.role_redirect, name="role_redirect"),

    # Dashboards
    path("dashboard/admin/", views.dashboard_administrator, name="dashboard_administrator"),
    path("dashboard/staff/", views.dashboard_staff, name="dashboard_staff"),
    path("dashboard/custodian/", views.dashboard_custodian, name="dashboard_custodian"),
    path("dashboard/inspection/", views.dashboard_inspection, name="dashboard_inspection"),
    path("dashboard/supply/", views.dashboard_supply, name="dashboard_supply"),
]
