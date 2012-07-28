import os

from django import forms
from django.db import models
from django.contrib.auth.models import User

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

class TextItem(models.Model):
    """A very basic model for storing bits of text-based content"""
    name = models.CharField(max_length=200)
    content = models.TextField()
    def __unicode__(self):
        return "TextItem: %s" % self.name

def textspace(namespace):
    '''Uses the beginning of name strings retrieve all the
    TextItem objects that share the same root in their name. Returns a dictionary
    with the form:
        {
        'text_item_name':'text_item_content',
        }
    Can be used to quickly add text items to a context and then use them
    directly in templates.
    '''
    objs = TextItem.objects.filter(name__startswith=namespace)
    d = {}
    for t in objs:
            d[t.name] = t.content
    return d


class DataFile(Dated):
    """Data files represent individual file uploads.
    They are used to construct DataLayers.

    """
    file = models.FileField(upload_to=get_upload_path)
    upload = models.ForeignKey('UploadEvent', null=True, blank=True)
    def get_upload_path(self, filename):
        return 'uploads/%s/%s' % (self.upload.user.username, filename)
    def __unicode__(self):
        return "DataFile: %s" % self.name

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

# still need the models for making site collections and site models
# as well as designating terrain layers.







