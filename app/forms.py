from django import forms
from allauth.account.forms import SignupForm


class SignupForm(SignupForm):
    def save(self, request):
        user = super().save(request)
        return user
