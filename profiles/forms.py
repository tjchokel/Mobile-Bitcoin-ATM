from django import forms
from django.utils.translation import ugettext_lazy as _


class ImageUploadForm(forms.Form):
    img_file = forms.ImageField(
        label=_('Image to Upload'),
        required=True,
        help_text=_('Files up to 5Mb only'),
    )
