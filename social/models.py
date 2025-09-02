from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes")
    article = models.ForeignKey("articles.Article", on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tb_like"
        unique_together = ("user", "article")  # 一个用户对一篇文章只能点一次赞

    def __str__(self):
        return f'{self.user.id} like {self.article.slug}'


class Collection(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="collections")
    name = models.CharField(max_length=64, verbose_name="收藏夹名称")
    description = models.CharField(max_length=2000, default='暂无描述', blank=True, verbose_name="描述")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tb_collection"
        unique_together = ("user", "name")

    def __str__(self):
        return f'{self.user.id} - {self.name}'


class CollectionItem(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="items")
    article = models.ForeignKey("articles.Article", on_delete=models.CASCADE, related_name="collected_items")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tb_collection_item"
        unique_together = ("collection", "article")

    def __str__(self):
        return f'{self.collection.name} - {self.article.slug}'


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    article = models.ForeignKey("articles.Article", on_delete=models.CASCADE, related_name="comments")
    content = models.CharField(max_length=2000, verbose_name="评论内容", null=False)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tb_comment"
        ordering = ['created_at']


class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tb_follow"
        unique_together = ("follower", "following")

    def __str__(self):
        return f'{self.follower.username} following {self.following.username}'

    def is_following(self, user):
        return self.following.filter(following=user).exists()

