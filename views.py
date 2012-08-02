from django.http import HttpResponse
import os

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import authenticate, login

from django.contrib.auth.models import User

#from django.contrib.gis.gdal import DataSource

from webfinches.forms import *
from webfinches.models import *

from django.core.mail import send_mail


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
    user=User.objects.get(username='carlos')
    #print request
    if request.method == 'POST':
        upload = UploadEvent(user=user)
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
    """A view for uploading new data.
    """
    user=User.objects.get(username='benjamin')
    if request.method == 'POST': # someone is giving us data
        formset = LayerReviewFormSet(request.POST, request.FILES)
        for form in formset:
            print 'reviewing form'
    else: # we are asking them to review data
        # get the last upload of this user
        upload = UploadEvent.objects.filter(user=user).order_by('-date')[0]
        data_files = DataFile.objects.filter(upload=upload)
        layer_data = [ f.get_layer_data() for f in data_files ]
        print layer_data
        formset = LayerReviewFormSet( initial=layer_data )
    c = {
            'formset':formset,
            }
    return render_to_response(
            'webfinches/review.html',
            RequestContext(request, c),
            )



layers = ['site','roads','parcels','selected sites']
projections = ['wsg93','wsg93','tansverse mercator','']


individual_sites = [ ]
for i in range(1,10):
	individual_sites.append(str(i)+'.json')

zip_file = ['sites.zip']
api_download = ['https://github.com/localcode']

def configure(request):
	# configure site layers
	#layers = DataLayer.objects.all()
	#layers = layers

	context = {
					'layers': layers,
					'projections': projections,
						}

	return render_to_response(
            'webfinches/browse/configure.html',
            context,
            )

def download(request):
	#A view for downloading data.

	# configure site layers
	#layers = DataLayer.objects.all()
	#layers = layers


	context = {
					'individual_sites': individual_sites,
					'zip_file': zip_file,
					'api_download': api_download,
					#'user': request.User,
						}



individual_sites = [ ]
for i in range(1,10):
	individual_sites.append(str(i)+'.json')

zip_file = ['sites.zip']

def configure(request):
	# configure site layers
	#layers = DataLayer.objects.all()
	#layers = layers

	context = {
					'layers': layers,
					'projections': projections,
						}

	return render_to_response(
            'webfinches/configure.html',
            context,
            )

def download(request):
	# configure site layers
	#layers = DataLayer.objects.all()
	#layers = layers

	context = {
					'individual_sites': individual_sites,
					'zip_file': zip_file,
						}

	return render_to_response(
            'webfinches/download.html',
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


