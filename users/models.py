from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from services.oauth import CONTACT_CHOICES

class CustomUser(AbstractUser):
    bio = models.CharField(max_length=255, default='该用户暂未填写简介', null=True, blank=True, verbose_name="个人简介")
    avatar = models.ImageField(
        upload_to='avatar/',
        default='avatar/default.png',
        null=True,
        blank=True,
        verbose_name="头像"
    )

    class Meta:
        db_table = 'tb_custom_user'
        verbose_name = '用户'
        verbose_name_plural = '用户管理'

    def __str__(self):
        return self.username


class UserContact(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name="所属用户"
    )
    type = models.CharField(max_length=50, choices=CONTACT_CHOICES, verbose_name="联系类型")
    openid = models.CharField(max_length=255, null=True, blank=True, verbose_name="OpenID")
    is_bound = models.BooleanField(default=False)

    class Meta:
        db_table = 'tb_user_contact'
        verbose_name = '用户外部联系方式'
        verbose_name_plural = '用户外部联系方式管理'

    def __str__(self):
        return f'{self.type}-{self.user.id}'
