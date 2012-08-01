from django import forms
from django.db import models
from django.contrib.auth.models import User
from django.core import validators

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

class DataLayer(Named, Authored, Dated, Noted):
    path = models.FilePathField()
    geometry_type = models.CharField(max_length=50)
    srs = models.CharField(max_length=50)
    def __unicode__(self):
        return "DataLayer: %s" % self.name

class LayerBox(models.Model):
    layer = models.OneToOneField(DataLayer)
    x_min = models.FloatField()
    x_max = models.FloatField()
    y_min = models.FloatField()
    y_max = models.FloatField()

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
class RegistrationForm(forms.Manipulator):
    def __init__(self):
        self.fields = (
            forms.TextField(field_name='username',
                            length=30, maxlength=30,
                            is_required=True, validator_list=[validators.isAlphaNumeric,
                                                              self.isValidUsername]),
            forms.EmailField(field_name='email',
                             length=30,
                             maxlength=30,
                             is_required=True),
            forms.PasswordField(field_name='password1',
                                length=30,
                                maxlength=60,
                                is_required=True),
            forms.PasswordField(field_name='password2',
                                length=30, maxlength=60,
                                is_required=True,
                                validator_list=[validators.AlwaysMatchesOtherField('password1',
                                                                                   'Passwords must match.')]),
            )
    
    def isValidUsername(self, field_data, all_data):
        try:
            User.objects.get(username=field_data)
        except User.DoesNotExist:
            return
        raise validators.ValidationError('The username "%s" is already taken.' % field_data)
    
    def save(self, new_data):
        u = User.objects.create_user(new_data['username'],
                                     new_data['email'],
                                     new_data['password1'])
        u.is_active = False
        u.save()
        return u
        '''
'''
#Need to figure out how to setup all this....
class UserProfile(models.Model):
    name = models.OneToOneField(User)
    activation_key = models.CharField(maxlength=40)
    key_expires = models.DateTimeField()
    name = forms.CharField(max_length=100)
    user_email = forms.EmailField()
    username = forms.CharField()
    password1 = forms.CharField(max_length=30,is_required=True)
    password2 = forms.CharField(max_length=30,is_required=True, validator_list=[validators.AlwaysMatchesOtherField('password1','Passwords must match.')])
    '''    
    
    
'''class LoginForm(forms.Form):
	username = forms.CharField(max_length=100)
	password = forms.CharField(widget=forms.PasswordInput(rendervalue=False),max_length=100)'''

# still need the models for making site collections and site models
# as well as designating terrain layers.







