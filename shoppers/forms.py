from django import forms

import phonenumbers

from countries import COUNTRY_DROPDOWN


class ShopperInformationForm(forms.Form):
    name = forms.CharField(
        required=True,
        label='Name',
        widget=forms.TextInput(attrs={'placeholder': 'John Smith'}),
        min_length=2,
    )

    email = forms.EmailField(
        label='Email Address',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'me@example.com'}),
    )

    phone_country = forms.ChoiceField(
            label='Phone Country',
            required=False,
            choices=COUNTRY_DROPDOWN,
            widget=forms.Select(attrs={'data-country': 'USA'}),
    )

    phone_num = forms.CharField(
            label='Cell Phone Number in International Format',
            required=False,
            widget=forms.TextInput(attrs={'class': 'bfh-phone', 'data-country': 'id_phone_country'}),
    )

    def clean_phone_num(self):
        # TODO: restrict phone number to one of Plivo's serviced countries:
        # https://s3.amazonaws.com/mf-tmp/plivo_countries.txt
        phone_num = self.cleaned_data['phone_num']
        print 'phone_num', phone_num, type(phone_num), len(phone_num)
        if not phone_num or len(phone_num.strip()) < 4:
            return None
        try:
            pn_parsed = phonenumbers.parse(phone_num, None)
            if not phonenumbers.is_valid_number(pn_parsed):
                err_msg = "Sorry, that number isn't valid"
                raise forms.ValidationError(err_msg)
        except phonenumbers.NumberParseException:
            err_msg = "Sorry, that number doesn't look like a real number"
            raise forms.ValidationError(err_msg)
        return phone_num
