"""
库存服务模块
提供库存检查和验证的业务逻辑
"""
from apps.products.models import ProductStock


class InsufficientStockError(Exception):
    """库存不足异常"""
    def __init__(self, product_name, available, required):
        self.product_name = product_name
        self.available = available
        self.required = required
        super().__init__(f'商品 {product_name} 库存不足,可用库存:{available},需要:{required}')


def check_stock_availability(product, quantity):
    """
    检查单个商品的库存是否充足
    
    Args:
        product: 商品对象
        quantity: 需要的数量
        
    Returns:
        tuple: (is_available: bool, stock: ProductStock|None)
        
    Raises:
        InsufficientStockError: 当库存不足时抛出
    """
    stock = getattr(product, 'stock', None)
    
    if not stock:
        raise InsufficientStockError(product.name, 0, quantity)
    
    if stock.available_quantity < quantity:
        raise InsufficientStockError(
            product.name, 
            stock.available_quantity, 
            quantity
        )
    
    return True, stock


def check_cart_items_stock(cart_items):
    """
    批量检查购物车商品的库存
    
    Args:
        cart_items: QuerySet 或 list of CartItem 对象
        
    Returns:
        bool: 所有商品库存充足返回 True
        
    Raises:
        InsufficientStockError: 当任一商品库存不足时抛出
    """
    for item in cart_items:
        check_stock_availability(item.product, item.quantity)
    
    return True
