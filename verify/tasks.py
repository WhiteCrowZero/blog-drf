import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags
from mysite.celery import app


@app.task
def send_email(email_recv, verify_code, mode='activate'):
    try:
        # 收件人列表格式化
        if isinstance(email_recv, str):
            email_recv = [email_recv]

        if mode == 'activate':
            # 邮件标题
            subject = 'Blog 激活邮件'

            # HTML 邮件内容
            html_message = f"""
                        <p>尊敬的用户，您好！</p>
                        <p>感谢您注册 <strong>Blog</strong>，请点击以下链接完成账户验证：</p>
                        <p style="font-size: 22px; font-weight: bold; color: #FF4C4C;">{verify_code}</p>
                        <p>该链接 <strong>{int(int(settings.EMAIL_EXPIRE_SECONDS) / 60)} 分钟</strong> 内有效，请尽快使用。</p>
                        <p>如果您未进行过本网站的注册操作，请忽略此邮件。</p>
                        <hr>
                        <p style="color: gray; font-size: 12px;">此邮件由系统自动发送，请勿直接回复。</p>
                    """
        elif mode == 'verify':
            # 邮件标题
            subject = 'Blog 邮箱验证邮件'

            # HTML 邮件内容
            html_message = f"""
                        <p>尊敬的用户，您好！</p>
                        <p>请点击以下链接完成账户邮箱更改的验证：</p>
                        <p style="font-size: 22px; font-weight: bold; color: #FF4C4C;">{verify_code}</p>
                        <p>该验证码 <strong>{int(int(settings.EMAIL_EXPIRE_SECONDS) / 60)} 分钟</strong> 内有效，请尽快使用。</p>
                        <p>如果您未进行过本网站的邮箱更改操作，请及时查看您的账户是否被盗。</p>
                        <hr>
                        <p style="color: gray; font-size: 12px;">此邮件由系统自动发送，请勿直接回复。</p>
                    """
        else:
            raise ValueError("Mode is error")

        # 纯文本内容（避免部分邮箱不支持 HTML）
        plain_message = strip_tags(html_message)
        # 发件人
        from_email = '13820826029@163.com'
        # 发送
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=email_recv,
            html_message=html_message
        )
        logging.info(f'邮件发送到: {email_recv}')
    except Exception as e:
        logging.error(f'邮件发送失败: {e}')
