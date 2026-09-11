"""A missing human assessment must never become a positive quality result."""
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
import human_review as H

class Review(unittest.TestCase):
    def setUp(self):
        self.packet={'packet_id':'fixture','categories':['radovi'],'rows':[
            {'id':'a','kind':'news','prediction':{'category':'radovi','belgrade':True}},
            {'id':'b','kind':'mind','prediction':{'accepted':True}}]}
        self.labels={'packet_id':'fixture','reviewer':'Synthetic human fixture','reviewer_type':'human',
                     'independent_before_reveal':True,'rows':[]}

    def test_empty_labels_do_not_measure_accuracy_or_complete(self):
        result=H.score(self.packet,self.labels)
        self.assertEqual(result['state'],'partial')
        self.assertIsNone(result['metrics']['news_category']['agreement'])

    def test_model_cannot_supply_the_human_labels(self):
        self.labels['reviewer_type']='model'
        with self.assertRaises(ValueError):H.score(self.packet,self.labels)

    def test_unknown_duplicate_and_foreign_ids_are_refused(self):
        self.labels['packet_id']='other'
        with self.assertRaises(ValueError):H.score(self.packet,self.labels)
        self.labels['packet_id']='fixture';self.labels['rows']=[{'id':'missing'}]
        with self.assertRaises(ValueError):H.score(self.packet,self.labels)
        row={'id':'a','category':'radovi','belgrade':'yes'};self.labels['rows']=[row,row]
        with self.assertRaises(ValueError):H.score(self.packet,self.labels)

    def test_uncertainty_has_a_visible_denominator_and_false_accept_is_counted(self):
        self.labels['rows']=[{'id':'a','category':'uncertain','belgrade':'yes'},{'id':'b','supported':'no'}]
        result=H.score(self.packet,self.labels)
        self.assertEqual(result['state'],'complete')
        self.assertEqual(result['metrics']['news_category']['decidable'],0)
        self.assertEqual(result['metrics']['news_belgrade']['agreement'],1)
        self.assertEqual(result['metrics']['mind_gate']['false_accept'],1)
