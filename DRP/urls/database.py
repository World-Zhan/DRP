'''A module containing urls for the database (reactions, compound guide) components of DRP'''

from django.conf.urls import url
import DRP.views

urls = [
  url('^(?P<filetype>.csv|.html|.arff)?$', DRP.views.reaction.ListPerformedReactions.as_view(), name='reactionlist_typed'),
  url('^/$', DRP.views.reaction.ListPerformedReactions.as_view(), name='reactionlist'),
  url('^/add.html', DRP.views.reaction.createReaction, name='newReaction'),
  url('^/compound_quantities/reaction_(?P<rxn_id>\d+).html', DRP.views.reaction.addCompoundDetails, name="addCompoundDetails"),
  url('^/edit_(?P<pk>\d+).html', DRP.views.reaction.editReaction, name='editReaction'),
  url('^/delete$', DRP.views.reaction.deleteReaction, name='deleteReaction'),
  url('^/invalidate$', DRP.views.reaction.invalidateReaction, name='invalidateReaction'),
  url('^/import/apiv1/(?P<component>[^//]*).xml', DRP.views.api1),
  url('^/select_viewing_group.html', DRP.views.selectGroup, name='selectGroup'),
  url('^/compoundguide(?P<filetype>.csv|.html|.arff|/)$', DRP.views.compound.ListCompound.as_view(), name='compoundguide'),
  url('^/compoundguide/search(?P<filetype>.html|.csv|.arff)$', DRP.views.compound.ListCompound.as_view(), name='compoundSearch'),
  url('^/compoundguide/advanced_search(?P<filetype>.html|.csv|.arff)$', DRP.views.compound.AdvancedCompoundSearchView.as_view(), name='advCompoundSearch'),
  url('^/compoundguide/add.html$', DRP.views.compound.CreateCompound.as_view(), name='newCompound'),
  url('^/compoundguide/delete$', DRP.views.compound.deleteCompound, name='deleteCompound'),
  url('^/compoundguide/edit_(?P<pk>\d+).html', DRP.views.compound.EditCompound.as_view(), name='editCompound'),
  url('^/compoundguide/upload.html', DRP.views.compound.uploadCompound, name='uploadcompoundcsv'),
  url('^/jsonapi/boolrxndescriptor.json', DRP.views.descriptors.BoolRxnDescriptor.as_view(), name='boolrxndescriptor'),
  url('^/jsonapi/catrxndescriptor.json', DRP.views.descriptors.CatRxnDescriptor.as_view(), name='catrxndescriptor'),
  url('^/jsonapi/numrxndescriptor.json', DRP.views.descriptors.NumRxnDescriptor.as_view(), name='numrxndescriptor'),
  url('^/jsonapi/ordrxndescriptor.json', DRP.views.descriptors.OrdRxnDescriptor.as_view(), name='ordrxndescriptor') 
]
