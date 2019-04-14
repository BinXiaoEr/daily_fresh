from django.shortcuts import render

# Create your views here.
from  django.views.generic import  View
from django.http import JsonResponse
from goods.models import GoodsSKU

from django_redis import get_redis_connection

class CartAddView(View):
    def post(self,request):
        #购物车记录的添加

        user=request.user
        if not user.is_authenticated:
            #用户未登陆
            return JsonResponse({"res":0, 'errmsg': '数据不完整'})
        #就收数据
        sku_id=request.POST.get('sku_id')
        count = request.POST.get('count')
        #数据校验
        if not all([sku_id,count]):
            return JsonResponse({"res":1,'errmsg':'数据不完整'})
        #校验添加的商品数量
        try:
            count=int(count)
        except Exception as e:
            return JsonResponse({"res":2,'errmsg':'商品数不完整'})
        try:
            sku =GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({"res": 3, 'errmsg': '商品数不存在'})
        #业务处理：添加购物车记录
            #先尝试获取购物车此商品加购的数量
        conn =get_redis_connection('default')
        cart_key="cart_%d"%user.id
        #如果查找的不存在 返回的是None
        cart_count=conn.hget(cart_key,sku_id)
        if cart_count:
            #累加购物车中商品的数目
            count +=int(cart_count)
        #如果没有这个数目count 就是count
        #设置hash中sku_id的值
        if count>sku.stock:
            return JsonResponse({"res": 4, 'errmsg': '商品库存不足'})
        conn.hset(cart_key,sku_id,count)
        total_count =conn.hlen(cart_key)
        #返回应答

        return JsonResponse({"res":5, 'total_count':total_count,'errmsg': '添加成功'})
from utils.mixin import LoginRequiredMixin
class CartInfoView(LoginRequiredMixin,View):
    def get(self,request):
        '''显示'''
        # 获取登录的用户
        user = request.user
        # 获取用户购物车中商品的信息
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # {'商品id':商品数量, ...}
        cart_dict = conn.hgetall(cart_key)

        skus = []
        # 保存用户购物车中商品的总数目和总价格
        total_count = 0
        total_price = 0
        # 遍历获取商品的信息
        for sku_id, count in cart_dict.items():
            # 根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 计算商品的小计
            amount = sku.price * int(count)
            # 动态给sku对象增加一个属性amount, 保存商品的小计
            sku.amount = amount
            # 动态给sku对象增加一个属性count, 保存购物车中对应商品的数量
            sku.count = count.decode()
            # 添加
            skus.append(sku)

            # 累加计算商品的总数目和总价格
            total_count += int(count)
            total_price += amount

        # 组织上下文
        context = {'total_count': total_count,
                   'total_price': total_price,
                   'skus': skus}

        # 使用模板
        return render(request, 'cart.html', context)
class CartUpdateView(View):
    def post(self,request):
        user = request.user
        if not user.is_authenticated:
            # 用户未登陆
            return JsonResponse({"res": 0, 'errmsg': '数据不完整'})
        # 就收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 数据校验
        if not all([sku_id, count]):
            return JsonResponse({"res": 1, 'errmsg': '数据不完整'})
        # 校验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({"res": 2, 'errmsg': '商品数不完整'})
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({"res": 3, 'errmsg': '商品数不存在'})
        conn=get_redis_connection('default')
        cart_key='cart_%d'%user.id
        if count>sku.stock:
            return JsonResponse({"res": 4, 'errmsg': '商品库存不足'})
        conn.hset(cart_key,sku_id,count)
        return JsonResponse({"res": 5, 'errmsg': '更新成功'})

class CartDeleteView(View):
    '''购物车记录删除'''
    def post(self, request):
        '''购物车记录删除'''
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收参数
        sku_id = request.POST.get('sku_id')

        # 数据的校验
        if not sku_id:
            return JsonResponse({'res':1, 'errmsg':'无效的商品id'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return JsonResponse({'res':2, 'errmsg':'商品不存在'})

        # 业务处理:删除购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id

        # 删除 hdel
        conn.hdel(cart_key, sku_id)

        # 计算用户购物车中商品的总件数 {'1':5, '2':3}
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res':3, 'total_count':total_count, 'message':'删除成功'})