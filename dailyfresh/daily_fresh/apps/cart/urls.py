
from django.conf.urls import url,include
from .views import CartAddView,CartInfoView,CartUpdateView,CartDeleteView
urlpatterns = [
url(r'^add$',CartAddView.as_view(),name='add'),#购物车记录添加
    url('^$',CartInfoView.as_view(),name='show'),#购物车显示
    url('^update$', CartUpdateView.as_view(), name='update'),  # 购物车显示
    url(r'^delete$', CartDeleteView.as_view(), name='delete'),  # 购物车记录删除
]
