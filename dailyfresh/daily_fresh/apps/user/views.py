from django.shortcuts import render,redirect
import re
from utils.mixin import LoginRequiredMixin
from .models import User,Address
from goods.models import GoodsSKU
from django.urls import reverse
from django.core.paginator import Paginator
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings
from django.http import  HttpResponse
from django.core.mail import send_mail
from order.models import OrderInfo,OrderGoods
from django.contrib.auth import authenticate,login,logout
#类视图
class Registerview(View):
    #注册
    def get(self,request):
        #显示注册页面


        return render(request, 'register.html', {})
    def post(self,request):
        pass
        #进行注册处理
        username = request.POST.get("user_name")
        password = request.POST.get("pwd")
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        if not all([username, password, email]):
            # 如果数据不完整
            return render(request, 'register.html', {"errmsg": "数据不完整"})
        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$$', email):
            return render(request, 'register.html', {"errmsg": "邮箱格式不正确"})

        if allow != "on":
            return render(request, 'register.html', {"errmsg": "请同意协议"})
        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except:
            # 用户名不存在
            user = None
        if user:
            return render(request, 'register.html', {"errmsg": "用户名已存在"})
        # 进行用户的注册
        user = User.objects.create_user(username,email, password)
        # 因为默认状态是已经激活 我门需要设置邮箱认证点击激活
        user.is_active = 0
        user.save()

        #发生激活链接，包含激活链接
        #激活链接需要包含用户的身份信息
        #加密用户的身份信息,生成激活token 使用django框架自带的密钥 并设置过期时间
        serializer=Serializer(settings.SECRET_KEY,3600)
        info={'confirm':user.id}
        token=serializer.dumps(info)
        token = token.decode()
        #发邮件
        subject="天天生鲜欢迎信息"
        html_message='<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/>' \
                                     '<a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>'\
                                     % (username, token, token)
        sender=settings.EMAIL_FROM
        receiver=[email]
        message=""
        #send_mail(subject,message,sender,receiver,html_message=html_message)
        from celery_tasks.tasks import send_register_active_email
        send_register_active_email.delay(email,username,token)
        # 返回应答，跳转到首页
        return redirect(reverse("goods:index"))

class Activity(View):
    #用户激活
    def get(self,request,token):
        #进行用户激活
        #进行解密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
             info =serializer.loads(token)#过期会有异常
             user_id=info['confirm']
             user=User.objects.get(id=user_id)
             user.is_active=1
             user.save()
             return redirect(reverse("user:login"))
             #跳转到登陆页面
        except SignatureExpired as e:
             #激活链接已经过期
            return HttpResponse("激活链接已经过期")

class LoginView(View):
    def get(self,request):
        #判断是否记住了用户名
        if 'username' in request.COOKIES:
            username=request.COOKIES.get('username')
            checked='checked'
        else:
            username=''
            checked=''
        return render(request,'login.html',{'username':username,'checked':checked})

    def post(self,request):
        username=request.POST.get('username')
        password=request.POST.get('pwd')
        if not all([username,password]):
            return render(request,'login.html',{'errmsg':'数据不完整'})
        user=authenticate(username=username,password=password)
        if user is not  None:
            if user.is_active:
                #记录用户登陆状态
                login(request,user)
                #判断是否需要记住用户名
                #获取登陆后跳转到的地址
                next_url=request.GET.get('next',reverse("goods:index"))#
                responser=redirect(next_url)
                rem =request.POST.get('remember')
                if rem=='on':
                    #记住用户名
                    responser.set_cookie('username',username,max_age=7*25*3600)
                else:
                    responser.delete_cookie('username')
                return responser
            else:

                return render(request,'login.html',{'errmsg':'用户还未进行邮箱验证'})
        else:

            return render(request,'login.html',{'errmsg':'用户名或密码错误'})



class UserInfoView(LoginRequiredMixin,View):
    def get(self,request):
        #获取用户的个人信息
        user=request.user
        #获取收货地址
        try:
            addres=Address.objects.get(user=user,is_default=True)
        except Address.DoesNotExist:
            #不存在默认地址
            addres=None
        #获取用户的历史浏览页面
        from redis import StrictRedis
        from django_redis import get_redis_connection
        #con=StrictRedis(host='127.0.0.1',port='6379',db=3)
        con=get_redis_connection('default')
        history_key='history_%d'%user.id
        #获取用户最新浏览的5个商品
        sku_id=con.lrange(history_key,0,4)
        good_li=GoodsSKU.objects.filter(id__in=sku_id)
        #按照浏览顺序保存记录
        goods_res=[]
        for a_id in sku_id:
            for goods in good_li:
                if a_id ==goods.id:
                    goods_res.append(goods)
        context={'page':'user','address':addres,'goods_li':good_li}
        #从数据库中查询用户浏览的商品具体信息
        return render(request,'user_center_info.html',context)

class UserOrderView(LoginRequiredMixin,View):
    def get(self,request,page):
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count * order_sku.price
                # 动态给order_sku增加属性amount,保存订单商品的小计
                order_sku.amount = amount
            print(order.order_status)
            # 动态给order增加属性，保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS_CHOICES[order.order_status-1][1]
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus

        # 分页
        paginator = Paginator(orders, 1)

        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # todo: 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示1-5页
        # 3.如果当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {'order_page': order_page,
                   'pages': pages,
                   'page': 'order'}

        # 使用模板
        return render(request, 'user_center_order.html', context)


class UserSiteView(LoginRequiredMixin,View):
    def get(self, request):
        #获取用户的默认收货地址
        user=request.user
        try:
            addres=Address.objects.get(user=user,is_default=True)
        except Address.DoesNotExist:
            #不存在默认地址
            addres=None
        return render(request, 'user_center_site.html',{'page':'address','address':addres})
    def post(self,request):
        #接受数据
        rece=request.POST.get('receiver')
        addr=request.POST.get('addr')
        zip_cod=request.POST.get("zip_code")
        phone=request.POST.get('phone')
        # 校验
        if not all([rece,addr,phone]):
            return render(request,'user_center_site.html',{'errmsg':'数据不完整'})

        if not re.match(r'^1(3|4|5|7|8)\d{9}$',phone):
            return render(request,'user_center_site.html',{'errmsg':'手机号不正确'})
        #获取登陆用户的登陆对象
        user=request.user
        #查询是否有默认的地址
        try:
            addres=Address.objects.get(user=user,is_default=True)
        except Address.DoesNotExist:
            #不存在默认地址
            addres=None
        if addres:
            is_defult=False
        else:
            is_defult=True
        Address.objects.create(user=user,receiver=rece,addr=addr,zip_code=zip_cod,phone=phone,is_default=is_defult)
        print(addres)
       #业务处理
        return redirect(reverse('user:address'))
class LogoutView(View):
    '''退出登录'''
    def get(self, request):
        '''退出登录'''
        # 清除用户的session信息
        logout(request)
        # 跳转到首页
        return redirect(reverse('goods:index'))