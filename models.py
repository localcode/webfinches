import os
import zipfile

from django import forms
from django.db import models
from django.contrib.auth.models import User
from django.core import validators

# requires GeoDjango Libraries
from django.contrib.gis.gdal import DataSource

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
            return os.path.join( self.extract_path(), piece[0] )
    def __unicode__(self):
        return "DataFile: %s" % self.file.url
    def get_layer_data(self):
        """extracts relevant data for building LayerData objects
            meant to be used as initial data for LayerReview Forms
        """
        data = {}
        data['data_file_id'] = self.id
        abs_path = self.abs_path()
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

class DataLayer(Named, Authored, Dated, Noted):
    geometry_type = models.CharField(max_length=50, null=True, blank=True)
    srs = models.CharField(max_length=50, null=True, blank=True)
    files = models.ManyToManyField('DataFile', null=True, blank=True )
    def get_browsing_data(self):
        obj = vars(self)
        tags = self.tag_set.all()
        if tags:
            obj['tags'] = ' '.join( [t.name for t in tags] )
        else:
            obj['tags'] = ''
        return obj
    def __unicode__(self):
        return "DataLayer: %s" % self.name

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



