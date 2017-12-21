from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import npgettext, pgettext_lazy

from ...core.utils import get_paginator_items
from ...discount.models import Sale, Voucher
from ..views import staff_member_required
from .filters import SaleFilter, VoucherFilter
from . import forms


@staff_member_required
@permission_required('discount.view_sale')
def sale_list(request):
    sales = Sale.objects.prefetch_related('products').order_by('name')
    sale_filter = SaleFilter(request.GET, queryset=sales)
    sales = get_paginator_items(
        sale_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    counter = sale_filter.qs.count()
    summary_msg = npgettext(
        'Number of matching records in the dashboard sales list',
        'Found %(counter)d matching sale',
        'Found %(counter)d matching sales',
        number=counter) % {'counter': counter}
    ctx = {
        'sales': sales, 'filter': sale_filter,
        'is_empty': not sale_filter.queryset.exists(),
        'summary_msg': summary_msg}
    return TemplateResponse(request, 'dashboard/discount/sale/list.html', ctx)


@staff_member_required
@permission_required('discount.edit_sale')
def sale_edit(request, pk=None):
    instance = get_object_or_404(Sale, pk=pk) if pk else Sale()
    form = forms.SaleForm(request.POST or None, instance=instance)
    if form.is_valid():
        instance = form.save()
        msg = (
            pgettext_lazy('Sale (discount) message', 'Updated sale') if pk
            else pgettext_lazy('Sale (discount) message', 'Added sale'))
        messages.success(request, msg)
        return redirect('dashboard:sale-update', pk=instance.pk)
    ctx = {'sale': instance, 'form': form}
    return TemplateResponse(request, 'dashboard/discount/sale/form.html', ctx)


@staff_member_required
@permission_required('discount.edit_sale')
def sale_delete(request, pk):
    instance = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        instance.delete()
        msg = pgettext_lazy(
            'Sale (discount) message', 'Removed sale %s') % (instance.name,)
        messages.success(request, msg)
        return redirect('dashboard:sale-list')
    ctx = {'sale': instance}
    return TemplateResponse(
        request, 'dashboard/discount/sale/modal/confirm_delete.html', ctx)


@staff_member_required
@permission_required('discount.view_voucher')
def voucher_list(request):
    vouchers = (Voucher.objects.select_related('product', 'category')
                .order_by('name'))
    voucher_filter = VoucherFilter(request.GET, queryset=vouchers)
    vouchers = get_paginator_items(
        voucher_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    counter = voucher_filter.qs.count()
    summary_msg = npgettext(
        'Number of matching records in the dashboard vouchers list',
        'Found %(counter)d matching voucher',
        'Found %(counter)d matching vouchers',
        number=counter) % {'counter': counter}
    ctx = {
        'vouchers': vouchers, 'filter': voucher_filter,
        'is_empty': not voucher_filter.queryset.exists(),
        'summary_msg': summary_msg}
    return TemplateResponse(
        request, 'dashboard/discount/voucher/list.html', ctx)


@staff_member_required
@permission_required('discount.edit_voucher')
def voucher_edit(request, pk=None):
    if pk is not None:
        instance = get_object_or_404(Voucher, pk=pk)
    else:
        instance = Voucher()
    voucher_form = forms.VoucherForm(request.POST or None, instance=instance)
    type_base_forms = {
        Voucher.SHIPPING_TYPE: forms.ShippingVoucherForm(
            request.POST or None, instance=instance,
            prefix=Voucher.SHIPPING_TYPE),
        Voucher.VALUE_TYPE: forms.ValueVoucherForm(
            request.POST or None, instance=instance,
            prefix=Voucher.VALUE_TYPE),
        Voucher.PRODUCT_TYPE: forms.ProductVoucherForm(
            request.POST or None, instance=instance,
            prefix=Voucher.PRODUCT_TYPE),
        Voucher.CATEGORY_TYPE: forms.CategoryVoucherForm(
            request.POST or None, instance=instance,
            prefix=Voucher.CATEGORY_TYPE)}
    if voucher_form.is_valid():
        voucher_type = voucher_form.cleaned_data['type']
        form_type = type_base_forms.get(voucher_type)
        if form_type is None:
            instance = voucher_form.save()
        elif form_type.is_valid():
            instance = form_type.save()

        if form_type is None or form_type.is_valid():
            msg = pgettext_lazy(
                'Voucher message', 'Updated voucher') if pk else pgettext_lazy(
                    'Voucher message', 'Added voucher')
            messages.success(request, msg)
            return redirect('dashboard:voucher-list')
    ctx = {
        'voucher': instance, 'default_currency': settings.DEFAULT_CURRENCY,
        'form': voucher_form, 'type_base_forms': type_base_forms}
    return TemplateResponse(
        request, 'dashboard/discount/voucher/form.html', ctx)


@staff_member_required
@permission_required('discount.edit_voucher')
def voucher_delete(request, pk):
    instance = get_object_or_404(Voucher, pk=pk)
    if request.method == 'POST':
        instance.delete()
        msg = pgettext_lazy(
            'Voucher message', 'Removed voucher %s') % (instance,)
        messages.success(request, msg)
        return redirect('dashboard:voucher-list')
    ctx = {'voucher': instance}
    return TemplateResponse(
        request, 'dashboard/discount/voucher/modal/confirm_delete.html', ctx)
