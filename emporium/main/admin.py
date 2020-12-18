from PIL import Image

from django.forms import ModelChoiceField, ModelForm, ValidationError
from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import *


class SmartphoneAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(SmartphoneAdminForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and not instance.sd:
            # if there is no sd card, field for its max capacity becomes readonly
            self.fields['sd_max_volume'].widget.attrs.update({
                'readonly': True,
                'style': 'background: lightblue'
            })

    def clean(self):
        if not self.cleaned_data['sd']:
            self.cleaned_data['sd_max_volume'] = None
        return self.cleaned_data


class NotebookAdminForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = mark_safe(
            """<span style="color:red; font-size:12px">Images larger than {} * {} px will be cropped</span>
            """.format(*Product.MAX_RESOLUTION))


# def clean_image(self):
#     image = self.cleaned_data['image']
#     img = Image.open(image).size
#     min_width, min_height = Product.MIN_RESOLUTION
#     max_width, max_height = Product.MAX_RESOLUTION
#     if image.size > Product.MAX_IMAGE_SIZE:
#         raise ValidationError("Image size shouldn't be more then 3 Mb")
#     if img[0] < min_width or img[1] < min_height:
#         raise ValidationError('Image is too small')
#     if img[0] > max_width or img[1] > max_height:
#         raise ValidationError('Image is too big')
#     return image


class NotebookAdmin(admin.ModelAdmin):
    form = NotebookAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='notebooks'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SmartphoneAdmin(admin.ModelAdmin):
    change_form_template = 'admin.html'
    form = SmartphoneAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='smartphones'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Category)
admin.site.register(Notebook, NotebookAdmin)
admin.site.register(Smartphone, SmartphoneAdmin)
admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Customer)
admin.site.register(Order)
