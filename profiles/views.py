from django.shortcuts import get_object_or_404

from annoying.decorators import render_to

from profiles.models import ShortURL


@render_to('profiles/main.html')
def merchant_site(request, uri):
    short_url_obj = get_object_or_404(ShortURL, uri=uri, deleted_at=None)
    return {'merchant': short_url_obj.merchant}
