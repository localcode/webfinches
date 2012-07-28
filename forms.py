import os
import zipfile

from django import forms
from django.forms import widgets
from django.forms.formsets import formset_factory

from webfinches.models import DataFile, DataLayer, UploadEvent


class ZipUploadForm(forms.ModelForm):
    """For uploading .zip files that contain .shp files"""

    class Meta:
        model = DataFile
        fields = ['file']

    def clean_file(self):
        zip_file = self.cleaned_data['file']
        zf = zipfile.ZipFile(zip_file)
        contents = zf.namelist()
        filetypes = [os.path.splitext(c)[1] for c in contents]
        if '.shp' not in filetypes:
            raise forms.ValidationError('.zip uploads must contain .shp files')
        if '.dbf' not in filetypes:
            raise forms.ValidationError('.zip uploads must contain .dbf files')
        if '.shx' not in filetypes:
            raise forms.ValidationError('.zip uploads must contain .shx files')
        return zip_file

    def save(self, upload, commit=True):
        """Data Files need a UploadEvent in order to be saved"""
        zip_file = self.cleaned_data['file']
        # create a DataFile object
        data_file = super(ZipUploadForm, self).save(commit=False)
        # attache the UploadEvent
        data_file.upload = upload
        print data_file.upload
        data_file.save(commit)
        return data_file

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


ZipFormSet = formset_factory(ZipUploadForm, extra=1)
LayerReviewFormSet = formset_factory(LayerReviewForm, extra=0)

