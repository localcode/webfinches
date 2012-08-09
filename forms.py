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
        # create a DataFile object
        data_file = super(ZipUploadForm, self).save(commit=False)
        # attach the UploadEvent
        data_file.upload = upload
        data_file.save(commit)
        return data_file

class LayerReviewForm(forms.ModelForm):
    """For editing and configuring the layer information for each layer."""
    data_file_id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = DataLayer
        fields = ['name', 'notes', 'geometry_type', 'srs']


ZipFormSet = formset_factory(ZipUploadForm, extra=1)
LayerReviewFormSet = formset_factory(LayerReviewForm, extra=0)

