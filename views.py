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
                tags = form.cleaned_data['tags']
                layer = DataLayer(srs = srs, tags=tags)
                layer = form.save(commit=False)
                layer.author = user
                # the DataLayer must exist before we can add relations to it
                layer.save()
                layer.files.add(data_file) # add the relation
                layer.save() # resave the layer
                print layer
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


    #if request.method == 'POST': # someone is giving us data
    #    formset = LayerReviewFormSet(request.POST)
    #    if formset.is_valid():
    #        for form in formset:
    #        # get the DataFile id from the form data
    #            data_file_id = form.cleaned_data['data_file_id']
    #            # now get the actual object associated with that id
    #            data_file = DataFile.objects.get(id=data_file_id)
    #            srs = form.cleaned_data['srs']
    #            tags = form.cleaned_data['tags']
    #            layer = DataLayer(srs = srs, tags=tags)
    #            layer = form.save(commit=False)
    #            layer.author = user
    #            # the DataLayer must exist before we can add relations to it
    #            layer.save()
    #            layer.files.add(data_file) # add the relation
    #            layer.save() # resave the layer
    #    return HttpResponseRedirect('/webfinches/configure/')
    #
    #else: # we are asking them to review data
    #    # get the last upload of this user
    #    upload = UploadEvent.objects.filter(user=user).order_by('-date')[0]
    #    data_files = DataFile.objects.filter(upload=upload)
    #    layer_data = [ f.get_layer_data() for f in data_files ]
    #    formset = LayerReviewFormSet( initial=layer_data )
    #
    #c = {
    #        'formset':formset,
    #        }
    #return render_to_response(
    #        'webfinches/review.html',
    #        RequestContext(request, c),
    #        )

@login_required
def configure(request):
    """A view that contains ajax scripts for sorting and dealing with layers,
        in order to build SiteConfigurations
    """
    user = request.user
    if request.method == 'POST': # someone is editing site configuration
        layers = DataLayer.objects.filter(author=user).order_by('-date_edited')
        site_id = request.POST.get("site_layer")
        other_ids = request.POST.getlist("other_layers")
        site_layer = DataLayer.objects.get(id=site_id)
        print site_layer, type(site_layer)
        other_layers_list = [ ]
        for other_layers_id in other_ids:
            other_layers_list.append(DataLayer.objects.filter(id=other_layers_id))
        try:
            radius = int(request.POST.get("radius"))
        except ValueError:
            radius = 1000 # We give them a predefined Radius if no radius or an invalid radius is selected
        srs = request.POST.get("srs")
        configuration = SiteConfiguration(srs = srs, radius=radius, site_layer=site_layer)
        print configuration

        #configuration = form.save(commit=False)
        configuration.author = user
        # the DataLayer must exist before we can add relations to it
        configuration.save()
        configuration.site_layer.add(site_layer) # add the relation #!!!!!! Foreign Key Objects have no add attribute...
        # the relationship needs to be established differently... just check the api... should be simple...
        #add is for m2m....
        #configuration.site_layer.
        #configuration.save() # resave the layer
        
        browsing_data = [ l.get_browsing_data() for l in layers ]
        #print browsing_data
        #print other_layers_ids, site_layer_id, radius, srs, site_layer, other_layers_list
        return HttpResponseRedirect('/webfinches/configure/')


    else:
        layers = DataLayer.objects.filter(author=user).order_by('-date_edited')
        #print layers
        #layer = [ f.get_browsing_data() for f in layers ]
        all_tags = Tag.objects.all()
        #other_layers = [ ]
        #site_layer = [ ]
    
    '''
    def handle(request):
        if request.method == 'POST':
            artists = request.POST.getlist('artists') # now artists is a list of [1,2,3]
    '''
    
    c = {
            'layers': layers,
            #'site_layer': site_layer,
            #'other_sites': other_layers,
            'tags': all_tags,
    
            }
    return render_to_response(
            'webfinches/configure.html',
            RequestContext(request, c),
            )

'''
def configure(request):
    """A view that contains ajax scripts for sorting and dealing with layers,
        in order to build SiteConfigurations
    """
    user = request.user
    if request.method == 'POST': # someone is editing site configuration
        formset = SiteConfigurationFormSet(request.POST)
        #formset = SiteConfigurationFormSet(request.POST, prefix='pfix')
        if formset.is_valid():
            pass
    else:
        layers = DataLayer.objects.filter(author=user).order_by('-date_edited')
        print layers
        layer = [ f.get_browsing_data() for f in layers ]
        print layer
        formset = SiteConfigurationFormSet( initial=layer )
        #formset = SiteConfigurationFormSet( initial=layer, prefix='pfix' )

        print formset.management_form
        print formset.is_valid()
        #all_tags = Tag.objects.all()
    
    
    def handle(request):
        if request.method == 'POST':
            artists = request.POST.getlist('artists') # now artists is a list of [1,2,3]
    
    
    c = {
            'layers': formset,
            #'tags': all_tags,
    
            }
    return render_to_response(
            'webfinches/configure.html',
            RequestContext(request, c),
            )
'''

@login_required
def create_sites(request):
    """A view to generate sites based on SiteConfigurations and Spatial Database
    Queries
    """
    user = request.user
    site_layer = DataLayer.objects.filter(author=user).get(related_name='siteconfiguration_site')
    try:
        other_sites = DataLayer.objects.filter(author=user).get(related_name='siteconfiguration_other')
    except DataLayer.DoesNotExist:
        other_sites = None
    
    sites_within = DataLayer.objects.filter(geom__distance_lte=(site_layer, D(m=radius)))
    sites_outside = DataLayer.objects.filter(geom__distance_gte=(site_layer, D(m=radius)))

    context = {
            'sites_within': sites_within,
            'sites_outside': sites_outside,
            }
    return render_to_response(
            'webfinches/get_sites.html',
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

