from django.db import models
from django.contrib.auth.models import User

import os
import uuid


def store_avatar(instance, filename):
    """
    Rename file and store to the avatars folder
    """
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join("avatars/", filename)


def store_photo(instance, filename):
    """
    Rename file and store to the avatars folder
    """
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join("items/", filename)


class UserProfile(models.Model):
    # Custom User Fields
    # - profile type (stylist/client)
    # - user source (facebook, google, instagram, email)
    # - avatar (base64 text field for image)
    USER_SOURCE_CHOICES = (
        ('facebook', 'facebook'),
        ('google', 'google'),
        ('instagram', 'instagram'),
        ('email', 'email'),
    )
    PROFILE_TYPE_CHOICES = (
        ('stylist', 'stylist'),
        ('client', 'client'),
    )
    user = models.OneToOneField(User, related_name='user_info')
    profile_type = models.CharField(max_length=100, choices=PROFILE_TYPE_CHOICES)
    user_source = models.CharField(max_length=100, choices=USER_SOURCE_CHOICES)
    avatar = models.FileField(upload_to=store_avatar, blank=True)
    total_rate = models.IntegerField(default=0)
    count_people = models.IntegerField(default=0)
    facebook_id = models.IntegerField(default=0)
    instagram_id = models.IntegerField(default=0)
    google_id = models.IntegerField(default=0)

    def __unicode__(self):
        return self.user.username


class UserNotification(models.Model):
    # - notification (identifier for push notification)
    user = models.ForeignKey(User)
    notification_id = models.CharField(max_length=500)

    def __unicode__(self):
        return self.user.username


class StylistRating(models.Model):
    # Stylist rating fields
    # - client (who rate)
    # - stylist (whom rate)
    # - rating (mark from 1 to 5)
    client = models.ForeignKey(User, related_name='client')
    stylist = models.ForeignKey(User, related_name='stylist')
    rating = models.IntegerField()

    def __unicode__(self):
        return '%s rating %s for %s' % (self.client, self.stylist, self.rating)


class Category(models.Model):
    # - list of categories for items
    name = models.CharField(max_length=500)

    def __unicode__(self):
        return self.name


class Brand(models.Model):
    # - list of brands for items
    name = models.CharField(max_length=500)

    def __unicode__(self):
        return self.name


class Size(models.Model):
    """
    Model for item size
    """
    size = models.CharField(max_length=255)

    def __unicode__(self):
        return self.size


class Item(models.Model):
    # Item Fields
    # - Title (item name)
    # - category (jacket, shoes etc)
    # - brand (zara, nike, bershka)
    # - size (M, L, XL, XXL etc)
    # - description (product description)
    # - cost (price of the item)
    # - cost currency (dollar, euro etc)
    # - discount (amount of the discount)
    # - discount currency (dollar, euro etc)
    # - number of likes
    # - number of comments
    # - owner (creator of the item)
    title = models.CharField(max_length=500)
    category = models.ForeignKey(Category)
    brand = models.ForeignKey(Brand)
    description = models.CharField(max_length=500)
    cost = models.FloatField(default=0)
    cost_currency = models.CharField(max_length=100)
    discount = models.FloatField(default=0)
    discount_currency = models.CharField(max_length=100)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    sold = models.BooleanField(default=False)
    owner = models.ForeignKey(User)

    def __unicode__(self):
        return self.title


class ItemPhoto(models.Model):
    # Item photos
    # - item relation
    # - photo(base64)
    item = models.ForeignKey(Item, related_name='item_photo')
    photo = models.FileField(upload_to=store_photo)

    def __unicode__(self):
        return self.item.title


class ItemSize(models.Model):
    # Item sizes
    # - item relation
    # - size relation
    item = models.ForeignKey(Item, related_name="item_size")
    size = models.ForeignKey(Size)

    def __unicode__(self):
        return self.item.title


class Hashtag(models.Model):
    # Item hashtags
    # - item relation
    # - hashtag
    item = models.ForeignKey(Item, related_name="item_hashtag")
    hashtag = models.CharField(max_length=100)

    def __unicode__(self):
        return '%s for %s' % (self.hashtag, self.item.title)


class Like(models.Model):
    # Item likes
    # - item relation
    # - user relation
    item = models.ForeignKey(Item)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return '%s like %s' % (self.item.title, self.user.username)


class Comment(models.Model):
    # Item comments
    # - item relation
    # - user relation
    # - comment text
    # - datetime sending
    item = models.ForeignKey(Item, related_name="comments")
    user = models.ForeignKey(User)
    text = models.CharField(max_length=500)
    date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s like %s' % (self.item.title, self.user.username)


class Follow(models.Model):
    """
    Model for user followers/following.
    - Who
    - Whom
    """
    user_who_follow = models.ForeignKey(User, related_name="who_follow")
    user_whom_follow = models.ForeignKey(User, related_name="whom_follow")

    class Meta:
        unique_together = ('user_who_follow', 'user_whom_follow')

    def __unicode__(self):
        return u'%s follow %s' % (self.user_who_follow, self.user_whom_follow)


class Favorite(models.Model):
    """
    Model for user favourite items
    - user instance
    - item instance
    """
    user = models.ForeignKey(User)
    item = models.ForeignKey(Item)

    def __unicode__(self):
        return u'%s favourite %s' % (self.user.username, self.item.title)


class Order(models.Model):
    """
    Model for user orders
    - user
    - item
    - quantity
    - address
    - zip
    - phone
    """
    user = models.ForeignKey(User)
    item = models.ForeignKey(Item)
    quantity = models.IntegerField(default=1)
    address = models.CharField(max_length=255)
    zip = models.CharField(max_length=255)
    size = models.ForeignKey(ItemSize)
    phone = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s buy %s on %s' % (self.user.username, self.item.title, self.date)


class Checkout(models.Model):
    """
    Model for user checkout
    - seller
    - buyer
    - order
    - seller_status
    - buyer_status
    """
    seller = models.ForeignKey(User, related_name="seller")
    buyer = models.ForeignKey(User, related_name="buyer")
    order = models.ForeignKey(Order)
    payment_status = models.BooleanField(default=False)
    seller_status = models.BooleanField(default=False)
    buyer_status = models.BooleanField(default=False)
