from django.http import HttpResponse
import os

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext


from django.contrib.auth.models import User


from webfinches.forms import *
from webfinches.models import *


def handleZipFile(username, layername, shp, dbf, prj, shx):
    path = 'media/uploads/%s' % username
    if not os.path.exists(path):
        os.makedirs(path)
    for f in (shp, prj, dbf, shx):
        ext = os.path.splitext(f.name)[1]
        filename = '%s%s' % (layername, ext)
        with open(os.path.join(path, filename), 'wb+') as destination:
            for chunk in f.chunks():
                print type(chunk)
                destination.write(chunk)
            destination.close()
    return os.path.join(path, '%s.shp' % layername)


def index(request):
    """A view for browsing the existing webfinches.
    """
    return render_to_response(
            'webfinches/index.html',
            {'webfinches':DataLayer.objects.all()},
            )

def upload(request):
    """This view is for uploading zip files and creating new DataFile objects
        It could be grown to read the uploaded files intelligently.
    """
    user = User.objects.get(username='benjamin')

    if request.method == 'POST':
        upload = UploadEvent(user=user)
        upload.save()
        formset = ZipFormSet(request.POST, request.FILES)
        for form in formset:
            if form.is_valid():
                data_file = form.save(upload)

    else:
        formset = ZipFormSet()

    c = {
            'formset':formset,
            }
    return render_to_response(
            'webfinches/upload.html',
            RequestContext(request, c),
            )

def review(request):
    # get the organized layer objects
    author = request.user
    # temporarily override this
    author = User.objects.get(username='localcode')
    layers = DataLayer.objects.filter(author=author).order_by('-date_added')

    formset = ZipFormSet()

    context = {
            'layers':layers,
            }
    # return a rendered template using the context
    return render_to_response(
            'webfinches/review.html',
            context,
            )




