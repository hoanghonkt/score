from django.contrib.auth.models import User

from rest_framework import serializers

from app.models import UserProfile, Brand, Category, Item, ItemPhoto, Favorite, Hashtag, Comment, Size, Order, \
    ItemSize, Checkout, Like, UserLocation


class UserProfileSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField('get_user_rating')

    def get_user_rating(self, obj):
        try:
            rating = obj.total_rate / obj.count_people
            return int(rating)
        except:
            return 0

    class Meta:
        model = UserProfile
        fields = ('profile_type', 'user_source', 'avatar', 'rating')


class UserSerializer(serializers.ModelSerializer):
    user_info = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'user_info')

class UserLocationSerializer(serializers.ModelSerializer):
  user = UserSerializer(read_only=True)
  class Meta:
    model = UserLocation
    fields = ('id', 'user', 'latitude', 'longitude', 'created_at', 'updated_at')


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ('id', 'name')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class ItemPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPhoto
        fields = ('id', 'photo')


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ('id', 'hashtag')


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'user', 'text', 'date')


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ('id', 'size')


class ItemSerializer(serializers.ModelSerializer):
    item_photo = ItemPhotoSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    owner = UserSerializer(read_only=True)
    item_hashtag = HashtagSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    size = serializers.SerializerMethodField('get_item_sizes')
    like = serializers.SerializerMethodField('check_like')

    def check_like(self, obj):
        user_id = self.context.get("user_id")
        user_has_like = False
        if Like.objects.filter(user_id=user_id, item=obj).exists():
            user_has_like = True
        return user_has_like

    def get_item_sizes(self, obj):
        try:
            item_sizes = ItemSize.objects.filter(item=obj).values_list('size_id', flat=True)
            sizes = Size.objects.filter(pk__in=item_sizes).values_list('size', flat=True)
            size = []
            for item in range(len(item_sizes)):
                dict = {}
                dict['id'] = item_sizes[item]
                dict['size'] = sizes[item]
                size.append(dict)
            return size
        except:
            return None

    class Meta:
        model = Item
        fields = ('id', 'title', 'category', 'brand', 'size', 'description',
                  'cost', 'cost_currency', 'discount', 'discount_currency',
                  'likes_count', 'like', 'comments_count', 'owner', 'item_photo',
                  'item_hashtag', 'sold', 'comments')


class FavoriteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    item = ItemSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'user', 'item')


class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    item = ItemSerializer(read_only=True)
    size = SizeSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'item', 'quantity', 'address', 'zip', 'phone', 'date', 'size')


class CheckoutSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    buyer = UserSerializer(read_only=True)
    order = OrderSerializer(read_only=True)

    class Meta:
        model = Checkout
        fields = ('id', 'buyer', 'seller', 'order', 'payment_status', 'seller_status', 'buyer_status')
