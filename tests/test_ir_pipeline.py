import unittest

from sportsbetlang.lang.ir import build_ir, has_definitely_infinite_loop
from sportsbetlang.lang.lexer import Lexer
from sportsbetlang.lang.parser import Parser


class TestIRPipeline(unittest.TestCase):
    def parse(self, source: str):
        return Parser(Lexer(source).tokenize(), source).parse()

    def test_constant_folding(self):
        ir = build_ir(self.parse("let x = 1 + 2 * 3\nx"))
        text = str(ir.statements[0])
        self.assertIn("value=NumberLiteral(value=7", text)

    def test_unreachable_and_unused(self):
        src = "func f() {\n  let tmp = 10\n  return 1\n  let never = 2\n}\n"
        ir = build_ir(self.parse(src))
        joined = "\n".join(ir.warnings)
        self.assertIn("Unused variable 'tmp'", joined)
        self.assertIn("Unreachable statements detected", joined)

    def test_infinite_loop_precheck(self):
        ir = build_ir(self.parse("while true {\n}\n"))
        self.assertTrue(has_definitely_infinite_loop(ir))


if __name__ == "__main__":
    unittest.main()
