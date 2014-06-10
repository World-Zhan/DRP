
import sys, os
django_dir = os.path.dirname(os.path.realpath(__file__)).split("DRP")[0]
django_path = "{}/DRP".format(django_dir)
if django_path not in sys.path:
  sys.path.append("{}/DRP".format(django_dir))

os.environ['DJANGO_SETTINGS_MODULE'] = 'DRP.settings'

from DRP.settings import BASE_DIR
import load_cg,json

def load(lab_group=None):
	from DRP.models import get_good_rxns
	rxns = fix_abbrevs(get_good_rxns(lab_group=lab_group)[1:])
	return rxns
	

def fix_abbrevs(rxns):
	abbrev_map, compound_set = get_abbrev_map()
	abbrev_map[''] = ''
	idxes = [1,4,7,10,13]
	for i in range(len(rxns)):
		for idx in idxes:
			if rxns[i][idx] in abbrev_map:
				rxns[i][idx] = abbrev_map[rxns[i][idx]]
	return rxns


def get_abbrev_map():
	from DRP.models import CompoundEntry as c 

 	entries = c.objects.all()
	abbrev_map = dict()
	compound_set = set()
	for e in entries:
		abbrev_map[e.abbrev] = e.compound
		compound_set.add(e.compound)
	return abbrev_map, compound_set


def get_feature_vectors(lab_group=None, cg = None, ml_convert = None, keys = None):
	raw = load(lab_group)
	return convert_to_feature_vectors(raw,cg, ml_convert, keys = keys)

def convert_to_feature_vectors(raw, cg = None, ml_convert = None, keys = None):
	if not cg:
		cg = load_cg.get_cg()
	if not ml_convert:
		ml_convert = json.load(open("{}/DRP/model_building/mlConvert.json".format(BASE_DIR)))
	import parse_rxn

	transformed = []
	failed = 0
	keys = []
	for row in raw:
		try:
			transformed.append(parse_rxn.parse_rxn(row, cg, ml_convert))
			keys.append(create_key(row))
		except Exception as e:
			failed += 1
			print e
	print "{0} failed out of {1} total".format(failed, len(raw))
	remove_XXX(transformed)

	for r in transformed:
		del r[-2]
	
	if keys:
		return transformed, keys
	return transformed

def create_key(line):
	print line
	key = [line[0], line[3], line[6], line[9], line[12]]
	key = [r for r in key if r.lower() != 'water' and r != ""]
	key.sort()
	return tuple(key)

	
def get_feature_vectors_by_triple(lab_group=None, cg = None, ml_convert = None):
	import parse_rxn
	if not cg:
		cg = load_cg.get_cg()
	if not ml_convert:
		ml_convert = json.load(open("{}/DRP/model_building/mlConvert.json".format(BASE_DIR)))
	raw = load(lab_group)
	transformed = []

	triple_to_rxn_list = dict()

	for rxn in raw:
		try:
			triple = rxn_to_triple(rxn, cg)
		except Exception as e:
			print "Ignoring for triple: {0}".format(e)
			continue
		if triple not in triple_to_rxn_list:
			triple_to_rxn_list[triple] = []
		triple_to_rxn_list[triple].append(rxn)
	failed = 0
	for triple in triple_to_rxn_list:
		rxn_list = triple_to_rxn_list[triple]
		transformed = []
		for row in rxn_list:
			try:
				transformed.append(parse_rxn.parse_rxn(row, cg, ml_convert))
			except Exception as e:
				failed += 1
		remove_XXX(transformed)
		triple_to_rxn_list[triple] = transformed
	print "{0} failed out of {1} total".format(failed, len(raw))
	return triple_to_rxn_list

def collapse_triples(dataset):
	unknown = []
	del_triples = []
	for triple in dataset:
		if len(dataset[triple]) < 6:
			unknown += dataset[triple]
			del_triples.append(triple)
	for triple in del_triples:
		del dataset[triple]

	dataset['unknown'] = unknown


def rxn_to_triple(rxn, cg):
	r = rxn
	compounds = filter(lambda x: x != 'water' and x != '', [r[1], r[4], r[7], r[10], r[13]])
	for compound in compounds:
		if compound not in cg:
			raise Exception("Unknown compound: {0}".format(compound))
	return tuple(sorted(compounds))
	
	
	
def remove_XXX(rows):
	import rxn_calculator
	dist = 0
	end = rxn_calculator.headers.index('outcome') + 1
	for hdr in rxn_calculator.headers:
		if "XXX" in hdr:
			dist += 1
	for i in range(len(rows)):
		rows[i] = rows[i][dist:end]
