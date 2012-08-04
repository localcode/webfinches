import os
import zipfile

from django import forms
from django.db import models
from django.contrib.auth.models import User
from django.core import validators

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
    def __unicode__(self):
        return "DataFile: %s" % self.file.url
    def get_layer_data(self):
        data = {}
        f = self.file
        zip_file = zipfile.ZipFile(f)
        contents = zip_file.namelist()
        proj = [n for n in contents if '.prj' in n]
        if proj:
            # guess the srs
            proj_text = zip_file.open( proj[0] ).read()
            data['notes'] = proj_text
            data['srs'] = ''
        else:
            data['srs'] = ''
        # give a default name
        basename = os.path.splitext(contents[0])[0]
        data['name'] = basename
        f.close()
        return data


class DataLayer(Named, Authored, Dated, Noted):
    geometry_type = models.CharField(max_length=50, null=True, blank=True)
    srs = models.CharField(max_length=50, null=True, blank=True)
    files = models.ManyToManyField('DataFile', null=True, blank=True )
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

'''
class UserName(models.Model):
    # This is the only required field
    user = models.ForeignKey(User, unique=True)

    # The rest is completely up to you...
    favorite_band = models.CharField(maxlength=100, blank=True)
    favorite_cheese = models.CharField(maxlength=100, blank=True)
    lucky_number = models.IntegerField()
'''
# still need the models for making site collections and site models
# as well as designating terrain layers.







