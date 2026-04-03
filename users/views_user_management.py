# users/views_user_management.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from users.decorators import role_required
from users.models import Entity, User
from users.forms_user_management import (
    EntityCreateForm,
    AdministratorCreateForm,
    UserCreateForm,
)
from users.services.user_service import UserService


# ==========================================================
# SYSTEM ADMIN – CREATE ENTITY + ADMINISTRATOR
# ==========================================================

@login_required
def create_entity_and_admin(request):

    if not request.user.is_superuser:
        return redirect("users:role_redirect")

    if request.method == "POST":
        entity_form = EntityCreateForm(request.POST)
        admin_form = AdministratorCreateForm(request.POST)

        if entity_form.is_valid() and admin_form.is_valid():

            entity = entity_form.save()

            UserService.create_administrator(
                entity=entity,
                form_data=admin_form.cleaned_data,
                created_by=request.user,
            )

            messages.success(
                request,
                "Entity and Administrator created successfully. Email sent."
            )
            return redirect("users:role_redirect")

    else:
        entity_form = EntityCreateForm()
        admin_form = AdministratorCreateForm()

    return render(
        request,
        "users/user_management/create_entity_admin.html",
        {
            "entity_form": entity_form,
            "admin_form": admin_form,
        },
    )


# ==========================================================
# ADMINISTRATOR – USER LIST
# ==========================================================

@login_required
@role_required("Administrator")
def user_list(request):

    entity = request.user.entity

    users = User.objects.filter(
        entity=entity
    ).select_related("entity")

    return render(
        request,
        "users/user_management/user_list.html",
        {
            "users": users,
        },
    )


# ==========================================================
# ADMINISTRATOR – CREATE USER
# ==========================================================

@login_required
@role_required("Administrator")
def create_user(request):

    entity = request.user.entity

    if request.method == "POST":
        form = UserCreateForm(request.POST)

        if form.is_valid():

            UserService.create_entity_user(
                entity=entity,
                form_data=form.cleaned_data,
                created_by=request.user,
            )

            messages.success(
                request,
                "User created successfully. Email sent."
            )

            return redirect("users:user_list")

    else:
        form = UserCreateForm()

    return render(
        request,
        "users/user_management/create_user.html",
        {
            "form": form,
        },
    )


# ==========================================================
# ADMINISTRATOR – DEACTIVATE USER
# ==========================================================

@login_required
@role_required("Administrator")
def deactivate_user(request, user_id):

    entity = request.user.entity

    user = get_object_or_404(
        User,
        id=user_id,
        entity=entity
    )

    if user == request.user:
        messages.error(request, "You cannot deactivate yourself.")
        return redirect("users:user_list")

    user.is_active = False
    user.save(update_fields=["is_active"])

    messages.success(request, "User deactivated successfully.")

    return redirect("users:user_list")