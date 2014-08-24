from django.shortcuts import get_object_or_404

from annoying.decorators import render_to

from profiles.models import ShortURL


@render_to('profiles/main.html')
def merchant_site(request, uri):
    short_url_obj = get_object_or_404(ShortURL, uri_lowercase=uri.lower(), deleted_at=None)
    merchant = short_url_obj.merchant

    is_users_profile = False
    if merchant.user == request.user:
        is_users_profile = True

    doc_object = merchant.get_doc_obj()
    hours_formatted = merchant.get_hours_formatted()
    hours_dict = merchant.get_hours_dict()

    return{
            'merchant': short_url_obj.merchant,
            'is_users_profile': is_users_profile,
            'doc_object': doc_object,
            'hours_dict': hours_dict,
            'biz_hours': hours_formatted,
    }
