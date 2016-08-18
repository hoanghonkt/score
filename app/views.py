from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.db.models import Q
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from app.models import UserProfile, UserNotification, Brand, Category, Item, ItemPhoto, Follow, Hashtag, \
    Comment, Like, StylistRating, Favorite, Order, Size, ItemSize, Checkout
from app.serializers import UserSerializer, BrandSerializer, CategorySerializer, ItemSerializer, FavoriteSerializer, \
    OrderSerializer, SizeSerializer, CheckoutSerializer

from base64 import b64decode
# import facebook
import requests
import json
import urllib2

import braintree

braintree.Configuration.configure(braintree.Environment.Sandbox,
  merchant_id="454g5vrdsh3wv7sf",
  public_key="9d4szd6cxkspp923",
  private_key="8e985d7cd53b5b34ae908f5f23e8458b")

TRANSACTION_SUCCESS_STATUSES = [
    braintree.Transaction.Status.Authorized,
    braintree.Transaction.Status.Authorizing,
    braintree.Transaction.Status.Settled,
    braintree.Transaction.Status.SettlementConfirmed,
    braintree.Transaction.Status.SettlementPending,
    braintree.Transaction.Status.Settling,
    braintree.Transaction.Status.SubmittedForSettlement
]


@api_view(['POST'])
def login(request):
    """
    User login via email.
    Example json:
    {
        "email": "antonboksha@gmail.com",
        "password": "qwerty",
        "notification_id": "id goes here"
    }
    """
    if request.method == 'POST':
        if User.objects.filter(email=request.data['email']).exists():
            user = get_object_or_404(User, email=request.data['email'])
            if user.check_password(request.data['password']):
                if UserNotification.objects.filter(user_id=user.id,
                                                   notification_id=request.data['notification_id']).exists():
                    serializer = UserSerializer(user)
                    token = get_object_or_404(Token, user_id=user.id)
                    return Response({'token': token.key, 'user': serializer.data})
                else:
                    UserNotification.objects.create(user_id=user.id, notification_id=request.data['notification_id'])
                    serializer = UserSerializer(user)
                    token = get_object_or_404(Token, user_id=user.id)
                    return Response({'token': token.key, 'user': serializer.data})
            else:
                return Response({'status': 'Incorrect password!'})

        else:
            return Response({'status': 'User does not exist!'})


@api_view(['POST'])
def registration(request):
    """
    User registration via email/facebook/google plus/instagram.
    Generating token and create new user.
    Example json:
    {
        "first_name":"Anton",
        "last_name":"Boksha",
        "email":"antonboksha@gmail.com",
        "password":"qwerty",
        "avatar":"base64 goes here",
        "profile_type": "stylist",
        "user_source": "facebook",
        "notification_id": "id goes here"
    }
    """
    if request.method == 'POST':
        if User.objects.filter(username=request.data['email']).exists():
            return Response({'status': 'User with this email already exist!'})
        else:
            if len(request.data['password']) < 6:
                return Response({'status': 'Your password should contain no less than 6 characters!'})
            else:
                # creating new user
                new_user = User.objects.create_user(username=request.data['email'],
                                                    password=request.data['password'],
                                                    email=request.data['email'],
                                                    first_name=request.data['first_name'],
                                                    last_name=request.data['last_name'])
                # create custom fields for new user
                info = UserProfile.objects.create(user_id=new_user.id,
                                                  avatar='/media/avatars/default.png',
                                                  profile_type=request.data['profile_type'],
                                                  user_source=request.data['user_source'])
                if request.data['avatar']:
                    image_data = b64decode(request.data['avatar'])
                    info.avatar = ContentFile(image_data, 'whatup.png')
                    info.save()
                # create custom notification_id for new user
                UserNotification.objects.create(user_id=new_user.id,
                                                notification_id=request.data['notification_id'])
                # create API token for new user
                token = Token.objects.create(user=new_user)
                # serialize user instance
                serializer = UserSerializer(new_user)
                return Response({'token': token.key, 'user': serializer.data})


@api_view(['POST'])
def get_user_by_id(request):
    """
    Get user instance by id.
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "user_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            if User.objects.filter(pk=request.data['user_id']).exists():
                user = get_object_or_404(User, pk=request.data['user_id'])
                serializer = UserSerializer(user)
                return Response(serializer.data)
            else:
                return Response({'status': 'User with this id does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def change_avatar(request):
    """
    Change user avatar:
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "avatar": "base64 goes here"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
                token = get_object_or_404(Token, key=request.data['token'])
                user = get_object_or_404(UserProfile, user_id=token.user_id)
                image_data = b64decode(request.data['avatar'])
                user.avatar = ContentFile(image_data, 'whatup.png')
                user.save()
                return Response({'status': 'Avatar successfully changed!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def change_name(request):
    """
    Change user first and last names:
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "first_name": "John",
        "last_lane": "Smith"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
                token = get_object_or_404(Token, key=request.data['token'])
                user = get_object_or_404(User, pk=token.user_id)
                user.first_name = request.data['first_name']
                user.last_name = request.data['last_name']
                user.save()
                return Response({'status': 'First and last name successfully changed!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_brands(request):
    """
    Get all brands
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            brands = Brand.objects.all()
            serializer = BrandSerializer(brands, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_categories(request):
    """
    Get all categories
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            categories = Category.objects.all()
            serializer = CategorySerializer(categories, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_sizes(request):
    """
    Get all sizes
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            sizes = Size.objects.all()
            serializer = SizeSerializer(sizes, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_user_by_token(request):
    """
    Get user by token
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            user = get_object_or_404(User, pk=token.user_id)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def add_new_item(request):
    """
    Get user by token
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "title": "Aweasome t-shirt",
        "category": 1,
        "brand": 1,
        "size": [],
        "description": "The best t-shirt ever!",
        "cost": "99.90",
        "cost_currency": "dollar",
        "discount": "13.90",
        "discount_currency": "euro",
        "item_photo":[],
        "hashtags":[]
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            item = Item.objects.create(title=request.data['title'],
                                       category_id=request.data['category'],
                                       brand_id=request.data['brand'],
                                       description=request.data['description'],
                                       cost=request.data['cost'],
                                       cost_currency=request.data['cost_currency'],
                                       discount=request.data['discount'],
                                       discount_currency=request.data['discount_currency'],
                                       owner_id=token.user_id)
            for size in request.data['size']:
                ItemSize.objects.create(item=item, size_id=size)
            for photo in request.data['item_photo']:
                image_data = b64decode(photo)
                ItemPhoto.objects.create(item=item, photo=ContentFile(image_data, 'whatup.png'))
            for hashtag in request.data['hashtags']:
                Hashtag.objects.create(item=item, hashtag=hashtag)
            return Response({'status': 'Successfully add new item!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_items_by_user_id(request):
    """
    Get user by token
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "user_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            if User.objects.filter(pk=request.data['user_id']).exists():
                items = Item.objects.filter(owner_id=request.data['user_id'])
                serializer = ItemSerializer(items, many=True)
                return Response(serializer.data)
            else:
                return Response({'status': 'User does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def follow_user(request):
    """
    View for following users. User A follow user B.
    Example json:
    {
        "token": "ad75f6fa7fa276aab61ae3e3d27cb22eda2b7afd",
        "user_id": 2
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            if User.objects.filter(pk=request.data['user_id']).exists():
                whom_user = get_object_or_404(User, pk=request.data['user_id'])
                if whom_user.id == token.user_id:
                    return Response({'status': 'You can not follow yourself!'})
                else:
                    try:
                        Follow.objects.create(user_who_follow_id=token.user_id,
                                              user_whom_follow_id=request.data['user_id'])
                        return Response({'status': 'Successfully following!'})
                    except IntegrityError:
                        return Response({'status': 'You already follow this user!'})
            else:
                return Response({'status': 'User does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def unfollow_user(request):
    """
    View for unfollowing users. User A unfollow user B.
    Example json:
    {
        "token": "ad75f6fa7fa276aab61ae3e3d27cb22eda2b7afd",
        "user_id": 2
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            if User.objects.filter(pk=request.data['user_id']).exists():
                whom_user = get_object_or_404(User, pk=request.data['user_id'])
                if whom_user.id == token.user_id:
                    return Response({'status': 'You can not unfollow yourself!'})
                else:
                    try:
                        relationship = Follow.objects.get(user_who_follow_id=token.user_id,
                                                          user_whom_follow_id=request.data['user_id'])
                        relationship.delete()
                        return Response({'status': 'Successfully unfollow this user.'})
                    except Follow.DoesNotExist:
                        return Response({'status': 'You do not follow this user!'})
            else:
                return Response({'status': 'User does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def user_followers(request):
    """
    View for getting user followers.
    Example json:
    {
        "token": "ad75f6fa7fa276aab61ae3e3d27cb22eda2b7afd"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            followers = Follow.objects.filter(user_whom_follow_id=token.user_id).\
                values_list('user_who_follow_id', flat=True)
            users = User.objects.filter(pk__in=followers)
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def user_followings(request):
    """
    View for getting user followings.
    Example json:
    {
        "token": "ad75f6fa7fa276aab61ae3e3d27cb22eda2b7afd"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            followings = Follow.objects.filter(user_who_follow_id=token.user_id).\
                values_list('user_whom_follow_id', flat=True)
            users = User.objects.filter(pk__in=followings)
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def send_comment(request):
    """
    View for sending comment to item
    Example json:
    {
        "token": "ad75f6fa7fa276aab61ae3e3d27cb22eda2b7afd",
        "item_id": 1,
        "text": "aweasome!"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            if Item.objects.filter(pk=request.data['item_id']).exists():
                token = get_object_or_404(Token, key=request.data['token'])
                item = get_object_or_404(Item, pk=request.data['item_id'])
                item.comments_count += 1
                item.save()
                Comment.objects.create(item=item,
                                       user_id=token.user_id,
                                       text=request.data['text'])
                return Response({'status': 'Comment successfully send!'})
            else:
                return Response({'status': 'Item does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def send_like(request):
    """
    View for sending like to item
    Example json:
    {
        "token": "ad75f6fa7fa276aab61ae3e3d27cb22eda2b7afd",
        "item_id": 1,
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            if Item.objects.filter(pk=request.data['item_id']).exists():
                token = get_object_or_404(Token, key=request.data['token'])
                if Like.objects.filter(item=request.data['item_id'], user=token.user_id).exists():
                    return Response({'status': 'You already like this item!'})
                else:
                    item = get_object_or_404(Item, pk=request.data['item_id'])
                    item.likes_count += 1
                    item.save()
                    return Response({'status': 'Like successfully send!'})
            else:
                return Response({'status': 'Item does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def rate_stylist(request):
    """
    View for getting user followings.
    Example json:
    {
        "token": "ad75f6fa7fa276aab61ae3e3d27cb22eda2b7afd",
        "user_id": 1,
        "rating": 3
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            if User.objects.filter(pk=request.data['user_id']).exists():
                token = get_object_or_404(Token, key=request.data['token'])
                if StylistRating.objects.filter(client_id=token.user_id,
                                                stylist_id=request.data['user_id']).exists():
                    return Response({'status': 'You already rate this stylist!'})
                else:
                    StylistRating.objects.create(client_id=token.user_id,
                                                 stylist_id=request.data['user_id'],
                                                 rating=request.data['rating'])
                    user_profile = get_object_or_404(UserProfile, user_id=token.user_id)
                    user_profile.total_rate += request.data["rating"]
                    user_profile.count_people += 1
                    user_profile.save()
                    return Response({'status': 'Rate successfully send!'})
            else:
                return Response({'status': 'Stylist does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def add_to_favorite(request):
    """
    View for add item to favorite.
    Example json:
    {
        "token": "ad75f6fa7fa276aab61ae3e3d27cb22eda2b7afd",
        "item_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            if Item.objects.filter(pk=request.data['item_id']).exists():
                token = get_object_or_404(Token, key=request.data['token'])
                if Favorite.objects.filter(user_id=token.user_id,
                                           item_id=request.data['item_id']).exists():
                    return Response({'status': 'You already have this item in favorites!'})
                else:
                    Favorite.objects.create(user_id=token.user_id,
                                            item_id=request.data['item_id'])
                    return Response({'status': 'Successfully add item to your favourite list!'})
            else:
                return Response({'status': 'Item does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_favorite_items(request):
    """
    View for getting all user favorite items.
    Example json:
    {
        "token": "ad75f6fa7fa276aab61ae3e3d27cb22eda2b7afd"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            favorites = Favorite.objects.filter(user_id=token.user_id)
            print favorites
            serializer = FavoriteSerializer(favorites, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_items_by_profile_type(request):
    """
    Get user by token
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            user_profile = get_object_or_404(UserProfile, user_id=token.user_id)
            items = Item.objects.filter(owner__user_info__profile_type=user_profile.profile_type)
            serializer = ItemSerializer(items, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_items_clients_by_category(request):
    """
    Get user by token
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "category_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            items = Item.objects.filter(owner__user_info__profile_type='client').\
                filter(category_id=request.data['category_id'])
            serializer = ItemSerializer(items, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_items_stylists_by_category(request):
    """
    Get user by token
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "category_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            items = Item.objects.filter(owner__user_info__profile_type='stylist').\
                filter(category_id=request.data['category_id']).filter(sold=False)
            serializer = ItemSerializer(items, context={'user_id': token.user_id}, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_stylist_sold_items(request):
    """
    Get all sold stylist items
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            items = Item.objects.filter(owner_id=token.user_id).filter(sold=True)
            serializer = ItemSerializer(items, context={'user_id': token.user_id}, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_stylist_unsold_items(request):
    """
    Get all unsold stylist items
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            items = Item.objects.filter(owner_id=token.user_id).filter(sold=False)
            serializer = ItemSerializer(items, context={'user_id': token.user_id}, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def set_item_sold(request):
    """
    Mark item as "sold"
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "item_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            if Item.objects.filter(pk=request.data['item_id']).exists():
                token = get_object_or_404(Token, key=request.data['token'])
                item = get_object_or_404(Item, pk=request.data['item_id'])
                if item.owner_id == token.user_id:
                    if item.sold:
                        return Response({'status': 'Item is already sold!'})
                    else:
                        item.sold = True
                        item.save()
                        return Response({'status': 'Item successfully sold!'})
                else:
                    return Response({'status': 'This is not your item!'})
            else:
                return Response({'status': 'Item does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def change_item(request):
    """
    Edit already exist item.
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "item_id": 1,
        "title": "Aweasome t-shirt",
        "category": 1,
        "brand": 1,
        "size": [],
        "description": "The best t-shirt ever!",
        "cost": "99.90",
        "cost_currency": "dollar",
        "discount": "13.90",
        "discount_currency": "euro",
        "item_photo":[],
        "hashtags":[]
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            if Item.objects.filter(pk=request.data['item_id']).exists():
                item = get_object_or_404(Item, pk=request.data['item_id'])
                item.title = request.data['title']
                item.category_id = request.data['category']
                item.brand_id = request.data['brand']
                item.description = request.data['description']
                item.cost = request.data['cost']
                item.cost_currency = request.data['cost_currency']
                item.discount = request.data['discount']
                item.discount_currency = request.data['discount_currency']
                item.save()
                for size in request.data['size']:
                    ItemSize.objects.filter(item=item).delete()
                    ItemSize.objects.create(item=item, size_id=size)
                for photo in request.data['item_photo']:
                    ItemPhoto.objects.filter(item=item).delete()
                    image_data = b64decode(photo)
                    ItemPhoto.objects.create(item=item, photo=ContentFile(image_data, 'whatup.png'))
                for hashtag in request.data['hashtags']:
                    Hashtag.objects.filter(item=item).delete()
                    Hashtag.objects.create(item=item, hashtag=hashtag)
                return Response({'status': 'Successfully edit item!'})
            else:
                return Response({'status': 'Item does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def remove_item(request):
    """
    Delete item / item comments / item photos / item likes
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "item_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            if Item.objects.filter(pk=request.data['item_id']).exists():
                item = get_object_or_404(Item, pk=request.data['item_id'])
                item.delete()
                ItemPhoto.objects.filter(item=item).delete()
                Hashtag.objects.filter(item=item).delete()
                Comment.objects.filter(item=item).delete()
                return Response({'status': 'Item successfully removed!'})
            else:
                return Response({'status': 'Item does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def remove_item_from_favorite(request):
    """
    Delete item from user favorite
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "item_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            if Item.objects.filter(pk=request.data['item_id']).exists():
                item = get_object_or_404(Item, pk=request.data['item_id'])
                if Favorite.objects.filter(item=item).exists():
                    get_object_or_404(Favorite, item=item).delete()
                    return Response({'status': 'Item successfully removed!'})
                else:
                    return Response({'status': 'This item not in your favorites!'})
            else:
                return Response({'status': 'Item does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def search_sold_items(request):
    """
    Search sold items by keyword and category
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "keyword": "jacket"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            items = Item.objects.filter(owner_id=token.user_id).\
                filter(sold=True).\
                filter(Q(title__icontains=request.data['keyword']) |
                       Q(brand__name__icontains=request.data['keyword']) |
                       Q(category__name__icontains=request.data['keyword']) |
                       # Q(size__icontains=request.data['keyword']) |
                       Q(description__icontains=request.data['keyword']))
            serializer = ItemSerializer(items, context={'user_id': token.user_id}, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def search_unsold_items(request):
    """
    Search unsold items by keyword and category
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "keyword": "jacket"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            items = Item.objects.filter(owner_id=token.user_id).\
                filter(sold=False).\
                filter(Q(title__icontains=request.data['keyword']) |
                       Q(brand__name__icontains=request.data['keyword']) |
                       Q(category__name__icontains=request.data['keyword']) |
                       # Q(size__icontains=request.data['keyword']) |
                       Q(description__icontains=request.data['keyword']))
            serializer = ItemSerializer(items, context={'user_id': token.user_id}, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def search_all_items_stylist(request):
    """
    Search ALL sold items by keyword and category
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "keyword": "jacket"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            items = Item.objects.filter(owner__user_info__profile_type='stylist').\
                filter(Q(title__icontains=request.data['keyword']) |
                       Q(brand__name__icontains=request.data['keyword']) |
                       Q(category__name__icontains=request.data['keyword']) |
                       # Q(size__icontains=request.data['keyword']) |
                       Q(description__icontains=request.data['keyword']))
            serializer = ItemSerializer(items, context={'user_id': token.user_id}, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def search_all_items_client(request):
    """
    Search ALL unsold items by keyword and category
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "keyword": "jacket"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            items = Item.objects.filter(owner__user_info__profile_type='client').\
                filter(Q(title__icontains=request.data['keyword']) |
                       Q(brand__name__icontains=request.data['keyword']) |
                       Q(category__name__icontains=request.data['keyword']) |
                       # Q(size__icontains=request.data['keyword']) |
                       Q(description__icontains=request.data['keyword']))
            serializer = ItemSerializer(items, context={'user_id': token.user_id}, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def sort_sold_items(request):
    """
    Sort sold items by category
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "category_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            items = Item.objects.filter(owner_id=token.user_id).\
                filter(sold=True).\
                filter(category_id=request.data['category_id'])
            serializer = ItemSerializer(items, context={'user_id': token.user_id}, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def sort_unsold_items(request):
    """
    Sort unsold items by category
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "category_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            items = Item.objects.filter(owner_id=token.user_id).\
                filter(sold=False).\
                filter(category_id=request.data['category_id'])
            serializer = ItemSerializer(items, context={'user_id': token.user_id}, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def sort_all_items_client(request):
    """
    Sort all client items by category
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "category_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            items = Item.objects.filter(owner__user_info__profile_type='client').\
                filter(category_id=request.data['category_id'])
            serializer = ItemSerializer(items, context={'user_id': token.user_id}, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def sort_all_items_stylist(request):
    """
    Sort all stylist items by category
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "category_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            items = Item.objects.filter(owner__user_info__profile_type='stylist').\
                filter(category_id=request.data['category_id'])
            serializer = ItemSerializer(items, context={'user_id': token.user_id}, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def sort_favorite(request):
    """
    Sort all favorite items by category
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "category_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            items = Favorite.objects.filter(user_id=token.user_id).filter(item__category=request.data['category_id'])
            serializer = FavoriteSerializer(items, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def search_favorite(request):
    """
    Search all favorite items by keyword
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "keyword": "jacket"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            items = Favorite.objects.filter(user_id=token.user_id).\
                filter(Q(item__title__icontains=request.data['keyword']) |
                       Q(item__brand__name__icontains=request.data['keyword']) |
                       Q(item__category__name__icontains=request.data['keyword']) |
                       Q(item__size__icontains=request.data['keyword']) |
                       Q(item__description__icontains=request.data['keyword']))
            serializer = FavoriteSerializer(items, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_single_item(request):
    """
    Get single item by item_id
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "item_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            if Item.objects.filter(pk=request.data['item_id']).exists():
                item = get_object_or_404(Item, pk=request.data['item_id'])
                serializer = ItemSerializer(item, context={'user_id': token.user_id},)
                return Response(serializer.data)
            else:
                return Response({'status': 'Item does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def buy_item(request):
    """
    User buy item.
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "item_id": 1,
        "quantity": 1,
        "address": "USA, NY, 5 Green St. 123",
        "zip": "11001",
        "phone": "305 567 8901",
        "size": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            if Item.objects.filter(pk=request.data['item_id']).exists():
                token = get_object_or_404(Token, key=request.data['token'])
                item = get_object_or_404(Item, pk=request.data['item_id'])
                # item.sold = True
                # item.save()
                order = Order.objects.create(user_id=token.user_id,
                                             item=item,
                                             quantity=request.data['quantity'],
                                             address=request.data['address'],
                                             zip=request.data['zip'],
                                             size_id=request.data["size"],
                                             phone=request.data['phone'])
                Checkout.objects.create(seller_id=item.owner_id,
                                        buyer_id=token.user_id,
                                        order=order)
                return Response({'status': 'Item successfully bought'})
            else:
                return Response({'status': 'Item does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_client_bought_items(request):
    """
    Return list of all bought client items
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            items = Order.objects.filter(user_id=token.user_id)
            serializer = OrderSerializer(items, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_client_single_bought_item(request):
    """
    Return single bought client item
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "item_id": 1
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            if Order.objects.filter(user_id=token.user_id).filter(item_id=request.data['item_id']).exists():
                order = Order.objects.get(user_id=token.user_id, item_id=request.data['item_id'])
                if order.user_id != token.user_id:
                    return Response({'status': 'This is not your order!'})
                else:
                    serializer = OrderSerializer(order)
                    return Response(serializer.data)
            else:
                return Response({'status': 'Order does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_client_checkout_items(request):
    """
    Return client checkouts
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            checkouts = Checkout.objects.filter(buyer_id=token.user_id)
            serializer = CheckoutSerializer(checkouts, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_stylist_checkout_items(request):
    """
    Return client checkouts
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e"
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data['token'])
            checkouts = Checkout.objects.filter(seller_id=token.user_id)
            serializer = CheckoutSerializer(checkouts, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def change_buyer_status(request):
    """
    Return client checkouts
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "checkout_id": 1,
        "status": True
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            if Checkout.objects.filter(pk=request.data["checkout_id"]).exists():
                checkout = get_object_or_404(Checkout, pk=request.data["checkout_id"])
                checkout.buyer_status = request.data["status"]
                checkout.save()
                serializer = CheckoutSerializer(checkout)
                return Response(serializer.data)
            else:
                return Response({'status': 'Checkout does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def change_seller_status(request):
    """
    Return client checkouts
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "checkout_id": 1,
        "status": True
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            if Checkout.objects.filter(pk=request.data["checkout_id"]).exists():
                checkout = get_object_or_404(Checkout, pk=request.data["checkout_id"])
                checkout.seller_status = request.data["status"]
                checkout.save()
                serializer = CheckoutSerializer(checkout)
                return Response(serializer.data)
            else:
                return Response({'status': 'Checkout does not exist!'})
        else:
            return Response({'status': 'Token does not exist!'})


# @api_view(['POST'])
# def login_facebook(request):
#     """
#     Login user via facebook
#     Example json:
#     {
#         "access_token": "CAAX1APE2yaEBAB6ZADh1lcbPVbk9HZCgAIrjv8JDxVdyK01Iki4alcg7LrY"
#     }
#     """
#     if request.method == "POST":
#         if "access_token" in request.data and request.data["access_token"] != "" and \
#                         request.data["access_token"] is not None:
#             graph = facebook.GraphAPI(access_token=request.data["access_token"], timeout=60)
#             facebook_user = graph.get_object("me", fields='id, name, email, first_name, last_name, picture.type(large),'
#                                                           ' bio, birthday, gender, hometown, about')
#             if UserProfile.objects.filter(facebook_id=facebook_user["id"]).exists():
#                 user_profile = get_object_or_404(UserProfile, facebook_id=facebook_user["id"])
#                 user = get_object_or_404(User, pk=user_profile.user_id)
#                 token = get_object_or_404(Token, user_id=user.id)
#                 serializer = UserSerializer(user, context={'user_id': token.user_id})
#                 return Response({"status": "Successfully login user via facebook!",
#                                  "token": token.key,
#                                  "user": serializer.data})
#             else:
#                 if facebook_user["first_name"] and facebook_user["last_name"]:
#                     username = facebook_user["first_name"].lower() + facebook_user["last_name"].lower()
#                 else:
#                     username = facebook_user["id"]
#                 user = User.objects.create(username=username,
#                                            first_name=facebook_user["first_name"],
#                                            last_name=facebook_user["last_name"],
#                                            email=facebook_user["email"]
#                                            )
#                 user.set_password(username + facebook_user["id"] + facebook_user["email"])
#                 user.save()
#                 token = Token.objects.create(user=user)
#                 user_profile = UserProfile.objects.create(user=user,
#                                                           user_source="facebook",
#                                                           facebook_id=facebook_user["id"],
#                                                           profile_type="client")
#                 url = "http://graph.facebook.com/" + str(facebook_user["id"]) + "/picture?type=large"
#                 r = requests.get(url)
#                 img_temp = NamedTemporaryFile(delete=True)
#                 img_temp.write(r.content)
#                 img_temp.flush()
#                 user_profile.avatar.save("image.jpg", File(img_temp), save=True)
#                 serializer = UserSerializer(user, context={'user_id': token.user_id})
#                 return Response({"status": "Successfully login via facebook!",
#                                  "token": token.key,
#                                  "user": serializer.data})


@api_view(['POST'])
def login_instagram(request):
    """
    Login user via instagram
    Example json:
    {
        "access_token": "CAAX1APE2yaEBAB6ZADh1lcbPVbk9HZCgAIrjv8JDxVdyK01Iki4alcg7LrY"
    }
    """
    if "access_token" in request.data and request.data["access_token"] != "" and \
                    request.data["access_token"] is not None:
        url = 'https://api.instagram.com/v1/users/self/?access_token=%s' % request.data["access_token"]
        obj = json.loads(urllib2.urlopen(url).read().decode('utf8'))
        print obj
        print obj["data"]["username"]
        if UserProfile.objects.filter(instagram_id=obj["data"]["id"]).exists():
            user_profile = get_object_or_404(UserProfile, instagram_id=obj["data"]["id"])
            user = get_object_or_404(User, pk=user_profile.user_id)
            token = get_object_or_404(Token, user_id=user.id)
            serializer = UserSerializer(user, context={'user_id': token.user_id})
            return Response({"status": "Successfully login user via instagram!",
                             "token": token.key,
                             "user": serializer.data})
        else:
            user = User.objects.create(username=obj["data"]["username"],
                                       email="")
            user.set_password(obj["data"]["username"]+obj["data"]["id"])
            user.save()
            token = Token.objects.create(user=user)
            user_profile = UserProfile.objects.create(user=user,
                                                      user_source="instagram",
                                                      instagram_id=obj["data"]["id"],
                                                      profile_type="client")
            r = requests.get(obj["data"]["profile_picture"])
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(r.content)
            img_temp.flush()
            user_profile.avatar.save("image.jpg", File(img_temp), save=True)
            serializer = UserSerializer(user, context={'user_id': token.user_id})
            return Response({"status": "Successfully login via instagram!",
                             "token": token.key,
                             "user": serializer.data})


@api_view(['POST'])
def get_seller_checkout_by_status(request):
    """
    Get User Checkouts by status(true/false)
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "status": True
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data["token"])
            checkouts = Checkout.objects.filter(seller_id=token.user_id,
                                                buyer_status=False,
                                                seller_status=request.data["status"])
            serializer = CheckoutSerializer(checkouts, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})


@api_view(['POST'])
def get_buyer_checkout_by_status(request):
    """
    Get User Checkouts by status(true/false)
    Example json:
    {
        "token": "b614ef53cbc01721a759d5bf69ca02b95bf8403e",
        "status": True
    }
    """
    if request.method == 'POST':
        if Token.objects.filter(key=request.data['token']).exists():
            token = get_object_or_404(Token, key=request.data["token"])
            checkouts = Checkout.objects.filter(buyer_id=token.user_id,
                                                buyer_status=request.data["status"],
                                                seller_status=True)
            serializer = CheckoutSerializer(checkouts, many=True)
            return Response(serializer.data)
        else:
            return Response({'status': 'Token does not exist!'})

@api_view(['POST'])
def generate_braintree_client_token(request):
  """
  Get braintree client token
  """
  if request.method == 'POST':
    if Token.objects.filter(key=request.data['token']).exists():
      return Response({'client_token': braintree.ClientToken.generate()})
    else:
      return Response({'status': 'Token does not exist!'})


@api_view(["POST"])
def create_braintree_subscription(request):
  """
  Create braintree transaction

  Example
  {
    "token": "4296e2830490845bdd8d44d47754bf1424f8c3c5",
    "payment_method_token": "fake-valid-nonce",
    "product_ids": "8,9,10",
    "quantity": "1,2,3"
  }

  """
  if request.method == 'POST':
    if Token.objects.filter(key=request.data['token']).exists():
      nonce_from_the_client = request.data["payment_method_token"]
      item_ids = request.data["product_ids"].split(',')
      item_qts = request.data["quantity"].split(',')

      # Use payment method nonce here...
      amount = 0
      for i in range(len(item_ids)):
        item = get_object_or_404(Item, pk=item_ids[i])
        amount += item.cost*int(item_qts[i])

      result = braintree.Transaction.sale({
        "amount": str(amount),
        "payment_method_nonce": nonce_from_the_client,
        "options": {
          "submit_for_settlement": True
        }
      })

      return Response({"status": 'successful'})
    else:
      return Response({'status': 'Token does not exist!'})


# @api_view(['POST'])
# def login_google(request):
#     """
#     Login user via google
#     Example json:
#     {
#         "google_user_id": 1231274833483
#     }
#     """
#     if "google_user_id" in request.data and request.data["google_user_id"] != "" and \
#                     request.data["google_user_id"] is not None:
#         url = 'https://www.googleapis.com/plus/v1/people/%s?key=AIzaSyAn2utl7FnEvXkSOkW16lwh_Qb1hEea1HM' % str(request.data["google_user_id"])
#         obj = json.loads(urllib2.urlopen(url).read().decode('utf8'))
#         print obj
#         print obj["id"]
#         if UserProfile.objects.filter(google_id=obj["data"]["id"]).exists():
#             user_profile = get_object_or_404(UserProfile, google_id=obj["id"])
#             user = get_object_or_404(User, pk=user_profile.user_id)
#             token = get_object_or_404(Token, user_id=user.id)
#             serializer = UserSerializer(user, context={'user_id': token.user_id})
#             return Response({"status": "Successfully login user via google!",
#                              "token": token.key,
#                              "user": serializer.data})
#         else:
#             user = User.objects.create(username=obj["name"]["givenName"].lower() + obj["name"]["familyName"].lower()),
#                                        email="")
        #     user.set_password(obj["data"]["username"]+obj["data"]["id"])
        #     user.save()
        #     token = Token.objects.create(user=user)
        #     user_profile = UserProfile.objects.create(user=user,
        #                                               user_source="instagram",
        #                                               instagram_id=obj["data"]["id"],
        #                                               profile_type="client")
        #     r = requests.get(obj["data"]["profile_picture"])
        #     img_temp = NamedTemporaryFile(delete=True)
        #     img_temp.write(r.content)
        #     img_temp.flush()
        #     user_profile.avatar.save("image.jpg", File(img_temp), save=True)
        #     serializer = UserSerializer(user, context={'user_id': token.user_id})
        #     return Response({"status": "Successfully login via instagram!",
        #                      "token": token.key,
        #                      "user": serializer.data})