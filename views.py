from django.http import HttpResponse
import os

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import authenticate, login

from django.contrib.auth.models import User

#from django.contrib.gis.gdal import DataSource

from webfinches.forms import ShpUploadForm, ShpFormSet, ZipFormSet
from webfinches.models import *

from django.core.mail import send_mail

'''
#Another login def
def login_user(request):
    state = "Please log in below..."
    username = ''
    password = ''
    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                state = "You're successfully logged in!"
            else:
                state = "Your account is not active, please contact the site admin."
        else:
            state = "Your username and/or password were incorrect."

    return render_to_response('webfinches/logged.html',{'state':state, 'username': username}
'''

#Register def

def register(request):
	local_code_email = 'localcode@localco.de'
	message = open('\templates\registration\send_mail.txt','r').read()
	name = forms.CharField(max_length=100)
	user_email = forms.EmailField()
	username = forms.CharField()
	password1 = forms.CharField(max_length=30,is_required=True)
	password2 = forms.CharField(max_length=30,is_required=True, validator_list=[validators.AlwaysMatchesOtherField('password1','Passwords must match.')])
	
	send_mail(user_email, message, local_code_email, user_email)
	return HttpResponseRedirect('/webfinches/register/complete/') # Redirect after POST
 
#testing login def 
'''
def login(request):
	def errorHandle(error):
		form = LoginForm()
		return render_to_response('login.html', {
				'error' : error,
				'form' : form,
		})
	if request.method == 'POST': # If the form has been submitted...
		form = LoginForm(request.POST) # A form bound to the POST data
		if form.is_valid(): # All validation rules pass
			username = request.POST['username']
			password = request.POST['password']
			user = authenticate(username=username, password=password)
			if user is not None:
				if user.is_active:
					# Redirect to a success page.
					login(request, user)
					return render_to_response('webfinches/logged_in.html', {
						'username': username,
					})
				else:
					# Return a 'disabled account' error message
					error = u'account disabled'
					return errorHandle(error)
			else:
				 # Return an 'invalid login' error message.
				error = u'invalid login'
				return errorHandle(error)
		else:
			error = u'form is invalid'
			return errorHandle(error)
	else:
		form = LoginForm() # An unbound form
		return render_to_response('login.html', {
			'form': form,
		})
		'''
		
def send_file_to_db(fobj):
    pass

def handleShpFiles(username, layername, shp, dbf, prj, shx):
    path = 'media/uploads/%s' % username
    if not os.path.exists(path):
        os.makedirs(path)
    for f in (shp, prj, dbf, shx):
        ext = os.path.splitext(f.name)[1]
        filename = '%s%s' % (layername, ext)
        with open(os.path.join(path, filename), 'wb+') as destination:
            for chunk in f.chunks():
                print type(chunk)
                destination.write(chunk)
            destination.close()
    return os.path.join(path, '%s.shp' % layername)

def index(request):
    """A view for browsing the existing webfinches.
    """
    return render_to_response(
            'webfinches/index.html',
            {'webfinches':DataLayer.objects.all()},
            )
# still need to work on these ones
def login(request):
	# login to site 
	user=User.objects.get(username='carlos')
	context = {
					'user': user,
					#'password': password,
						}
	
	return render_to_response(
            'webfinches/login.html',
            context,
            )
# still need to work on this ones
def create_account(request):
	# login to site 
	user=User.objects.get(username='carlos')
	context = {
					#'user': user,
					#'password': password,
						}
	
	return render_to_response( 'webfinches/create_account.html', context, ) 

def upload(request):
    """A view for uploading new data.
    """
    user=User.objects.get(username='carlos')
    #print request
    if request.method == 'POST':
        formset = ZipFormSet(request.POST, request.FILES)
        for form in formset:
            if form.is_valid():
                data = form.cleaned_data
                if data:
                    ds_path = handleShpFiles('localcode', data['layer_name'],
                            data['shp_file'], data['dbf_file'],
                            data['prj_file'], data['shx_file'])
                    full_path = os.path.join(os.getcwd(), ds_path)
                    ds = DataSource(full_path)
                    layer = ds[0]
                    datalayer = DataLayer()
                    datalayer.author = user
                    datalayer.name = data['layer_name']
                    datalayer.srs = data['epsg_code']
                    datalayer.path = ds_path
                    datalayer.geometry_type = layer.geom_type.name
                    datalayer.save()
                    # make the bounding box
                    xmin, ymin, xmax, ymax = layer.extent.tuple
                    box = LayerBox()
                    box.x_min = xmin
                    box.x_max = xmax
                    box.y_min = ymin
                    box.y_max = ymax
                    box.layer = datalayer
                    box.save()
                    for i, field in enumerate(layer.fields):
                        attribute = Attribute()
                        attribute.name = field
                        attribute.data_type = layer.field_types[i].__name__
                        attribute.layer = datalayer
                        attribute.save()
                    tags = data['tags'].split()
                    for tag in tags:

                        pass



                #print 'shp_file' in data
                # perhaps instantiate a fileupload object
                # use the geos api to read the file from the path you put it
                # on.
                # using geos, build the layer object, also building fields for
                # each layer


    else:
        formset = ZipFormSet()

    c = {
            'formset':formset,
            }
    return render_to_response(
            'webfinches/upload.html',
            RequestContext(request, c),
            )


def review(request):
    # do someting / get something
    layers = Layer.objects.all()
    # define a context for the template
    context = {
            'layers':layers,
            'user': request.User,
            }
    # return a rendered template using the context
    return render_to_response(
            'webfinches/review.html',
            context,
            )

layers = ['site','roads','parcels','selected sites']
projections = ['wsg93','wsg93','tansverse mercator','']

individual_sites = [ ]
for i in range(1,10):
	individual_sites.append(str(i)+'.json') 

zip_file = ['sites.zip']
api_download = ['https://github.com/localcode']

def configure(request):
	# configure site layers 
	#layers = DataLayer.objects.all()
	#layers = layers

	context = {
					'layers': layers,
					'projections': projections,
						}
	
	return render_to_response(
            'webfinches/browse/configure.html',
            context,
            )
	
def download(request):
	#A view for downloading data.

	# configure site layers 
	#layers = DataLayer.objects.all()
	#layers = layers
	

	'''user=User.objects.get(username='carlos')
    #print request
    if request.method == 'GET':
        formset = ZipFormSet(request.GET, request.FILES)
        for form in formset:
            if form.is_valid():
                data = form.cleaned_data
                if data:
                    ds_path = handleShpFiles('localcode', data['layer_name'],
                            data['shp_file'], data['dbf_file'],
                            data['prj_file'], data['shx_file'])
                    full_path = os.path.join(os.getcwd(), ds_path)
                    ds = DataSource(full_path)
                    layer = ds[0]
                    datalayer = DataLayer()
                    datalayer.author = user
                    datalayer.name = data['layer_name']
                    datalayer.srs = data['epsg_code']
                    datalayer.path = ds_path
                    datalayer.geometry_type = layer.geom_type.name
                    datalayer.save()
                    # make the bounding box
                    xmin, ymin, xmax, ymax = layer.extent.tuple
                    box = LayerBox()
                    box.x_min = xmin
                    box.x_max = xmax
                    box.y_min = ymin
                    box.y_max = ymax
                    box.layer = datalayer
                    box.save()
                    for i, field in enumerate(layer.fields):
                        attribute = Attribute()
                        attribute.name = field
                        attribute.data_type = layer.field_types[i].__name__
                        attribute.layer = datalayer
                        attribute.save()
                    tags = data['tags'].split()
                    for tag in tags:

                        pass

                #print 'shp_file' in data
                # perhaps instantiate a fileupload object
                # use the geos api to read the file from the path you put it
                # on.
                # using geos, build the layer object, also building fields for
                # each layer

    else:
        formset = ZipFormSet()'''

	context = {
					'individual_sites': individual_sites,
					'zip_file': zip_file,
					'api_download': api_download,
					#'user': request.User,
						}

	return render_to_response(
            'webfinches/download.html',
            context,
            )
# AJAX views for processing file data

def fileReceiver(request):
    """Receives a File object. Returns data about the file."""
    pass

def layerInfo(request):
    """Receives a snippet of data about a file, and returns information to the
     browser via ajax.
    """
    pass

def ajaxUpload(request):
    """A view for ajax uploads of data.

        Should return information to
    """
    pass


