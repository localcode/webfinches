import os
import zipfile
from urllib import urlencode
from urllib2 import urlopen
import json

from django import forms
from django.contrib.auth.models import User
from django.core import validators

# requires GeoDjango Libraries
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.gdal import OGRGeometry
from django.contrib.gis.measure import D
from django.contrib.gis.db import models

# the basepath for file uploads (needed to read shapefiles)
from settings import MEDIA_ROOT

def get_upload_path(instance, filename):
    return instance.get_upload_path(filename)

class Authored(models.Model):
    """For things made by people """
    author = models.ForeignKey(User)
    class Meta:
        abstract=True

class Named(models.Model):
    """just putting names on models"""
    name = models.CharField(max_length=200, null=True, blank=True)
    class Meta:
        abstract=True

class Dated(models.Model):
    date_added = models.DateTimeField(auto_now_add=True)
    date_edited = models.DateTimeField(auto_now=True)
    class Meta:
        abstract=True

class Noted(models.Model):
    notes = models.TextField(null=True, blank=True)
    class Meta:
        abstract=True

class Lookup(Named):
    """name and slug"""
    slug = models.SlugField(max_length=100, null=True, blank=True)
    class Meta:
        abstract=True

class GeomType(models.Model):
    """just putting names on models"""
    geometry_type = models.CharField(max_length=200, null=True, blank=True)
    class Meta:
        abstract=True

class Bboxes(models.Model):
    """just putting names on models"""
    bbox = models.TextField()
    class Meta:
        abstract=True

class GeomFields(models.Model):
    """just putting names on models"""
    bbx = models.TextField()
    class Meta:
        abstract=True

class DataFile(Dated):
    """Data files represent individual file uploads.
    They are used to construct DataLayers.
    """
    file = models.FileField(upload_to=get_upload_path)
    upload = models.ForeignKey('UploadEvent', null=True, blank=True)
    def get_upload_path(self, filename):
        return 'uploads/%s/%s' % (self.upload.user.username, filename)
    def abs_path(self):
        """returns the full path of the zip file"""
        return os.path.join( MEDIA_ROOT, self.file.__unicode__())
    def extract_path(self):
        """returns a directory path for extracting zip files to"""
        return os.path.splitext( self.abs_path() )[0]
    def path_of_part(self, ext):
        """give an file extension of a specific file within the zip file, and
        get an absolute path to the extracted file with that extension.
            Assumes that the contents have been extracted.
            Returns `None` if the file can't be found
        """
        pieces = os.listdir( self.extract_path() )
        piece = [p for p in pieces if ext in p]
        if not piece:
            return None
        else:
            #path_of_part_list = [ ]
            #for p in piece:
                #path_of_part_list.append(p)
            return os.path.join( self.extract_path(), piece[0] )
        #return path_of_part_list
    def __unicode__(self):
        return "DataFile: %s" % self.file.url
    def get_layer_data(self):
        """extracts relevant data for building LayerData objects
            meant to be used as initial data for LayerReview Forms
        """
        data = {}
        data['data_file_id'] = self.id

        # see if we need to extract it
        extract_dir = self.extract_path()
        basename = os.path.split( extract_dir )[1]
        if not os.path.isdir( extract_dir ):
            # extract it to a directory with that name
            os.mkdir( extract_dir )
            zip_file = zipfile.ZipFile( self.file )
            zip_file.extractall( extract_dir )

        # get shape type
        shape_path = self.path_of_part('.shp')
        ds = DataSource( shape_path )
        layer = ds[0]

        data['geometry_type'] = layer.geom_type.name
        data['name'] = layer.name
        data['fields'] = layer.fields
        data['bbox'] = layer.extent.tuple
        if layer.srs:
            srs = layer.srs
            try:
                srs.identify_epsg()
                data['srs'] = srs['AUTHORITY'] +':'+srs['AUTHORITY', 1]
            except:
                data['srs'] = None
        if not data['srs']:
            # get .prj text
            prj_path = self.path_of_part('.prj')
            if prj_path:
                prj_text = open(prj_path, 'r').read()
                data['notes'] = prj_text
            data['srs'] = 'No known Spatial Reference System'
        return data
    
    def get_srs(self):
        """takes the prj data and sends it to the prj2epsg API.
        The API returns the srs code if found.
        """
        json_srs = {}
        prj_path = self.path_of_part('.prj')
        if prj_path:
            prj_text = open(prj_path, 'r').read()
            query = urlencode({
                'exact' : False,
                'error' : True,
                'terms' : prj_text})
            webres = urlopen('http://prj2epsg.org/search.json', query)
            jres = json.loads(webres.read())
            if jres['codes']:
                json_srs['message'] = 'An exact match was found'
                json_srs['srs'] = int(jres['codes'][0]['code'])
            else:
                json_srs['message'] = 'No exact match was found'
                json_srs['srs'] = 'No known Spatial Reference System'
        return json_srs
    
    def get_centroids(self, spatial_ref):
        '''
        Gets the centroids of the site layer to do a distance query based on them.
        Converts different type of geometries int point objects. 
        '''
        
        shp_path = self.path_of_part('.shp')
        site_ds = DataSource(shp_path)
        site_layer = site_ds[0]
        geoms = [ ]
        for feature in site_layer:
            #Geometries can only be transformed if they have a .prj file
            if feature.geom.srs:
                polygon = feature.geom.transform(spatial_ref,True)
                #Get the centroids to calculate distances.
                if polygon.geom_type == 'POINT':
                    centroids = polygon
                    geoms.append(centroids)
                elif polygon.geom_type == 'POLYGON':
                    centroids = polygon.centroid
                    geoms.append(centroids)
                #Linestrings and geometry collections can't return centroids,
                #so we get the bbox and then the centroid.
                elif polygon.geom_type == 'LINESTRING' or 'MULTIPOINT' or 'MULTILINESTRING' or 'MULTIPOLYGON':
                    bbox = polygon.envelope.wkt
                    centroids = OGRGeometry(bbox).centroid
                    geoms.append(centroids)
        return geoms

class DataLayer(Named, Authored, Dated, Noted, GeomType):
    srs = models.CharField(max_length=50, null=True, blank=True)
    files = models.ManyToManyField('DataFile', null=True, blank=True )
    layer_id = models.AutoField(primary_key=True)
    fields = models.TextField()

    objects = models.GeoManager() #added for spatial queries

    def __unicode__(self):
        return "DataLayer: %s" % self.name

class SiteConfiguration(Named, Authored, Dated, Noted, GeomType):
    srs = models.CharField(max_length=50, null=True, blank=True)
    files = models.ManyToManyField('DataFile', null=True, blank=True )
    layer_id = models.AutoField(primary_key=True)
    fields = models.TextField()

    objects = models.GeoManager() #added for spatial queries

    def __unicode__(self):
        return "DataLayer: %s" % self.name

class SiteLayer(Named, Authored, Dated, Noted):
    geometry_type = models.CharField(max_length=50, null=True, blank=True)
    srs = models.CharField(max_length=50, null=True, blank=True)
    files = models.ManyToManyField('DataLayer', null=True, blank=True )
    layer_id = models.AutoField(primary_key=True)
    radius = models.FloatField(max_length=10, null=True, blank=True)
    objects = models.GeoManager() #added for spatial queries
    
    def __unicode__(self):
        return "DataLayer: %s" % self.name

class SitesJson(Named, Authored, Dated, Noted):
    """Do database queries, and get the geometries around the sites.
    Generate GeoJson files from the geometries. 
    """
    sites = models.ManyToManyField('DataLayer', null=True, blank=True)
    site_layer = models.ForeignKey('SiteLayer', null=True, blank=True)
    radius = models.FloatField(max_length=10, null=True, blank=True)
    geojson = models.TextField(null=True, blank=True)
    objects = models.GeoManager()
    
    def __unicode__(self):
        return "UploadEvent: %s" % self.date
    
    def get_sites_within(self, radius):
        '''
        Performs distance queries, and creates json files.
        '''
        sites_within_json = [ ]
        for centroid in self:
            # If DataLayer uses a projected coordinate system, this is allowed.
            #Sites within the radius
            sites_within = DataLayer.objects.filter(geom__distance_lte=(centroid, D(m=radius)))
            sites_within_json.append(sites_within.json)
        return sites_within_json

    def get_sites_outside(self, radius):
        '''
        Performs distance queries, and creates json files.
        '''
        sites_outside_json = [ ]
        for centroid in self:
            #Sites outside the radius
            sites_outside = DataLayer.objects.filter(geom__distance_gte=(centroid, D(m=radius)))
            sites_outside_json.append(sites_within.json)
        return sites_outside_json
    
class UploadEvent(models.Model):
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    def __unicode__(self):
        return "UploadEvent: %s" % self.date

class Tag(Lookup, Dated, Noted):
    layers = models.ManyToManyField(DataLayer)
    def __unicode__(self):
        return "Tag: %s" % self.slug

class Attribute(Named):
    layer = models.ForeignKey(DataLayer)
    data_type = models.CharField(max_length=100)
    def __unicode__(self):
        return "Attribute: %s" % self.name



