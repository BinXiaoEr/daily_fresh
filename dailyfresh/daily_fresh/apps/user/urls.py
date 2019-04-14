
from django.conf.urls import url
from user.views import Registerview,Activity,LoginView,UserInfoView,UserOrderView,UserSiteView,LogoutView
urlpatterns = [
    url(r'register$',Registerview.as_view(),name='register'),
    url(r'active/(?P<token>.*)$',Activity.as_view(),name='active'),#用户激活
    url(r'login$',LoginView.as_view(),name='login'),
    #url('order$', login_required(UserOrderView.as_view()), name='order'),#用户订单页面
    #url(r'^$', login_required(UserInfoView.as_view()), name='user'), # 用户中心-信息页
    #url('address$', login_required(UserSiteView.as_view()), name='address'),#用户地址页面
   # url(r'^logout$',login_required( LogoutView.as_view()), name='logout'),  # 注销登录
     url('order/(?P<page>\d+)$', UserOrderView.as_view(), name='order'),#用户订单页面
    url(r'^$', UserInfoView.as_view(), name='user'), # 用户中心-信息页
     url('address$', UserSiteView.as_view(), name='address'),#用户地址页面
     url(r'^logout$', LogoutView.as_view(), name='logout'),  # 注销登录
]
