from django.conf.urls import include, url, patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings

from app.views import registration, login, get_user_by_id, change_avatar, change_name, get_brands, get_categories, \
    get_user_by_token, add_new_item, get_items_by_user_id, follow_user, unfollow_user, user_followers, user_followings,\
    send_comment, send_like, add_to_favorite, get_favorite_items, get_items_by_profile_type, \
    get_items_stylists_by_category, get_items_clients_by_category, get_stylist_sold_items, set_item_sold, change_item,\
    remove_item, remove_item_from_favorite, search_sold_items, search_unsold_items, rate_stylist, \
    search_all_items_client, search_all_items_stylist, sort_sold_items, sort_unsold_items, sort_all_items_client,\
    sort_all_items_stylist, sort_favorite, search_favorite, get_stylist_unsold_items, get_single_item, buy_item, \
    get_client_bought_items, get_sizes, get_client_single_bought_item, get_client_checkout_items, \
    get_stylist_checkout_items, change_seller_status, change_buyer_status, login_instagram, \
    get_seller_checkout_by_status, get_buyer_checkout_by_status, generate_braintree_client_token, create_braintree_subscription, user_location#, login_google

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    # login/registration system
    url(r'^api/v1/registration/$', registration),
    url(r'^api/v1/login/$', login),
    # url(r'^api/v1/login-facebook/$', login_facebook),
    url(r'^api/v1/login-instagram/$', login_instagram),
    # url(r'^api/v1/login-google/$', login_google),
    # add
    url(r'^api/v1/user/add-new-item/$', add_new_item),
    url(r'^api/v1/user/add-to-favorite/$', add_to_favorite),
    # get
    url(r'^api/v1/get-user-by-token/$', get_user_by_token),
    url(r'^api/v1/get-user-by-id/$', get_user_by_id),
    url(r'^api/v1/get-brands/$', get_brands),
    url(r'^api/v1/get-categories/$', get_categories),
    url(r'^api/v1/get-sizes/$', get_sizes),
    url(r'^api/v1/get-item-by-id/$', get_single_item),
    url(r'^api/v1/get-items-by-user-id/$', get_items_by_user_id),
    url(r'^api/v1/get-items-by-profile-type/$', get_items_by_profile_type),
    url(r'^api/v1/get-items-stylists-by-category/$', get_items_stylists_by_category),
    url(r'^api/v1/get-items-clients-by-category/$', get_items_clients_by_category),
    url(r'^api/v1/get-favorite-items/$', get_favorite_items),
    url(r'^api/v1/get-stylist-sold-items/$', get_stylist_sold_items),
    url(r'^api/v1/get-stylist-unsold-items/$', get_stylist_unsold_items),
    url(r'^api/v1/get-client-bought-items/$', get_client_bought_items),
    url(r'^api/v1/get-client-single-bought-item/$', get_client_single_bought_item),
    url(r'^api/v1/get-client-checkout-items/$', get_client_checkout_items),
    url(r'^api/v1/get-stylist-checkout-items/$', get_stylist_checkout_items),
    # edit
    url(r'^api/v1/user/change-avatar/$', change_avatar),
    url(r'^api/v1/user/change-name/$', change_name),
    url(r'^api/v1/user/change-item/$', change_item),
    # remove
    url(r'^api/v1/user/remove-item/$', remove_item),
    url(r'^api/v1/user/remove-item-from-favorite/$', remove_item_from_favorite),
    # users actions
    url(r'^api/v1/user/send-comment/$', send_comment),
    url(r'^api/v1/user/send-like/$', send_like),
    url(r'^api/v1/user/set_item_sold/$', set_item_sold),
    url(r'^api/v1/user/rate-stylist/$', rate_stylist),
    url(r'^api/v1/user/buy-item/$', buy_item),
    # follow
    url(r'^api/v1/user/follow/$', follow_user),
    url(r'^api/v1/user/unfollow/$', unfollow_user),
    # follow get
    url(r'^api/v1/user/get-followers/$', user_followers),
    url(r'^api/v1/user/get-followings/$', user_followings),
    # search
    url(r'^api/v1/search/search-sold-items/$', search_sold_items),  # SEARCH by KEYWORD in your SOLD items
    url(r'^api/v1/search/search-unsold-items/$', search_unsold_items),  # SEARCH by KEYWORD in your UNSOLD items
    url(r'^api/v1/search/search-all-items-stylist/$', search_all_items_stylist),  # SEARCH by KEYWORD in ALL items STYLIST
    url(r'^api/v1/search/search-all-items-client/$', search_all_items_client),  # SEARCH by KEYWORD in ALL items CLIENT
    url(r'^api/v1/search/search-favorite/$', search_favorite),  # Search favorite items
    # sort
    url(r'^api/v1/sort/sort-sold-items/$', sort_sold_items),  # SORT your SOLD items
    url(r'^api/v1/sort/sort-unsold-items/$', sort_unsold_items),  # SORT your UNSOLD items
    url(r'^api/v1/sort/sort-all-sold-items/$', sort_all_items_stylist),  # SORT ALL items STYLIST
    url(r'^api/v1/sort/sort-all-unsold-items/$', sort_all_items_client),  # SORT ALL items CLIENT
    url(r'^api/v1/sort/sort-favorite/$', sort_favorite),  # SORT favorite items
    # statuses
    url(r'^api/v1/status/seller-status/$', change_seller_status),
    url(r'^api/v1/status/buyer-status/$', change_buyer_status),
    # get_checkouts
    url(r'^api/v1/checkout/get-seller-checkout-by-status/$', get_seller_checkout_by_status),
    url(r'^api/v1/checkout/get-buyer-checkout-by-status/$', get_buyer_checkout_by_status),
    # braintree
    url(r'^api/v1/generate_braintree_client_token$', generate_braintree_client_token),
    url(r'^api/v1/create_braintree_subscription$', create_braintree_subscription),
    url(r'^api/v1/user_location$', user_location)
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)