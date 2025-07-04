import unittest
from ..core.args_parser import Args_parser as parser


class TestArgParser(unittest.TestCase):

    def test_symbols(self):
        args = parser.args_parse(["-s='LKOH'"])
        self.assertEqual(args.symbols, ['LKOH'])
        args = parser.args_parse(["-s='LKOH' 'TATN'"])
        self.assertEqual(args.symbols, ['LKOH', 'TATN'])
        args = parser.args_parse(["-s='LKOH', 'TATN'"])
        self.assertEqual(args.symbols, ['LKOH'])
        args = parser.args_parse(["-s=LKOH"])
        self.assertEqual(args.symbols, ['LKOH'])


if __name__ == '__main__':
    unittest.main()
