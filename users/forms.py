from django import forms
from django.utils.translation import ugettext_lazy as _
from countries import COUNTRY_DROPDOWN


class CustomerRegistrationForm(forms.Form):
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'me@example.com'}),
    )
    country = forms.ChoiceField(
        label=_('Country'),
        required=True,
        choices=COUNTRY_DROPDOWN,
        widget=forms.Select(attrs={'data-country': 'USA'}),
    )
    city = forms.CharField(
        label=_('City'),
        required=False,
    )


class ContactForm(forms.Form):
    email = forms.EmailField(
        label=_('Your Email'),
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'me@example.com'}),
    )
    name = forms.CharField(
        label=_('Name'),
        required=True,
    )
    message = forms.CharField(
        label=_('Message'),
        required=True,
        widget=forms.Textarea(),
    )


class RequestNewPWForm(forms.Form):
    email = forms.EmailField(
        label=_('Your Email'),
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'me@example.com'}),
        help_text=_('Be sure to enter the one you used when you created this account.'),
    )


class ChangePWForm(forms.Form):

    oldpassword = forms.CharField(
            required=True,
            label=_('Current Password'),
            widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
            help_text=_('Your existing password that you no longer want to use'),
    )

    newpassword = forms.CharField(
            required=True,
            label=_('New Password'),
            widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
            min_length=7,
            help_text=_('Please choose a new secure password'),
    )

    newpassword_confirm = forms.CharField(
            required=True,
            label=_('Confirm New Password'),
            widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(ChangePWForm, self).__init__(*args, **kwargs)

    def clean_oldpassword(self):
        password = self.cleaned_data['oldpassword']
        if not self.user.check_password(password):
            raise forms.ValidationError(_('Sorry, that password is not correct'))
        return password

    def clean(self):
        if self.cleaned_data.get('newpassword') != self.cleaned_data.get('newpassword_confirm'):
            raise forms.ValidationError(_('Your new passwords did not match.  Please try again.'))
        if self.cleaned_data.get('newpassword') == self.cleaned_data.get('oldpassword'):
            raise forms.ValidationError(_('Your old password matches your new password. Your password was not changed.'))
        else:
            return self.cleaned_data


class SetPWForm(forms.Form):

    newpassword = forms.CharField(
            required=True,
            label=_('New Password'),
            widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
            min_length=7,
            help_text=_('Please choose a new secure password'),
    )

    newpassword_confirm = forms.CharField(
            required=True,
            label=_('Confirm New Password'),
            widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
    )

    def clean(self):
        if self.cleaned_data.get('newpassword') != self.cleaned_data.get('newpassword_confirm'):
            raise forms.ValidationError(_('Your new passwords did not match.  Please try again.'))
        else:
            return self.cleaned_data
