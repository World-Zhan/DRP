from retrievalFunctions import *

   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
   # # # # # # # # # # # # #  CG_calculations  # # # # # # # # # # # # # # # #
   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
   # # # # # # # # # # # # #  Recommendations  # # # # # # # # # # # # # # # #
   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

#Organize the reactants into sublists: [[reactant, quantity, unit], ...]
def partition_reactant_fields(lst):
 num_fields = CONFIG.fields_per_reactant
 total_fields = num_fields * CONFIG.num_reactants
 #Sort the <total_fields> elements of lst into sublists of <num_fields> elements each
 reaction = []
 reactant = []
 for (datum, i) in zip(lst, xrange(total_fields)):
  if i%num_fields==0 and i!=0:
   reaction.append(reactant)
   reactant = [datum] 
  else:
   reactant.append(datum)
 reaction.append(reactant)
 return reaction
 
#Apply the headings to the variables in the list.
def get_vars_from_list(lst):
 verbose_headers = get_model_field_names(verbose=True, model="Data")[16:]
 info = [[i, j] for (i,j) in zip(verbose_headers, lst)]
 return info 

#Creates the Recommendation entry, but does not store it in database.
def field_list_to_Recommendation(lab_group, lst, in_bulk=False):
 try:
  new_rec = Recommendation()
  #Set the self-assigning fields:
  setattr(new_rec, "lab_group", lab_group)
  setattr(new_rec, "score", float(lst[0]))

  #Set the non-user field values.
  fields = get_model_field_names(model="Recommendation")
  for (field, value) in zip(fields, lst[2][1:]): #Ignore the reference field.
   #Translate Booleans into Boolean values.
   if value=="yes":
    value=True
   if value=="no":
    value=False
   setattr(new_rec, field, value)
  return new_rec
   
  new_rec.atoms = "".join(get_atom_set_from_abbrevs(lab_group, get_abbrevs_from_reaction(new_rec)))
 
  if not in_bulk:
    new_rec.date = str(datetime.datetime.now())

  return new_rec
 except Exception as e:
  raise Exception("Recommendation construction failed: {}".format(e))

def store_new_Recommendation_list(lab_group, list_of_recommendations, version_notes = ""):
 lab_group = get_Lab_Group(lab_group)
 
 call_time = str(datetime.datetime.now())
 
 #Store the information for this "Version" of the Recommendation model.
 new_version = Model_Version()
 new_version.model_type = "Recommendation"
 new_version.date = call_time
 new_version.notes = version_notes
 new_version.lab_group = lab_group
 new_version.save()

 #Store the actual Recommendation entries.
 num_success = 0
 count = 0
 for i in list_of_recommendations:
  count += 1
  try:
   new_rec = field_list_to_Recommendation(lab_group, i, in_bulk=True)
   new_rec.date = call_time
   new_rec.model_version = new_version
   new_rec.save() #Store this recommendation in the database
   num_success += 1
  except Exception as e:
    print "Recommendation {} could not be constructed: {}".format(count, e)
 
 print "Finished creating and storing {} of {} items!.".format(num_success, count)