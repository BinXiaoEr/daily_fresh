from  celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import time

#创建一个celery实例对象
app=Celery('celery_tasks.tasks',broker='redis://192.168.31.133:6379/0')
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daily_fresh.settings')
django.setup()
from goods.models import GoodsType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner
from django.template import loader

@app.task#定义任务函数
def send_register_active_email(to_email,username,token):
    """发送激活邮件"""
    subject = '天天生鲜欢迎信息'
    sender = settings.EMAIL_FROM
    message = ''
    receiver = [to_email]
    html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/>' \
                   '<a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' \
                   % (username, token, token)
    send_mail(subject, message, sender, receiver, html_message=html_message)
    time.sleep(5)


@app.task
def generate_static_index_html():
    '''显示首页'''
    # 获取商品的种类信息
    types = GoodsType.objects.all()

    # 获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    for type in types:  # GoodsType
        # 获取type种类首页分类商品的图片展示信息
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        # 获取type种类首页分类商品的文字展示信息
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

        # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
        type.image_banners = image_banners
        type.title_banners = title_banners

    # 获取用户购物车中商品的数目
    # 组织模板上下文
    context = {'types': types,
               'goods_banners': goods_banners,
               'promotion_banners': promotion_banners, }

    # 使用模板
    temp = loader.get_template('static_index.html')
    html = temp.render(context)
   # print(context)
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    #print(save_path)
    with open(save_path, 'w') as f:
        f.write(html)

