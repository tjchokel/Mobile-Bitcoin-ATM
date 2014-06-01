from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    url(r'^login/$', 'business.views.login_request', name='login_request'),
    url(r'^logout/?$', 'business.views.logout_request', name='logout'),

    url(r'^app/$', 'app.views.customer_dashboard', name='customer_dashboard'),
    url(r'^simulate-deposit/$', 'app.views.simulate_deposit_detected', name='simulate_deposit_detected'),
    url(r'^deposit/$', 'app.views.deposit_dashboard', name='deposit_dashboard'),

    url(r'^register/$', 'business.views.register_router',
        name='register_router'),
    url(r'^register-account/$', 'business.views.register_account', name='register_account'),
    url(r'^register-personal/$', 'business.views.register_personal', name='register_personal'),
    url(r'^register-business/$', 'business.views.register_business', name='register_business'),
    url(r'^register-bitcoins/$', 'business.views.register_bitcoins', name='register_bitcoins'),
    
    url(r'^business-settings/$', 'business.views.business_settings', name='business_settings'),
    url(r'^profile/$', 'business.views.business_profile', name='business_profile'),
    url(r'^transactions/$', 'business.views.transactions', name='transactions'),
    url(r'^edit-personal-info/$', 'business.views.edit_personal_info', name='edit_personal_info'),
    url(r'^edit-business-info/$', 'business.views.edit_business_info', name='edit_business_info'),
    url(r'^edit-btc-info/$', 'business.views.edit_bitcoin_info', name='edit_bitcoin_info'),

    url(r'^poll-deposits/$', 'bitcoins.views.poll_deposits', name='poll_deposits'),
    url(r'^get-bitcoin-price/$', 'bitcoins.views.get_bitcoin_price', name='get_bitcoin_price'),
    url(r'^get-deposit-address/$', 'bitcoins.views.get_next_deposit_address', name='get_next_deposit_address'),

    url(r'^bci-webhook/$', 'bitcoins.views.process_bci_webook', name='process_bci_webhook'),

    url(r'^admin/', include(admin.site.urls)),
)
