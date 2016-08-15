from django.contrib import admin

from app.models import UserNotification, UserProfile, Brand, Category, Item, ItemPhoto, Follow, Hashtag, Comment, \
    Favorite, Order, Size, ItemSize, StylistRating, Checkout

admin.site.register(UserNotification)
admin.site.register(UserProfile)
admin.site.register(Brand)
admin.site.register(Category)
admin.site.register(Item)
admin.site.register(ItemPhoto)
admin.site.register(Follow)
admin.site.register(Hashtag)
admin.site.register(Comment)
admin.site.register(Favorite)
admin.site.register(Size)
admin.site.register(Order)
admin.site.register(ItemSize)
admin.site.register(StylistRating)
admin.site.register(Checkout)
