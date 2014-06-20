from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^login/$', 'merchants.views.login_request', name='login_request'),
    url(r'^logout/?$', 'merchants.views.logout_request', name='logout'),

    url(r'^app/$', 'users.views.customer_dashboard', name='customer_dashboard'),
    url(r'^simulate-deposit/$', 'users.views.simulate_deposit_detected', name='simulate_deposit_detected'),

    url(r'^register-merchant/$', 'merchants.views.register_merchant', name='register_merchant'),

    # Merchant Settings
    url(r'^merchant-settings/$', 'merchants.views.merchant_settings', name='merchant_settings'),
    url(r'^profile/$', 'merchants.views.merchant_profile', name='merchant_profile'),
    url(r'^transactions/$', 'merchants.views.merchant_transactions', name='merchant_transactions'),
    url(r'^edit-personal-info/$', 'merchants.views.edit_personal_info', name='edit_personal_info'),
    url(r'^edit-merchant-info/$', 'merchants.views.edit_merchant_info', name='edit_merchant_info'),
    url(r'^edit-btc-info/$', 'merchants.views.edit_bitcoin_info', name='edit_bitcoin_info'),

    # API Partners
    url(r'^coinbase/$', 'merchants.views.coinbase', name='coinbase'),

    # AJAX Calls
    url(r'^poll-deposits/$', 'bitcoins.views.poll_deposits', name='poll_deposits'),
    url(r'^get-bitcoin-price/$', 'bitcoins.views.get_bitcoin_price', name='get_bitcoin_price'),
    url(r'^get-deposit-address/$', 'bitcoins.views.get_next_deposit_address', name='get_next_deposit_address'),
    url(r'^customer-confirm-deposit/$', 'bitcoins.views.customer_confirm_deposit', name='customer_confirm_deposit'),
    url(r'^merchant-complete-deposit/$', 'bitcoins.views.merchant_complete_deposit', name='merchant_complete_deposit'),
    url(r'^cancel-address/$', 'bitcoins.views.cancel_address', name='cancel_address'),
    url(r'^cancel-buy/$', 'bitcoins.views.cancel_buy', name='cancel_buy'),


    # Inbound Webhooks
    url(r'^bci-webhook/(?P<random_id>\w+)$', 'bitcoins.views.process_bci_webhook', name='process_bci_webhook'),
    url(r'^blockcypher-webhook/(?P<random_id>\w+)$', 'bitcoins.views.process_blockcypher_webhook', name='process_blockcypher_webhook'),

    # Static Pages
    url(r'^$', 'users.views.home', name='home'),  # homepage
    url(r'^help/', TemplateView.as_view(template_name='fixed_pages/help.html'), name='help'),
    url(r'^team/', TemplateView.as_view(template_name='fixed_pages/team.html'), name='team'),
    url(r'^contact/', TemplateView.as_view(template_name='fixed_pages/contact.html'), name='contact'),

    url(r'^admin/', include(admin.site.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),
)
