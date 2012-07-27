from django import forms
from django.forms import widgets
from django.forms.formsets import formset_factory


class ZipUploadForm(forms.Form):
    """For uploading .zip files that contain .shp files"""
    zip_file = forms.FileField(label='.zip')

class LayerReviewForm(forms.Form):
    """For editing and configuring the layer information for each layer."""
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


ZipFormSet = formset_factory(ZipUploadForm, extra=10)
LayerReviewFormSet = formset_factory(LayerReviewForm, extra=0)

