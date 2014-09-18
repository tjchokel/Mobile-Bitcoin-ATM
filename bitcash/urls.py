from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

from bitcash.settings import IS_PRODUCTION

from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^login/$', 'merchants.views.login_request', name='login_request'),
    url(r'^logout/?$', 'merchants.views.logout_request', name='logout'),
    url(r'^request-new-password/?$', 'users.views.request_new_password', name='request_new_password'),
    url(r'^reset-password/(?P<verif_key>\w+)/?$', 'users.views.reset_password', name='reset_password'),
    url(r'^set-new-password/?$', 'users.views.set_new_password', name='set_new_password'),
    url(r'^change-password/?$', 'users.views.change_password', name='change_password'),

    url(r'^app/$', 'shoppers.views.customer_dashboard', name='customer_dashboard'),

    url(r'^register/$', 'merchants.views.register_router', name='register_router'),
    url(r'^register-merchant/$', 'merchants.views.register_merchant', name='register_merchant'),
    url(r'^register-bitcoin/$', 'merchants.views.register_bitcoin', name='register_bitcoin'),
    url(r'^register-customer/$', 'users.views.register_customer', name='register_customer'),

    # Merchant Settings
    url(r'^merchant-settings/$', 'merchants.views.merchant_settings', name='merchant_settings'),
    url(r'^profile/$', 'merchants.views.merchant_profile', name='merchant_profile'),
    url(r'^transactions/$', 'merchants.views.merchant_transactions', name='merchant_transactions'),
    url(r'^edit-hours-info/$', 'merchants.views.edit_hours_info', name='edit_hours_info'),
    url(r'^password/$', 'merchants.views.password_prompt', name='password_prompt'),
    url(r'^wallet/$', 'credentials.views.base_creds', name='base_creds'),

    # AJAX Calls
    url(r'^poll-deposits/$', 'bitcoins.views.poll_deposits', name='poll_deposits'),
    url(r'^get-bitcoin-price/$', 'bitcoins.views.get_bitcoin_price', name='get_bitcoin_price'),  # In the app
    url(r'^get-bitcoin-price/(?P<merchant_id>\w+)/?$', 'bitcoins.views.get_bitcoin_price', name='get_bitcoin_price'),  # Looking at the merchant profile (likely logged out):
    url(r'^get-deposit-address/$', 'bitcoins.views.get_next_deposit_address', name='get_next_deposit_address'),
    url(r'^customer-confirm-deposit/$', 'bitcoins.views.customer_confirm_deposit', name='customer_confirm_deposit'),
    url(r'^merchant-complete-deposit/$', 'bitcoins.views.merchant_complete_deposit', name='merchant_complete_deposit'),
    url(r'^cancel-address/$', 'bitcoins.views.cancel_address', name='cancel_address'),
    url(r'^cancel-buy/$', 'bitcoins.views.cancel_buy', name='cancel_buy'),
    url(r'^city-autocomplete/(?P<city>\w+)/(?P<country>\w+)$', 'users.views.city_autocomplete', name='city_autocomplete'),
    # API Partner AJAX Calls
    url(r'^get-new-address/(?P<credential_id>\w+)$', 'credentials.views.get_new_address', name='get_new_address'),
    url(r'^get-current-balance/(?P<credential_id>\w+)$', 'credentials.views.get_current_balance', name='get_current_balance'),
    url(r'^refresh-credentials/(?P<credential_id>\w+)$', 'credentials.views.refresh_credentials', name='refresh_credentials'),

    # Inbound Webhooks
    url(r'^bci-webhook/(?P<random_id>\w+)$', 'bitcoins.views.process_bci_webhook', name='process_bci_webhook'),

    # Static Pages
    url(r'^$', 'users.views.home', name='home'),  # homepage
    url(r'^help/', TemplateView.as_view(template_name='fixed_pages/help.html'), name='help'),
    url(r'^team/', TemplateView.as_view(template_name='fixed_pages/team.html'), name='team'),
    url(r'^terms/', TemplateView.as_view(template_name='fixed_pages/terms.html'), name='terms'),
    url(r'^privacy/', TemplateView.as_view(template_name='fixed_pages/privacy.html'), name='privacy'),
    url(r'^cold-storage-guide/', 'blog.views.cold_storage_guide', name='cold_storage_guide'),
    url(r'^contact/', 'users.views.contact', name='contact'),
    url(r'^bitstamp-instructions/', TemplateView.as_view(template_name='fixed_pages/bitstamp_instructions.html'), name='bitstamp_instructions'),
    url(r'^coinbase-instructions/', TemplateView.as_view(template_name='fixed_pages/coinbase_instructions.html'), name='coinbase_instructions'),
    url(r'^blockchain-instructions/', TemplateView.as_view(template_name='fixed_pages/blockchain_instructions.html'), name='blockchain_instructions'),
    url(r'^promotional-material/', TemplateView.as_view(template_name='fixed_pages/promotional_material.html'), name='promotional_material'),
    url(r'^jobs/', TemplateView.as_view(template_name='fixed_pages/jobs.html'), name='jobs'),
    url(r'^press/', TemplateView.as_view(template_name='fixed_pages/press.html'), name='press'),

    # blog
    url(r'^blog/category/(?P<slug>[^\.]+)', 'blog.views.view_category', name='view_blog_category'),
    url(r'^blog/(?P<slug>[^\.]+)', 'blog.views.view_post', name='view_blog_post'),
    url(r'^blog/', 'blog.views.blog_index', name='blog_index'),

    url(r'^admin/', include(admin.site.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),

    # Logging Test
    url(r'^fail500/$', 'services.views.fail500', name='services500'),

    # Short URLs (this must be last for obvious reasons)
    url(r'^(?P<uri>[-\w]+)/$', 'profiles.views.merchant_site', name='merchant_site'),
    url(r'', include('two_factor.urls', 'two_factor')),
)

if not IS_PRODUCTION:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
