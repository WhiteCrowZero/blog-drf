from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers, generics, status
from services import permissions
from .models import Like, Collection, CollectionItem, Comment, Follow
from .serializers import CollectionSerializer, LikeSerializer, CommentArticleSerializer, CommentUserSerializer, \
    ReplySerializer, FollowListSerializer
from articles.models import Article

User = get_user_model()


class LikeToggleView(APIView):
    """ 点赞/取消点赞视图 """

    def post(self, request, slug):
        user = request.user
        article = Article.objects.get(slug=slug)
        like, created = Like.objects.get_or_create(user=user, article=article)
        if not created:
            like.delete()
            return Response({"detail": "取消点赞成功"}, status=status.HTTP_200_OK)
        return Response({"detail": "点赞成功"}, status=status.HTTP_201_CREATED)


class MyLikeListView(generics.ListAPIView):
    """ 用户点赞文章列表视图 """
    serializer_class = LikeSerializer

    def get_queryset(self):
        return Like.objects.filter(user=self.request.user)


class CollectionView(generics.ListCreateAPIView):
    """ 用户收藏夹列表视图 """
    serializer_class = CollectionSerializer

    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        name = serializer.validated_data.get("name", "默认收藏夹")

        # 检查当前用户是否已有同名的收藏夹
        if Collection.objects.filter(user=self.request.user, name=name).exists():
            raise serializers.ValidationError({"collection": "当前收藏夹已存在"})

        serializer.save(user=self.request.user)


class CollectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """ 用户收藏夹修改视图 """
    serializer_class = CollectionSerializer
    # 指定查询字段为模型中的 id 字段
    lookup_field = 'id'
    # 指定 URL 中的参数名为 collection_id
    lookup_url_kwarg = 'collection_id'
    permission_classes = [IsAuthenticated, permissions.IsSelf, permissions.IsActiveAccount]

    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        name = serializer.validated_data.get("name", "默认收藏夹")

        # 检查当前用户是否已有同名的收藏夹
        if Collection.objects.filter(user=self.request.user, name=name).exists():
            raise serializers.ValidationError({"collection": "当前收藏夹已存在"})


class CollectionToggleView(APIView):
    """ 文章收藏/取消收藏视图 """

    def post(self, request, collection_id, slug):
        article = Article.objects.get(slug=slug)
        collect_item, created = CollectionItem.objects.get_or_create(collection_id=collection_id, article=article)
        if not created:
            collect_item.delete()
            return Response({"detail": "取消收藏成功"}, status=status.HTTP_200_OK)
        return Response({"detail": "收藏成功"}, status=status.HTTP_201_CREATED)


class CommentArticleListView(generics.ListAPIView):
    """ 文章评一级论列表视图 """
    serializer_class = CommentArticleSerializer
    permission_classes = [AllowAny]  # 所有人可见

    def get_queryset(self):
        article_slug = self.kwargs.get("slug")
        return Comment.objects.filter(
            article__slug=article_slug,
            parent__isnull=True  # 一级评论
        ).prefetch_related("replies__user").order_by("created_at")


class CommentRepliesView(generics.ListAPIView):
    """ 文章二级回复列表视图 """
    serializer_class = ReplySerializer
    # 其他二级回复需要登录
    # permission_classes = [AllowAny]

    def get_queryset(self):
        comment_id = self.kwargs.get("comment_id")
        return Comment.objects.filter(parent_id=comment_id).select_related("user").order_by("created_at")


class CommentUserCreateView(generics.CreateAPIView):
    """ 用户评论创建视图 """
    serializer_class = CommentUserSerializer

    def perform_create(self, serializer):
        article_slug = self.kwargs['slug']
        article = Article.objects.get(slug=article_slug)
        serializer.save(user=self.request.user, article=article)


class CommentUserDestroyView(generics.DestroyAPIView):
    """ 用户评论删除视图 """
    serializer_class = CommentUserSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'comment_id'

    def get_queryset(self):
        return Comment.objects.filter(user=self.request.user)


class FollowUserToggleView(APIView):
    """ 用户订阅/取消订阅视图 """
    def post(self, request, user_id):
        follower = request.user
        if follower.id == user_id:
            raise serializers.ValidationError({"following": "用户不能关注自己"})

        try:
            following = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"following": "您关注的用户不存在"})

        follow, created = Follow.objects.get_or_create(follower=follower, following=following)
        if not created:
            follow.delete()
            return Response({"detail": "取消关注成功"}, status=status.HTTP_200_OK)
        return Response({"detail": "关注成功"}, status=status.HTTP_201_CREATED)


class MyFollowListView(generics.ListAPIView):
    """ 用户订阅列表视图 """
    serializer_class = FollowListSerializer

    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user)
