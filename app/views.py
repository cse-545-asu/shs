from django.contrib.auth.models import Group
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django_registration.backends.activation.views import RegistrationView
from django.contrib.auth.models import Group

from app.decorators import check_view_permissions


@login_required
def index(request):
    return render(request, "home.html")


class CustomRegistrationView(RegistrationView):
    def register(self, form):
        user =  super().register(form)
        patient_group = Group.objects.get(name='patient')
        patient_group.user_set.add(user)


@login_required
@check_view_permissions("admin")
def admin(request):
    return render("hello")
    