from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    
    url(r'^login/$', 'business.views.login_request', name='login_request'),
    url(r'^logout/?$', 'business.views.logout_request', name='logout'),

    url(r'^app/$', 'app.views.customer_dashboard', name='customer_dashboard'),
    url(r'^simulate-deposit/$', 'app.views.simulate_deposit_detected', name='simulate_deposit_detected'),
    url(r'^deposit/$', 'app.views.deposit_dashboard', name='deposit_dashboard'),

    url(r'^register-account/$', 'business.views.register_account', name='register_account'),
    url(r'^register-personal/$', 'business.views.register_personal', name='register_personal'),
    url(r'^register-business/$', 'business.views.register_business', name='register_business'),
    url(r'^business-dash/$', 'business.views.business_dash', name='business_dash'),

    url(r'^poll-deposits/$', 'bitcoins.views.poll_deposits', name='poll_deposits'),
    url(r'^get-bitcoin-price/$', 'bitcoins.views.get_bitcoin_price', name='get_bitcoin_price'),

    url(r'^admin/', include(admin.site.urls)),
)
