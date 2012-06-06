from django import forms
from django.forms import widgets
from django.forms.formsets import formset_factory


class ShpUploadForm(forms.Form):
    "for the upload"
    layer_name = forms.CharField(max_length=200,
            widget=forms.TextInput(attrs={
                'class':'name_field',
                })
            )
    epsg_code = forms.CharField(max_length=20,
            widget=forms.TextInput(attrs={
                'class':'epsg_field',
                }), required=False,
            )
    tags = forms.CharField(max_length=200,
            widget=forms.TextInput(attrs={
                'class':'tag_field',
                }), required=False,
            )
    z_field = forms.CharField(max_length=200,
            widget=forms.TextInput(attrs={
                'class':'z_field',
                }), required=False,
            )
    shp_file = forms.FileField(label='.shp')
    prj_file = forms.FileField(label='.prj', required=False)
    dbf_file = forms.FileField(label='.dbf')
    shx_file = forms.FileField(label='.shx')

ShpFormSet = formset_factory(ShpUploadForm, extra=10)

