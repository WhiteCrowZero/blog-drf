from django.urls import path

from social import views

urlpatterns = [
    # 点赞
    path("like/<slug:slug>/", views.LikeToggleView.as_view(), name="article-like"),
    path("like/my/", views.MyLikeListView.as_view(), name="my-article-like"),

    # 收藏
    path("collect/", views.CollectionView.as_view(), name="collect"),
    path("collect/<int:collection_id>/", views.CollectionDetailView.as_view(), name="collect-detail"),
    path("collect/<int:collection_id>/<slug:slug>/", views.CollectionToggleView.as_view(), name="collect-toggle"),

    # 评论
    path("comment/<slug:slug>/", views.CommentArticleListView.as_view(), name="comment-article"),
    path("comment/<int:comment_id>/replies/", views.CommentRepliesView.as_view(), name="comment-replies"),
    path("comment/<slug:slug>/create/", views.CommentUserCreateView.as_view(), name="comment-article-create"),
    path("comment/<int:comment_id>/delete/", views.CommentUserDestroyView.as_view(), name="comment-article-delete"),

    # 订阅
    path("follow/<int:user_id>/", views.FollowUserToggleView.as_view(), name='follow'),
    path("follow/my/", views.MyFollowListView.as_view(), name='my-follow'),
]
