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

import django.contrib.gis
from django.contrib.gis.geos import *
from django.contrib.gis.db import models
from django.contrib.gis.measure import D


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
                tags = form.cleaned_data['tags']
                layer = DataLayer(srs = srs, tags=tags)
                layer = form.save(commit=False)
                layer.author = user
                # the DataLayer must exist before we can add relations to it
                layer.save()
                layer.files.add(data_file) # add the relation
                layer.save() # resave the layer
        return HttpResponseRedirect('/webfinches/configure/')

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
    #Maybe we hould add Ajax to the add tags???
    user = request.user
    if request.method == 'POST': # someone is giving us data
        '''
        formset = LayerBrowseFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                # get the DataFile id from the form data
                data_tags = form.cleaned_data['tags']
                # now get the actual object associated with that id
                data_file = DataFile.objects.get(id=data_tags)
                '''
        formset = LayerReviewFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
            # get the DataFile id from the form data
                data_file_id = form.cleaned_data['data_file_id']
                # now get the actual object associated with that id
                data_file = DataFile.objects.get(id=data_file_id)
                
                tags = form.cleaned_data['tags']
                layer = DataLayer(tags = tags)
                layer = form.save(commit=False)
                layer.author = user
                # the DataLayer must exist before we can add relations to its
                layer.save()
                layer.files.add(data_file) # add the relation
                layer.save() # resave the layer
        return HttpResponseRedirect('/webfinches/configure/')

    else:
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
    """A view that contains ajax scripts for sorting and dealing with layers,
        in order to build SiteConfigurations
    """
    user = request.user
    if request.method == 'POST': # someone is editing site configuration
        layers = DataLayer.objects.filter(author=user).order_by('-date_edited')
        # Get site_layer from checkboxes
        site_id = request.POST.get("site_layer")
        site_layer = DataLayer.objects.get(id=site_id)
        # Get other_layers from checkboxes
        other_ids = request.POST.getlist("other_layers")
        other_layers = [ ]
        for other_layers_id in other_ids:
            other_layers.append(DataLayer.objects.get(id=other_layers_id))
        # Get radius for query
        try:
            radius = int(request.POST.get("radius"))
        except ValueError:
            radius = 1000 # We give them a predefined Radius if no radius or an invalid radius is selected
        srs = request.POST.get("srs") # Get the srs value to reproject DataLayers
        name = request.POST.get("name") # We get the SiteConfiguration name entered by the user
        configuration = SiteConfiguration(srs = srs, radius=radius, site_layer = site_layer
                                          , author = user, name = name)
        configuration.save() # We create the object
        # We add the m2m relationship with other_layes
        for other_layer in other_layers:
            configuration.other_layers.add(other_layer)
        configuration.save() # Re-save the SiteConfiguration
        
        return HttpResponseRedirect('/webfinches/create_sites/')

    else:
        # We are browsing data
        layers = DataLayer.objects.filter(author=user).order_by('-date_edited')
        layer = DataLayer.objects.filter(author=user)[0]
        all_tags = Tag.objects.all()
        
    
    c = {
            'layers': layers,
            'tags': all_tags,
    
            }
    return render_to_response(
            'webfinches/configure.html',
            RequestContext(request, c),
            )

@login_required
def create_sites(request):
    """A view to generate sites based on SiteConfigurations and Spatial Database
    Queries
    """
    user = request.user
    if request.method == 'POST': # someone is editing site configuration
        site_configurations = SiteConfiguration.objects.filter(author=user).order_by('-date_edited')
        # This one should create a SiteSet
        
    
    else:
        # We are browsing data
        site_configurations = SiteConfiguration.objects.filter(author=user).order_by('-date_edited')
        
        site_configurations_test = SiteConfiguration.objects.filter(author=user).order_by('-date_edited')[0]
        site_layer = site_configurations_test.site_layer
        other_layer = site_configurations_test.other_layers.all()#[0]
        radius = site_configurations_test.radius
        print site_layer, other_layer, radius
        path_site_layer = site_layer.get_browsing_data()['pathy']
        
        ds_site_layer = DataSource( path_site_layer )
        layer_site_layer = ds_site_layer[0]
        print ds_site_layer, layer_site_layer
        site_geoms = layer_site_layer.get_geoms(geos=True)
        print site_geoms
        
        pnt = fromstr('POINT(-96.876369 29.905320)', srid=4326)
        for geom in site_geoms:
            print geom.distance(pnt)
        
        

    c = {
            'site_configurations': site_configurations,
            }
    return render_to_response(
            'webfinches/create_sites.html',
            RequestContext(request, c),
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

