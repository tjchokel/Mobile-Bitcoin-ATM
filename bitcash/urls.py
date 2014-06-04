from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    url(r'^login/$', 'merchants.views.login_request', name='login_request'),
    url(r'^logout/?$', 'merchants.views.logout_request', name='logout'),

    url(r'^app/$', 'users.views.customer_dashboard', name='customer_dashboard'),
    url(r'^simulate-deposit/$', 'users.views.simulate_deposit_detected', name='simulate_deposit_detected'),
    url(r'^deposit/$', 'users.views.deposit_dashboard', name='deposit_dashboard'),

    url(r'^register/$', 'merchants.views.register_router',
        name='register_router'),
    url(r'^register-account/$', 'merchants.views.register_account', name='register_account'),
    url(r'^register-personal/$', 'merchants.views.register_personal', name='register_personal'),
    url(r'^register-merchant/$', 'merchants.views.register_merchant', name='register_merchant'),
    url(r'^register-bitcoins/$', 'merchants.views.register_bitcoins', name='register_bitcoins'),

    url(r'^merchant-settings/$', 'merchants.views.merchant_settings', name='merchant_settings'),
    url(r'^profile/$', 'merchants.views.merchant_profile', name='merchant_profile'),
    url(r'^transactions/$', 'merchants.views.transactions', name='transactions'),
    url(r'^edit-personal-info/$', 'merchants.views.edit_personal_info', name='edit_personal_info'),
    url(r'^edit-merchant-info/$', 'merchants.views.edit_merchant_info', name='edit_merchant_info'),
    url(r'^edit-btc-info/$', 'merchants.views.edit_bitcoin_info', name='edit_bitcoin_info'),

    url(r'^poll-deposits/$', 'bitcoins.views.poll_deposits', name='poll_deposits'),
    url(r'^get-bitcoin-price/$', 'bitcoins.views.get_bitcoin_price', name='get_bitcoin_price'),
    url(r'^get-deposit-address/$', 'bitcoins.views.get_next_deposit_address', name='get_next_deposit_address'),
    url(r'^confirm-deposit/$', 'bitcoins.views.confirm_deposit', name='confirm_deposit'),
    url(r'^complete-deposit/$', 'bitcoins.views.complete_deposit', name='complete_deposit'),

    url(r'^bci-webhook/(?P<random_id>\w+)$', 'bitcoins.views.process_bci_webhook', name='process_bci_webhook'),
    url(r'^blockcypher-webhook/(?P<random_id>\w+)$', 'bitcoins.views.process_blockcypher_webhook', name='process_blockcypher_webhook'),

    url(r'^admin/', include(admin.site.urls)),
)
