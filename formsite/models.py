from django.forms import *
from django.core import validators
from django.core.cache import cache

from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm

from django.db import models
from djangotoolbox import fields

from validation import *
from data_ranges import *
import random, string, datetime

import logging ###

############### USER and LAB INTEGRATION #######################
ACCESS_CODE_MAX_LENGTH = 20 #Designates the max_length of access_codes

#Create a random alphanumeric code of specified length.
def get_random_code(length = ACCESS_CODE_MAX_LENGTH):
	return "".join(
			random.choice(
				string.letters + string.digits
			) for i in range(length))	
	
	
class Lab_Group(models.Model):
	saved_data = [] #fields.ListField()
	lab_title = models.CharField(max_length=200)
	
	access_code = models.CharField(max_length=ACCESS_CODE_MAX_LENGTH,
		default=get_random_code)
	
	def __unicode__(self):
		return self.lab_title


############### USER CREATION #######################
class Lab_Member(models.Model):
	user = models.OneToOneField(User, unique=True)
	lab_group = models.ForeignKey(Lab_Group)
	
	def __unicode__(self):
		return self.user.username


class UserForm(ModelForm):
	username = CharField(label="Username", required=True,
		widget=TextInput(attrs={'class':'form_text'}))
	password = CharField(label="Password", required=True,
		widget=PasswordInput(attrs={'class':'form_text'}))
	first_name = CharField(label="First Name", required=True,
		widget=TextInput(attrs={'class':'form_text'}))
	last_name = CharField(label="Last Name", required=True,
		widget=TextInput(attrs={'class':'form_text'}))
	email = EmailField(label="Email", required=True,
		widget=TextInput(attrs={'class':'form_text'}))
				
	class Meta:
		model = User
		fields = ("username", "email", 
			"first_name", "last_name", 
			"password")
	
	#Hash the user's password upon save.
	def save(self, commit=True):
		user = super(UserForm, self).save(commit=False)
		user.set_password(self.cleaned_data["password"])
		if commit:
			user.save()
		return user
		
class UserProfileForm(ModelForm):
	#Enumerate all of the lab titles.
		
	lab_group = ModelChoiceField(queryset=Lab_Group.objects.all(),
		label="Lab Group", required=True,
		widget=Select(attrs={'class':'form_text'}))
	access_code = CharField(label="Access Code", required=True,
		max_length=ACCESS_CODE_MAX_LENGTH,
		widget=TextInput(attrs={'class':'form_text'}))
		
	class Meta:
		model = Lab_Member
		fields = ["lab_group"]

 
################ COMPOUND GUIDE ########################
class CompoundEntry(models.Model):
	abbrev = models.CharField("Abbreviation", max_length=100)
	compound = models.CharField("Compound", max_length=100)
	CAS_ID = models.CharField("CAS ID", max_length=13, blank=True, null=True)
	compound_type = models.CharField("Type", max_length=10)

	lab_group = models.ForeignKey(Lab_Group, unique=False)
		
	def __unicode__(self):
		if self.compound == self.abbrev:
			return "{} (--> same) (LAB: {})".format(self.abbrev, self.lab_group.lab_title)
		return "{} --> {} (LAB: {})".format(self.abbrev, self.compound, self.lab_group.lab_title)	

TYPE_CHOICES = [[opt,opt] for opt in edit_choices["typeChoices"]]

class CompoundGuideForm(ModelForm):
	compound = CharField(widget=TextInput(
		attrs={'class':'form_text',
		"title":"What the abbreviation stands for."}))
	abbrev = CharField(widget=TextInput(
		attrs={'class':'form_text form_text_short',
		"title":"The abbreviation you want to type."}))
	CAS_ID = CharField(label="CAS ID", widget=TextInput(
		attrs={'class':'form_text',
		"title":"The CAS ID of the compound if available."}),
		required=False)
	compound_type = ChoiceField(label="Type", choices = TYPE_CHOICES, 
		widget=Select(attrs={'class':'form_text dropDownMenu',
		"title":"Choose the compound type: <br/> --Organic <br/> --Inorganic<br/>--pH Changing<br/>--Oxalate-like<br/>"+
		"--Solute<br/>--Water"}))
		
	class Meta:
		model = CompoundEntry	
		exclude = ("lab_group",)

	def __init__(self, lab_group=None, *args, **kwargs):
		super(CompoundGuideForm, self).__init__(*args, **kwargs)
		self.lab_group = lab_group
		
	def save(self, commit=True):
		entry = super(CompoundGuideForm, self).save(commit=False)
		entry.lab_group = self.lab_group
		if commit:
			entry.save()
		return entry

	def clean(self):
		#Initialize the variables needed for the cleansing process.
		dirty_data = super(CompoundGuideForm, self).clean() #Get the available raw (dirty) data
		clean_data = {} #Keep track of cleaned fields
		
		try:
			clean_CAS_ID = dirty_data["CAS_ID"].replace(" ", "-").replace("/", "-").replace("_", "-")
			assert(clean_CAS_ID)
			#Check that the CAS ID has three hyphen-delineated parts.
			if len(clean_CAS_ID.split("-")) != 3:
				self._errors["CAS_ID"] = self.error_class(
					["CAS ID requires three distinct parts."])
			#Check that only numbers are present.
			elif not clean_CAS_ID.replace("-","").isdigit(): 
				self._errors["CAS_ID"] = self.error_class(
					["CAS ID may only have numeric characters."])
			clean_data["CAS_ID"] = clean_CAS_ID
		except Exception as e:
			#If no CAS_ID is found, store a blank value.
			logging.info("\n\n\nException!  {}".format(e))
			clean_data["clean_CAS_ID"] = ""
		
		other_fields = ["abbrev", "compound", "compound_type"]
		for field in other_fields:
			try:
				clean_data[field] = dirty_data[field]
			except:
				self._errors[field] = self.error_class(
					["This field cannot be blank."])
		
		return clean_data
		
############### DATA ENTRY ########################
#Create the form choices from the pre-defined ranges.
OUTCOME_CHOICES = [[opt,opt] for opt in edit_choices["outcomeChoices"]]
PURITY_CHOICES = [[opt,opt] for opt in edit_choices["purityChoices"]]
UNIT_CHOICES = [[opt,opt] for opt in edit_choices["unitChoices"]]
BOOL_CHOICES = [[opt,opt] for opt in edit_choices["boolChoices"]]

#Many data are saved per lab group. Each data represents one submission.
class Data(models.Model):
	reactant_1 = models.CharField("Reactant 1", max_length=100)
	quantity_1 = models.CharField("Quantity 1", max_length=15)
	unit_1 = models.CharField("Unit 1", max_length=10)
	
	reactant_2 = models.CharField("Reactant 2", max_length=200)
	quantity_2 = models.CharField("Quantity 2", max_length=25)
	unit_2 = models.CharField("Unit 2", max_length=20)
	
	reactant_3 = models.CharField("Reactant 3", max_length=300)
	quantity_3 = models.CharField("Quantity 3", max_length=35)
	unit_3 = models.CharField("Unit 3", max_length=30)
	
	reactant_4 = models.CharField("Reactant 4", max_length=400, blank=True)
	quantity_4 = models.CharField("Quantity 4", max_length=45, blank=True)
	unit_4 = models.CharField("Unit 4", max_length=40, blank=True)
	
	reactant_5 = models.CharField("Reactant 5", max_length=500, blank=True)
	quantity_5 = models.CharField("Quantity 5", max_length=55, blank=True)
	unit_5 = models.CharField("Unit 5", max_length=50, blank=True)
	
	ref = models.CharField("Reference", max_length=25)
	temp = models.CharField("Temperature", max_length=10)
	time = models.CharField("Time", max_length=10) ###
	pH = models.CharField("pH", max_length=5)
	
	#Yes/No/? Fields:
	slow_cool = models.CharField("Slow Cool", max_length=10)
	leak = models.CharField("Leak", max_length=10)
	outcome = models.CharField("Outcome", max_length=1)
	purity = models.CharField("Purity", max_length=1)
	
	notes = models.CharField("Notes", max_length=200, blank=True)
	
	#Self-assigning Fields
	user = models.ForeignKey(User, unique=False)
	lab_group = models.ForeignKey(Lab_Group, unique=False)
	creation_time = models.CharField("Created", max_length=26, null=True, blank=True)
	
	def __unicode__(self):
		return "{} -- (LAB: {})".format(self.ref, self.lab_group.lab_title)
	#def save(self, *args, **kwargs):
		##Set the self-assigning fields:
		#setattr(new_entry, "creation_time", str(datetime.datetime.now()))
		#super(Data, self).save(*args, **kwargs)
	
def collect_CG_entries(lab_group, overwrite=False):
	compound_guide = cache.get("{}|COMPOUNDGUIDE".format(lab_group.lab_title))
	if not compound_guide or overwrite:
		compound_guide = CompoundEntry.objects.filter(lab_group=lab_group).order_by("abbrev")
		cache.set("{}|COMPOUNDGUIDE".format(lab_group.lab_title), list(compound_guide))
	return compound_guide

def collect_CG_name_pairs(lab_group, overwrite=False):
	pairs = cache.get("{}|COMPOUNDGUIDE|NAMEPAIRS".format(lab_group.lab_title))
	if not pairs or overwrite:
		compound_guide = collect_CG_entries(lab_group)
		pairs = {entry.abbrev: entry.compound for entry in compound_guide}
		cache.set("{}|COMPOUNDGUIDE|NAMEPAIRS".format(lab_group.lab_title), pairs)
	return pairs

def validate_name(abbrev_to_check, lab_group): ###Ultimately in validation.py?
	#Get the cached set of abbreviations.
	abbrevs = collect_CG_name_pairs(lab_group)
	return abbrev_to_check in abbrevs
		
#Add specified entries to a datum. Assume fields are present, safe, and clean.### NEEDED?
def create_data_entry(user, **kwargs): ###Not re-read yet.
	try:
		new_entry = Data()
		#Set the self-assigning fields:
		setattr(new_entry, "creation_time", str(datetime.datetime.now()))
		setattr(new_entry, "user", user)
		setattr(new_entry, "lab_group", user.get_profile().lab_group)
		
		#Validate field names
		field_vals = kwargs.items()
		
		fields_left = get_data_field_names()
		for field_pair in field_vals:
			fields_left.remove(field_pair[0])
		assert len(field_vals) == len(get_data_field_names()) ###SLOW?

		#Set the non-user field values.
		for (field, value) in field_vals: #Assume data passed to the function is clean.
			setattr(new_entry, field, value)
		new_entry.save()
	except Exception as e:
		raise Exception("Data construction failed!")
		
def get_data_field_names(verbose = False):
	fields_to_ignore = {u"id","user","lab_group", "creation_time"} ###Auto-populate?
	dirty_fields = [field for field in Data._meta.fields]
	
	#Ignore any field that is in fields_to_ignore.
	clean_fields = []
	for field in dirty_fields:
		if field.name not in fields_to_ignore:
			#Return either the verbose names or the non-verbose names.
			if verbose:
				clean_fields += [field.verbose_name] ###Make verbose names pretty
			else:
				clean_fields += [field.name]
	
	return clean_fields
	
class DataEntryForm(ModelForm):
	#Define the style and other attributes for each field.
	reactant_1 = CharField(widget=TextInput(
		attrs={'class':'form_text autocomplete_reactant',
		"title":"Enter the name of the reactant."}))
	quantity_1 = CharField(label="Quantity", widget=TextInput(
		attrs={'class':'form_text form_text_short', 'placeholder':'Amount',
		"title":"Enter the mass of Reactant 1."}))
	unit_1 = ChoiceField(choices = UNIT_CHOICES, widget=Select(
		attrs={'class':'form_text dropDownMenu',
		"title":"Is the quantity a mass or volume?"}))
	reactant_2 = CharField(widget=TextInput(
		attrs={'class':'form_text autocomplete_reactant',
		"title":"Enter the name of the reactant."}))
	quantity_2 = CharField(label="Quantity", widget=TextInput(
		attrs={'class':'form_text form_text_short', 'placeholder':'Amount',
		"title":"Enter the mass of Reactant 2."}))
	unit_2 = ChoiceField(choices = UNIT_CHOICES, widget=Select(
		attrs={'class':'form_text dropDownMenu',
		"title":"Is the quantity a mass or volume?"}))
	reactant_3 = CharField(required=False,
		widget=TextInput(attrs={'class':'form_text autocomplete_reactant',
		"title":"Enter the name of the reactant."}))
	quantity_3 = CharField(required=False,
		label="Quantity", widget=TextInput(
		attrs={'class':'form_text form_text_short', 'placeholder':'Amount',
		"title":"Enter the mass of Reactant 3."}))
	unit_3 = ChoiceField(choices = UNIT_CHOICES, widget=Select(
		attrs={'class':'form_text dropDownMenu',
		"title":"Is the quantity a mass or volume?"}))
	reactant_4 = CharField(required=False,
		widget=TextInput(attrs={'class':'form_text autocomplete_reactant',
		"title":"Enter the name of the reactant."}))
	quantity_4 = CharField(required=False,
		label="Quantity", widget=TextInput(
		attrs={'class':'form_text form_text_short', 'placeholder':'Amount',
		"title":"Enter the mass of Reactant 4."}))
	unit_4 = ChoiceField(choices = UNIT_CHOICES, widget=Select(
		attrs={'class':'form_text dropDownMenu',
		"title":"Is the quantity a mass or volume?"}))
	reactant_5 = CharField(required=False,
		widget=TextInput(attrs={'class':'form_text autocomplete_reactant',
		"title":"Enter the name of the reactant."}))
	quantity_5 = CharField(required=False,
		label="Quantity", widget=TextInput(
		attrs={'class':'form_text form_text_short', 'placeholder':'Amount',
		"title":"Enter the mass of Reactant 5."}))
	unit_5 = ChoiceField(choices = UNIT_CHOICES, widget=Select(
		attrs={'class':'form_text dropDownMenu',
		"title":"Is the quantity a mass or volume?"}))
	ref = CharField(label="Ref.", widget=TextInput(
		attrs={'class':'form_text form_text_short',
		"title":"The lab notebook and page number where the data can be found."}))
	temp = CharField(label="Temp.", widget=TextInput(
		attrs={'class':'form_text form_text_short', 'placeholder':'Celsius',
		"title":"The temperature at which the reaction took place."}))
	time = CharField(widget=TextInput(
		attrs={'class':'form_text form_text_short', 'placeholder':'Hours',
		"title":"How long the reaction was allowed to occur."})) ###
	pH = CharField(label="pH", widget=TextInput(
		attrs={'class':'form_text form_text_short', 'placeholder':'0 - 14',
		"title":"The pH at which the reaction occurred."}))
	slow_cool = ChoiceField(label="Slow Cool", choices = BOOL_CHOICES, 
		widget=Select(attrs={'class':'form_text dropDownMenu',
		"title":"Was the reaction allowed to slow-cool?"}))
	leak = ChoiceField(choices = BOOL_CHOICES, widget=Select(
		attrs={'class':'form_text dropDownMenu',
		"title":"Was a leak present during the reaction?"}))
	outcome = ChoiceField(choices = OUTCOME_CHOICES, widget=Select(
		attrs={'class':'form_text dropDownMenu',
		"title":"0: No Data Available <br/> 1: No Solid<br/> 2: Noncrystalline/Brown<br/>3: Powder/Crystallites<br/>4: Large Single Crystals"}))
	purity = ChoiceField(choices = PURITY_CHOICES, widget=Select(
		attrs={'class':'form_text dropDownMenu',
		"title":"0: No Data Available<br/> 1: Multiphase<br/> 2: Single Phase"}))
	notes = CharField(required = False, widget=TextInput(
		attrs={'class':'form_text form_text_long',
		"title":"Additional notes about the reaction."}))
	
	class Meta:
		model = Data
		exclude = ("user","lab_group", "creation_time")

	def __init__(self, user=None, *args, **kwargs):
		###http://stackoverflow.com/questions/1202839/get-request-data-in-django-form
		super(DataEntryForm, self).__init__(*args, **kwargs)
		
		if user:
			self.user = user
			self.lab_group = user.get_profile().lab_group
		self.creation_time = str(datetime.datetime.now())
		
	def save(self, commit=True):
		datum = super(DataEntryForm, self).save(commit=False)
		datum.user = self.user
		datum.lab_group = self.lab_group
		datum.creation_time = self.creation_time
		if commit:
			datum.save()
		return datum
		
		
	#Clean All of the Data (IF FIELDS ARE ADDED, THEY MUST BE CLEANED HERE)
	def clean(self):
		
		#Initialize the variables needed for the cleansing process.
		dirty_data = super(DataEntryForm, self).clean() #Get the available raw (dirty) data
		clean_data = {} #Keep track of cleaned fields
		bad_data = set() #Keep track of fields that already include errors:
		
		#Add the user information to the clean data package:
		clean_data["lab_group"] = self.lab_group
		clean_data["user"] = self.user
		clean_data["creation_time"] = self.creation_time
		
		fields = get_data_field_names()
		
		#Gather the "coupled" fields (ie, the fields ending in a similar number) 
		field_groups = [[] for _ in range(5)]
		for field in fields:
			if field[-1].isdigit():
				field_groups[int(field[-1])-1] += [field]
		
		not_required = { ###Auto-generate?
			"reactant_3", "quantity_3", "unit_3", 
			"reactant_4", "quantity_4", "unit_4",
			"reactant_5", "quantity_5", "unit_5",
			"notes"
		}
		
		#Make sure all fields are available:
		#	(Skip checking for missing dirty_data if possible.)
		if len(dirty_data) != len(fields):
			for field in fields:
				try:
					dirty_data[field]	
				except: #At this point, the datum is not available. 
					if field in not_required: #Ie, if a field is required...
						dirty_data[field] = "?" #The datum was not required and nothing was entered.
					else:
						bad_data.add(field) #Remember that the data is bad.
						
		#Check that all grouped data is present if a group is "used."
		for field_group in field_groups:
			group_used = False
			for field in field_group:
				#Don't check bad data.
				if field in bad_data: 
					continue
				#Most units should be auto-completed, so ignore if units exist and nothing else does.
				elif field[:-2] == "unit" and dirty_data[field]!="":
					continue
				elif dirty_data[field] != "":
					group_used = True
				elif group_used:
					#A field is empty, but the group is "used" -- so raise an error.
					bad_data.add(field)
					self._errors[field] = self.error_class(
						["Datum is missing for reaction!"]
					)
				#Else, don't do anything. ###Verify the datum here?
		
		#Grouped fields	
		for field in fields:
			#If data is already bad, don't attempt to validate it.
			if field in bad_data:continue
			
			#If data is empty and not required, don't validate it. 
			if dirty_data[field] == "" and field in not_required: 
				clean_data[field] = ""
				continue
			
			#Make sure each reactant name is valid.
			if field[:-2]=="reactant":
				try:
					dirty_reactant = str(dirty_data[field])
					assert(validate_name(dirty_reactant, clean_data["lab_group"]))
					clean_data[field] = dirty_reactant #Add the filtered value to the clean values dict.
				except:
					self._errors[field] = self.error_class(
						["Reactant not in compound guide! {}".format(e)])
					bad_data.add(field)
			
			#Make sure each mass is a number.
			elif field[:-2]=="quantity":
				try:
					dirty_quantity = float(dirty_data[field])
					assert(quick_validation(field, dirty_quantity))
					clean_data[field] = dirty_quantity #Add the filtered mass to clean_data 
				except:
					self._errors[field] = self.error_class(
						["Quantity must be between {} and {}.".format(quantity_range[0], quantity_range[1])]) ###Remove range limit?
					bad_data.add(field)
					
			elif field[:-2]=="unit":
				try:
					dirty_unit = str(dirty_data[field])
					assert(quick_validation(field, dirty_unit))
					clean_data[field] = dirty_unit  
				except:
					self._errors[field] = self.error_class(
						["Unit must be mass (\"g\") or volume (\"mL\"/\\\"d\"rops)."])
					bad_data.add(field)

			#Range-dependent fields.
			elif field in {"pH", "temp", "time",  "outcome", "purity"}:
				try:
					dirty_datum = int(dirty_data[field])
					assert(quick_validation(field,dirty_datum))
					clean_data[field] = dirty_datum 
				except:
					#Get the associated field range (Note: each field in this if-statement is assumed to have a range)
					field_range = eval(field+"_range")
					
					self._errors[field] = self.error_class(
						["{} must be a number between {} and {}.".format(field, field_range[0], field_range[1])])
					bad_data.add(field)		
			
			#"Yes" or "No" fields.
			elif field in {"slow_cool","leak"}:
				try:
					#It is faster not to quick_validate booleans and skip to conversions.
					dirty_datum = str(dirty_data[field]).lower()
					if dirty_datum in {"yes","y","no","n","?"}:
						clean_data[field]  = dirty_datum
					else:
						raise Exception
				except:
					self._errors[field] = self.error_class(
						["{} must be a \"yes\" or \"no\" answer.".format(field)])
					bad_data.add(field)
			
			#Text fields.
			elif field in {"ref","notes"}:
				try:
					dirty_datum = str(dirty_data[field])
					assert(quick_validation(field, dirty_datum))
					clean_data[field] = dirty_datum
				except:
					#Get the associated field range (Note: each field in this if-statement is assumed to have a range)
					field_range = eval(field+"_range")
					
					self._errors[field] = self.error_class(
						["{} cannot exceed {} characters.".format(field, field_range[1])])
					bad_data.add(field)
					
		return clean_data
		
