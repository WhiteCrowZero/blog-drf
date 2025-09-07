# exceptions.py
from rest_framework.views import exception_handler
from django.db import DatabaseError, IntegrityError
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def database_exception_handler(exc, context):
    # 先调用DRF的默认异常处理
    response = exception_handler(exc, context)

    if response is None:
        # 检查是否是数据库异常
        if isinstance(exc, IntegrityError):
            logger.error(f"数据完整性错误: {exc}")
            return Response(
                {"error": "数据完整性错误", "detail": "请检查输入数据"},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif isinstance(exc, DatabaseError):
            logger.error(f"数据库错误: {exc}")
            return Response(
                {"error": "数据库操作失败", "detail": "服务器内部错误，请稍后重试"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return response
