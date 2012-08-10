import os

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import authenticate, login

from django.contrib.auth.models import User

from webfinches.forms import *
from webfinches.models import *
from django.contrib.auth.views import login
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required


def index(request):
    """A view for browsing the existing webfinches.
    """
    return render_to_response(
            'webfinches/index.html',
            {'webfinches':DataLayer.objects.all()},
            )

@login_required
def upload(request):
    """A view for uploading new data.
    """
    user = request.user
    #print request
    if request.method == 'POST':
        upload = UploadEvent(user=user)
        upload.save()
        formset = ZipFormSet(request.POST, request.FILES)
        for form in formset:
            if form.is_valid() and form.has_changed():
                data_file = form.save(upload)
        return HttpResponseRedirect('/webfinches/review/')
    else:
        formset = ZipFormSet()

    c = {
            'formset':formset,
            }
    return render_to_response(
            'webfinches/upload.html',
            RequestContext(request, c),
            )

@login_required
def review(request):
    """A view for uploading new data.
    """
    user = request.user
    if request.method == 'POST': # someone is giving us data
        formset = LayerReviewFormSet(request.POST)
        if formset.is_valid():
        		for form in formset:
        				# get the DataFile id from the form data
        				data_file_id = form.cleaned_data['data_file_id']
        				# now get the actual object associated with that id
        				data_file = DataFile.objects.get(id=data_file_id)
        				srs = form.cleaned_data['srs']
        				layer = DataLayer(srs = srs)
        				layer = form.save(commit=False)
        				layer.author = user
        				# the DataLayer must exist before we can add relations to it
        				layer.save()
        				layer.files.add(data_file) # add the relation
        				layer.save() # resave the layer
        return HttpResponseRedirect('/webfinches/browse/')

    else: # we are asking them to review data
        # get the last upload of this user
        upload = UploadEvent.objects.filter(user=user).order_by('-date')[0]
        data_files = DataFile.objects.filter(upload=upload)
        layer_data = [ f.get_layer_data() for f in data_files ]
        formset = LayerReviewFormSet( initial=layer_data )

    c = {
            'formset':formset,
            }
    return render_to_response(
            'webfinches/review.html',
            RequestContext(request, c),
            )

@login_required
def browse(request):
    """A view for browsing and editing layers"""
    user = request.user
    layers = DataLayer.objects.filter(author=user).order_by('-date_edited')
    browsing_data = [ l.get_browsing_data() for l in layers ]
    # do I need to convert these to dicts?
    formset = LayerBrowseFormSet(initial=browsing_data)
    all_tags = Tag.objects.all()
    c = {
            'formset': formset,
            'tags': all_tags,
            }
    return render_to_response(
            'webfinches/browse.html',
            RequestContext( request, c ),
            )

@login_required
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

@login_required
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

