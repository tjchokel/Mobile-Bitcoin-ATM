from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^login/$', 'merchants.views.login_request', name='login_request'),
    url(r'^logout/?$', 'merchants.views.logout_request', name='logout'),
    url(r'^request-new-password/?$', 'users.views.request_new_pw', name='request_new_pw'),
    url(r'^reset-password/(?P<verif_key>\w+)$', 'users.views.reset_password', name='reset_password'),
    url(r'^change-dassword/?$', 'users.views.change_password', name='change_password'),

    url(r'^app/$', 'users.views.customer_dashboard', name='customer_dashboard'),

    url(r'^register/$', 'merchants.views.register_router', name='register_router'),
    url(r'^register-merchant/$', 'merchants.views.register_merchant', name='register_merchant'),
    url(r'^register-bitcoin/$', 'merchants.views.register_bitcoin', name='register_bitcoin'),
    url(r'^register-customer/$', 'users.views.register_customer', name='register_customer'),


    # Merchant Settings
    url(r'^merchant-settings/$', 'merchants.views.merchant_settings', name='merchant_settings'),
    url(r'^profile/$', 'merchants.views.merchant_profile', name='merchant_profile'),
    url(r'^transactions/$', 'merchants.views.merchant_transactions', name='merchant_transactions'),
    url(r'^edit-personal-info/$', 'merchants.views.edit_personal_info', name='edit_personal_info'),
    url(r'^edit-hours-info/$', 'merchants.views.edit_hours_info', name='edit_hours_info'),
    url(r'^edit-merchant-info/$', 'merchants.views.edit_merchant_info', name='edit_merchant_info'),
    url(r'^edit-btc-info/$', 'merchants.views.edit_bitcoin_info', name='edit_bitcoin_info'),
    url(r'^password/$', 'merchants.views.password_prompt', name='password_prompt'),

    # API Partners
    url(r'^coinbase/$', 'credentials.views.coinbase_creds', name='coinbase_creds'),
    url(r'^bitstamp/$', 'credentials.views.bitstamp_creds', name='bitstamp_creds'),
    url(r'^blockchain/$', 'credentials.views.blockchain_creds', name='blockchain_creds'),

    # AJAX Calls
    url(r'^poll-deposits/$', 'bitcoins.views.poll_deposits', name='poll_deposits'),
    url(r'^get-bitcoin-price/$', 'bitcoins.views.get_bitcoin_price', name='get_bitcoin_price'),
    url(r'^get-deposit-address/$', 'bitcoins.views.get_next_deposit_address', name='get_next_deposit_address'),
    url(r'^customer-confirm-deposit/$', 'bitcoins.views.customer_confirm_deposit', name='customer_confirm_deposit'),
    url(r'^merchant-complete-deposit/$', 'bitcoins.views.merchant_complete_deposit', name='merchant_complete_deposit'),
    url(r'^cancel-address/$', 'bitcoins.views.cancel_address', name='cancel_address'),
    url(r'^cancel-buy/$', 'bitcoins.views.cancel_buy', name='cancel_buy'),
    # API Partner AJAX Calls (TODO: DRY this out)
    url(r'^get-new-address/(?P<credential_id>\w+)$', 'credentials.views.get_new_address', name='get_new_address'),
    url(r'^get-credential-balance/(?P<credential_id>\w+)$', 'credentials.views.get_credential_balance', name='get_credential_balance'),
    url(r'^refresh-cb-credentials/$', 'credentials.views.refresh_cb_credentials', name='refresh_cb_credentials'),
    url(r'^disable-cb-credentials/$', 'credentials.views.disable_cb_credentials', name='disable_cb_credentials'),
    url(r'^refresh-bs-credentials/$', 'credentials.views.refresh_bs_credentials', name='refresh_bs_credentials'),
    url(r'^disable-bs-credentials/$', 'credentials.views.disable_bs_credentials', name='disable_bs_credentials'),
    url(r'^refresh-bci-credentials/$', 'credentials.views.refresh_bci_credentials', name='refresh_bci_credentials'),
    url(r'^disable-bci-credentials/$', 'credentials.views.disable_bci_credentials', name='disable_bci_credentials'),

    # Inbound Webhooks
    url(r'^bci-webhook/(?P<random_id>\w+)$', 'bitcoins.views.process_bci_webhook', name='process_bci_webhook'),

    # Static Pages
    url(r'^$', 'users.views.home', name='home'),  # homepage
    url(r'^help/', TemplateView.as_view(template_name='fixed_pages/help.html'), name='help'),
    url(r'^team/', TemplateView.as_view(template_name='fixed_pages/team.html'), name='team'),
    url(r'^terms/', TemplateView.as_view(template_name='fixed_pages/terms.html'), name='terms'),
    url(r'^privacy/', TemplateView.as_view(template_name='fixed_pages/privacy.html'), name='privacy'),
    url(r'^cold-storage-guide/', TemplateView.as_view(template_name='fixed_pages/cold_storage_guide.html'), name='cold_storage_guide'),
    url(r'^contact/', 'users.views.contact', name='contact'),
    url(r'^bitstamp-instructions/', TemplateView.as_view(template_name='fixed_pages/bitstamp_instructions.html'), name='bitstamp_instructions'),
    url(r'^coinbase-instructions/', TemplateView.as_view(template_name='fixed_pages/coinbase_instructions.html'), name='coinbase_instructions'),
    url(r'^blockchain-instructions/', TemplateView.as_view(template_name='fixed_pages/blockchain_instructions.html'), name='blockchain_instructions'),
    url(r'^promotional-material/', TemplateView.as_view(template_name='fixed_pages/promotional_material.html'), name='promotional_material'),
    url(r'^jobs/', TemplateView.as_view(template_name='fixed_pages/jobs.html'), name='jobs'),
    url(r'^press/', TemplateView.as_view(template_name='fixed_pages/press.html'), name='press'),

    url(r'^admin/', include(admin.site.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),

    # Logging Test
    url(r'^fail500/$', 'services.views.fail500', name='services500'),

    # Short URLs
    url(r'^(?P<uri>[-\w]+)/$', 'profiles.views.merchant_site', name='merchant_site'),

)
