from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Like, Comment, Collection, CollectionItem, Follow

User = get_user_model()


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'article', 'created_at']
        read_only_fields = ['id', 'created_at']


class CollectionItemSerializer(serializers.ModelSerializer):
    article = serializers.SerializerMethodField()

    class Meta:
        model = CollectionItem
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def get_article(self, obj):
        return obj.article.get_absolute_url()


class CollectionSerializer(serializers.ModelSerializer):
    items = CollectionItemSerializer(many=True)
    collection_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = Collection
        exclude = ['user', 'id']
        read_only_fields = ['collection_id', 'created_at', 'items']


class CommentArticleSerializer(serializers.ModelSerializer):
    comment_id = serializers.IntegerField(source='id', read_only=True)
    # 默认返回前 3 条二级评论
    user = serializers.StringRelatedField()
    replies = serializers.SerializerMethodField()

    def get_replies(self, obj):
        # 获取前 3 条二级评论
        replies_qs = obj.replies.all().order_by("created_at")[:3]
        return ReplySerializer(replies_qs, many=True).data

    class Meta:
        model = Comment
        fields = '__all__'


class ReplySerializer(serializers.ModelSerializer):
    comment_id = serializers.IntegerField(source='id', read_only=True)
    user = serializers.StringRelatedField()

    class Meta:
        model = Comment
        fields = '__all__'


class CommentUserSerializer(serializers.ModelSerializer):
    comment_id = serializers.IntegerField(source='id', read_only=True)
    article = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        exclude = ['user']

    def validate_content(self, value):
        if not value:
            raise serializers.ValidationError("评论内容不能为空")
        return value

    def validate(self, attrs):
        # 获取父评论
        parent = attrs.get('parent')
        # 检查层级深度
        if parent and parent.parent:
            raise serializers.ValidationError("只允许二级回复")

        return attrs

    def get_article(self, obj):
        return obj.article.get_absolute_url()


class FollowNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class FollowListSerializer(serializers.ModelSerializer):
    following = FollowNestedSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['following', 'created_at']
        extra_kwargs = {
            'created_at': {'read_only': True}
        }
