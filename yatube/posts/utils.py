from django.core.paginator import Paginator
from yatube.settings import PAGE_QUANTITY


def page_quan(queryset, request):
    paginator = Paginator(queryset, PAGE_QUANTITY)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_object': page_object,
    }
