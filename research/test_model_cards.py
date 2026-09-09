import unittest
from audit_model_cards import summarize


class ModelCardTests(unittest.TestCase):
    def info(self):
        return {'id': 'author/model', 'sha': 'a' * 40, 'siblings': []}

    def test_missing_size_is_unknown_and_never_runtime_ready(self):
        result = summarize(self.info(), 'author/model')
        self.assertIsNone(result['parameter_count_api'])
        self.assertFalse(result['inference_verified'])
        self.assertFalse(result['publication_approved'])
        self.assertFalse(result['weights_downloaded'])

    def test_wrong_identity_rejected(self):
        with self.assertRaises(ValueError):
            summarize(self.info(), 'other/model')

    def test_moving_or_missing_revision_rejected(self):
        for revision in (None, 'main', '../README.md'):
            info = self.info()
            info['sha'] = revision
            with self.assertRaises(ValueError):
                summarize(info, 'author/model')

    def test_declared_size_and_files_are_not_ram_estimates(self):
        info = self.info()
        info['safetensors'] = {'total': 1000}
        info['siblings'] = [{'rfilename': 'model.safetensors', 'size': 5000}]
        result = summarize(info, 'author/model')
        self.assertEqual(result['parameter_count_api'], 1000)
        self.assertEqual(result['files'][0]['bytes'], 5000)
        self.assertNotIn('ram', result)


if __name__ == '__main__':
    unittest.main()
