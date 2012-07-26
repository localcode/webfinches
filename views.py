from django.http import HttpResponse
import os

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext


from django.contrib.auth.models import User

from django.contrib.gis.gdal import DataSource

from webfinches.forms import ShpUploadForm, ShpFormSet, ZipFormSet
from webfinches.models import *

def send_file_to_db(fobj):
    pass

def handleShpFiles(username, layername, shp, dbf, prj, shx):
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
    """A view for uploading new data.
    """
    user=User.objects.get(username='localcode')
    #print request
    if request.method == 'POST':
        formset = ZipFormSet(request.POST, request.FILES)
        for form in formset:
            if form.is_valid():
                data = form.cleaned_data
                if data:
                    ds_path = handleShpFiles('localcode', data['layer_name'],
                            data['shp_file'], data['dbf_file'],
                            data['prj_file'], data['shx_file'])
                    full_path = os.path.join(os.getcwd(), ds_path)
                    ds = DataSource(full_path)
                    layer = ds[0]
                    datalayer = DataLayer()
                    datalayer.author = user
                    datalayer.name = data['layer_name']
                    datalayer.srs = data['epsg_code']
                    datalayer.path = ds_path
                    datalayer.geometry_type = layer.geom_type.name
                    datalayer.save()
                    # make the bounding box
                    xmin, ymin, xmax, ymax = layer.extent.tuple
                    box = LayerBox()
                    box.x_min = xmin
                    box.x_max = xmax
                    box.y_min = ymin
                    box.y_max = ymax
                    box.layer = datalayer
                    box.save()
                    for i, field in enumerate(layer.fields):
                        attribute = Attribute()
                        attribute.name = field
                        attribute.data_type = layer.field_types[i].__name__
                        attribute.layer = datalayer
                        attribute.save()
                    tags = data['tags'].split()
                    for tag in tags:

                        pass



                #print 'shp_file' in data
                # perhaps instantiate a fileupload object
                # use the geos api to read the file from the path you put it
                # on.
                # using geos, build the layer object, also building fields for
                # each layer


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
    # do someting / get something
    layers = Layer.objects.all()
    # define a context for the template
    context = {
            'layers':layers,
            'user': request.User,
            }
    # return a rendered template using the context
    return render_to_response(
            'webfinches/review.html',
            context,
            )


# AJAX views for processing file data

def fileReceiver(request):
    """Receives a File object. Returns data about the file."""
    pass

def layerInfo(request):
    """Receives a snippet of data about a file, and returns information to the
     browser via ajax.
    """
    pass

def ajaxUpload(request):
    """A view for ajax uploads of data.

        Should return information to
    """
    pass


