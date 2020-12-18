from django import template
from django.utils.safestring import mark_safe
from main.models import Smartphone
register = template.Library()

TABLE_HEAD = """
                <table class="table">
                <tbody>
            """

TABLE_TAIL = """
                </tbody>
                </table>
            """

TABLE_CONTENT = """
                    <tr>
                        <td>{name}</td>
                        <td>{value}</td>
                    </tr>
                """

PRODUCT_SPEC = {
    'notebook': {
        'Diagonal': 'diagonal',
        'Display type': 'display_type',
        'Processor frequency': 'processor_freq',
        'RAM': 'ram',
        'Video card': 'video_card',
        'Battery capacity': 'battery_capacity'
    },
    'smartphone': {
        'Diagonal': 'diagonal',
        'Display type': 'display_type',
        'Screen resolution': 'resolution',
        'Battery capacity': 'battery_capacity',
        'RAM': 'ram',
        'SD': 'sd',
        'SD max capacity': 'sd_max_volume',
        'Main camera': 'camera_main',
        'Frontal camera': 'camera_frontal'
    }
}


def get_product_spec(product, model_name):
    table_content = ''
    for name, value in PRODUCT_SPEC[model_name].items():
        table_content += TABLE_CONTENT.format(name=name, value=getattr(product, value))
    return table_content


@register.filter
def product_spec(product):
    model_name = product.__class__._meta.model_name
    if isinstance(product, Smartphone):
        if not product.sd:
            PRODUCT_SPEC['smartphone'].pop('SD max capacity')
        else:
            PRODUCT_SPEC['smartphone']['SD max capacity'] = 'sd_max_volume'
    return mark_safe(TABLE_HEAD + get_product_spec(product, model_name) + TABLE_TAIL)
