import unittest

from sportsbetlang.lang.bytecode import BytecodeCompiler, BytecodeVM
from sportsbetlang.lang.lexer import Lexer
from sportsbetlang.lang.parser import Parser


class TestBytecodeVM(unittest.TestCase):
    def test_numeric_program(self):
        src = "let x = 10\nlet y = x * 2\ny + 5\n"
        ast = Parser(Lexer(src).tokenize(), src).parse()
        code = BytecodeCompiler().compile(ast)
        vm = BytecodeVM()
        vm.run(code)
        self.assertEqual(vm.env["y"], 20)


if __name__ == "__main__":
    unittest.main()
