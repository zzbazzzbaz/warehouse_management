from django.db import models
from django.core.exceptions import ValidationError


class Category(models.Model):
    """商品分类（最多二级）"""
    name = models.CharField('分类名称', max_length=100)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True, related_name='children',
        verbose_name='父分类'
    )
    sort_order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'categories'
        verbose_name = '商品分类'
        verbose_name_plural = '商品分类'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name
    
    def clean(self):
        """验证分类最多二级"""
        if self.parent and self.parent.parent:
            raise ValidationError('分类最多支持二级，不能选择已有父分类的分类作为父分类')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Product(models.Model):
    """商品"""
    name = models.CharField('商品名称', max_length=200)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, related_name='products',
        verbose_name='分类'
    )
    cost_price = models.DecimalField('成本价', max_digits=10, decimal_places=2)
    selling_price = models.DecimalField('售价', max_digits=10, decimal_places=2)
    image = models.ImageField('商品图片', upload_to='products/', blank=True)
    description = models.TextField('商品描述', blank=True)
    is_active = models.BooleanField('是否上架', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'products'
        verbose_name = '商品'
        verbose_name_plural = '商品'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_active', '-created_at']),
        ]

    def __str__(self):
        return self.name
