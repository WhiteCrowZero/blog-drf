from django.db import models
from django.conf import settings
from autoslug import AutoSlugField
from django.urls import reverse
from django.utils import timezone


class Article(models.Model):
    title = models.CharField(max_length=255, verbose_name="标题")
    content = models.TextField(verbose_name="正文")
    slug = AutoSlugField(populate_from='title', unique=True, verbose_name="URL别名")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name="作者"
    )
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_draft = models.BooleanField(default=True, verbose_name="是否为草稿")
    cover_pic = models.ImageField(
        upload_to='cover/',
        default='cover/default.png',
        verbose_name="封面图片"
    )
    tags = models.ManyToManyField("Tag", related_name="articles", verbose_name="标签")

    class Meta:
        db_table = 'tb_article'
        ordering = ['-created_at']
        verbose_name = '文章'
        verbose_name_plural = '文章管理'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('article-detail', kwargs={'slug': self.slug})

    @property
    def is_published(self):
        return (
                not self.is_draft
                and self.published_at is not None
                and self.published_at <= timezone.now()
        )


class Tag(models.Model):
    name = models.CharField(max_length=32, unique=True, verbose_name="标签名称")
    slug = AutoSlugField(populate_from='name', unique=True, verbose_name="URL别名")

    class Meta:
        db_table = 'tb_tag'
        verbose_name = '标签'
        verbose_name_plural = '标签管理'
        ordering = ['-name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tag-article', kwargs={'slug': self.slug})
