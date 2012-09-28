import os
import math
import itertools

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
from django.contrib.gis.gdal import *


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
    """
    A view to generate sites based on SiteConfigurations and Spatial Database
    Queries
    """
    user = request.user
    if request.method == 'POST': # someone is editing site configuration
        site_configurations = SiteConfiguration.objects.filter(author=user).order_by('-date_edited')
        configuration_id = request.POST.get("create_sites")
        
        # This will give me the selected site and perform distance queries.
        site_configurations_selected = SiteConfiguration.objects.get(id=configuration_id)
        srs = site_configurations_selected.srs
        radius = site_configurations_selected.radius
        
        site_layer = site_configurations_selected.site_layer
        other_layers = site_configurations_selected.other_layers.all()
        # this makes the radius bogus....
        radius = (site_configurations_selected.radius)*7
        path_site_layer = site_layer.get_browsing_data()['pathy']
        ds_site_layer = DataSource( path_site_layer )
        layer_site_layer = ds_site_layer[0]
        
        layer_site_fields = layer_site_layer.fields
        site_field_values = [[geom.get(field) for field in layer_site_fields] for geom in layer_site_layer]
        field_attributes = [dict(itertools.izip(layer_site_fields, field_value)) for field_value in site_field_values]
        site_attributes_dict = [dict([("type","feature"), ("properties", attribute)])for attribute in field_attributes]
        site_centroids = [ ]
        site_json = [ ]
        site_dicts = [ ]
        for feature in layer_site_layer:
            if feature.geom.srs:
                polygon = feature.geom.transform(srs,True)
                site_json.append(polygon.json)
                # it used to be append(feature.geom.json)
                # but I think this gets the reprojected geom?
                
                #Get the centroid to calculate distances.
                site_centroids.append(get_centroid(polygon))
        geom_json_dict = [dict([("geometry", geom)])for geom in site_json]
        
        site_json_dicts = list(itertools.izip(geom_json_dict,site_attributes_dict))
        for site_json_dict in site_json_dicts:
            site_geojson_dict = {"type": "Feature Collection", "features":site_json_dict}
            site_dict = {"type": "Layer", "name":"site", "contents":site_geojson_dict}
            site_dicts.append(site_dict)
        temporary_geo_json = site_dicts[2] # this is the 'finished' list of site dicts
        print temporary_geo_json
        
        # Also iterate through all the site layers??? and make radius distance not bogus...
        # Fix the geoJSON dict.....
        
        test_site_number = 3
        # Maybe Create a Range of number of sites and loop with this??? The max number can
        # be the len of geometries???
        # Also maybe I don't need to get the centroid, I can do queries with polygons?
        
        site = site_centroids[test_site_number]
        if len(other_layers) != 0:
            other_features_list = [ ]
            for other_layer in other_layers:
                path_other_layer = other_layer.get_browsing_data()['pathy']
                ds_site_layer = DataSource( path_other_layer )
                layer_other_layer = ds_site_layer[0]
                other_layer_fields = layer_other_layer.fields
                
                other_centroids = [ ]
                other_layers_features = [ ]
                for feature in layer_other_layer:
                    #Geometries can only be transformed if they have a .prj file
                    #print feature.get('Type')
                    if feature.geom.srs:
                        polygon = feature.geom.transform(srs,True)
                        #Get the centroid to calculate distances.
                        other_centroids.append(get_centroid(polygon))
                for centroid in other_centroids:
                    distance = math.sqrt(((site.x-centroid.x)**2)+((site.y-centroid.y)**2))
                    if distance <= radius:
                        #create dictionaries based on layer.... that way I can retrieve the list...
                        # Here I can add the other script I wrote to get dictionaries, etc...
                        
                        ############################################
                        # This is not appending the right geometries.... I guess it just appends the
                        # first one...... how can I append all of them??? Maybe get its FID???
                        # I think I might have to create a dictionary and then get all the
                        # attributes based on the query..... fuck!
                        # something like retireve the key for the selected value... key could be
                        # feature ID???
                        other_layers_features.append(feature)
                
                '''
                Here I am going to start creating the dictionaries with the GDAL API
                '''
                if len(other_layers_features) > 0:
                    other_layer_name = other_layers_features[0].layer_name
                    other_layer_dict = dict([(other_layer_name, other_layers_features)])
                    other_features_list.append(other_layer_dict)
            
            #print other_features_list
            # are these feature objects gonna let me get gdal attributes???
            # if they don't, maybe I can create the attributes first and then query them
            # based on distance???
            # and now figure out how to get key and values to get all the gis info from them

            # We are not getting the right geometries from the queries!!!

            for other_feature in other_features_list:
                for v in other_feature:
                    other_layers_list = other_feature.get(v)
                    #print other_layers_list
                    other_layer_fields = other_layers_list[0].fields
                    other_field_values = [[geom.get(field) for field in other_layer_fields] for geom in other_layers_list]
                    other_field_attributes = [dict(itertools.izip(other_layer_fields, field_value)) for field_value in other_field_values]
                    other_attributes_dict = [dict([("type","feature"), ("properties", attribute)])for attribute in other_field_attributes]
                    other_json = [ ]
                    other_dicts = [ ]
                    for feature in other_layers_list:
                        if feature.geom.srs:
                            polygon = feature.geom.transform(srs,True)
                            other_json.append(polygon.json)
                        other_json_dict = [dict([("geometry", geom)])for geom in other_json]
                    other_json_dicts = list(itertools.izip(other_json_dict, other_attributes_dict))
                    for othr_json_dict in other_json_dicts:
                        other_geojson_dict = {"type": "Feature Collection", "features":othr_json_dict}
                        other_dict = {"type": "Layer", "name":v, "contents":other_geojson_dict}
                        other_dicts.append(other_dict)
                    
                    print other_dicts #Now we only need to append all the elements of the
                    # individual lists into a new list with all the other layers!!!!
                    # We are not getting the right geometries from the queries!!!
                    # dunno if it is really getting the right geometry!
            
            # Here I am gonna try to save the SiteSets!!!
            # First I need to erase the DB, create a new one and sync it!!!
            '''
            sites_set = SiteSet(author = user, configuration = site_configurations_selected,
                                geoJson = site_dicts)
            
            sites_set.save() # We create the object
            # the question is.... if once I save this as a string, am I gonna be able to
            # access them as a list??? Do I need to save them as m2m????
            '''
            
            # We add the m2m relationship with other_layes
            # maybe I can save a list of siteset appending them individually like othe_layers
            # but this needs to be m2m....
            # maybe I had to generate all the site_dicts when I created the site_config and
            # then just retrieve the selected one???
            # for other_layer in other_layers:
            #    configuration.other_layers.add(other_layer)
            #configuration.save() # Re-save the SiteConfiguration
            
            return HttpResponseRedirect('/webfinches/create_sites/')
    
    else:
        # We are browsing data
        site_configurations = SiteConfiguration.objects.filter(author=user).order_by('-date_edited')

    c = {
            'site_configurations': site_configurations,
            }
    return render_to_response(
            'webfinches/create_sites.html',
            RequestContext(request, c),
            )


'''
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
        
        site_configurations_selected = SiteConfiguration.objects.filter(author=user).order_by('-date_edited')[0]
        site_layer = site_configurations_selected.site_layer
        other_layer = site_configurations_selected.other_layers.all()#[0]
        radius = site_configurations_selected.radius
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
'''

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

def get_centroids(polygon):
    #Gets the centroid of DataLayers to do a distance query based on them.
    #Converts different type of geometries into point objects.
    centroids = [ ]
    if polygon.geom_type == 'POINT':
        centroid = polygon
        centroids.append(centroid)
    elif polygon.geom_type == 'POLYGON':
        centroid = polygon.centroid
        centroids.append(centroid)
    #Linestrings and geometry collections can't return centroid,
    #so we get the bbox and then the centroid.
    elif polygon.geom_type == 'LINESTRING' or 'MULTIPOINT' or 'MULTILINESTRING' or 'MULTIPOLYGON':
        bbox = polygon.envelope.wkt
        centroid = OGRGeometry(bbox).centroid
        centroids.append(centroid)
    return centroids

def get_centroid(polygon):
    '''
    Gets the centroid of DataLayers to do a distance query based on them.
    Converts different type of geometries into point objects.
    '''
    
    if polygon.geom_type == 'POINT':
        centroids = polygon
    elif polygon.geom_type == 'POLYGON':
        centroids = polygon.centroid
    #Linestrings and geometry collections can't return centroid,
    #so we get the bbox and then the centroid.
    elif polygon.geom_type == 'LINESTRING' or 'MULTIPOINT' or 'MULTILINESTRING' or 'MULTIPOLYGON':
        bbox = polygon.envelope.wkt
        centroids = OGRGeometry(bbox).centroid
    return centroids
