"""
SportsBetLang JIT Compiler - Emits and executes LLVM IR for numeric workloads.
"""

from __future__ import annotations

from dataclasses import dataclass
import ctypes
import importlib.util
from typing import Dict, Optional

from sportsbetlang.core.lexer import TokenType
from sportsbetlang.core.parser import (
    ASTNode,
    Assignment,
    BinaryOp,
    BooleanLiteral,
    Identifier,
    NumberLiteral,
    Program,
    ReturnStatement,
    UnaryOp,
)

_LLVM_AVAILABLE = importlib.util.find_spec("llvmlite") is not None
if _LLVM_AVAILABLE:
    from llvmlite import binding as llvm
    from llvmlite import ir
else:  # pragma: no cover - optional dependency
    llvm = None
    ir = None


@dataclass
class JITCompilationResult:
    """Container for LLVM IR output and native function pointer."""
    llvm_ir: str
    function_pointer: int


class JITCompilationError(RuntimeError):
    """Raised when the JIT compiler encounters unsupported syntax."""


class JITCompiler:
    """Compile SportsBetLang numeric programs to LLVM IR and execute them."""

    def __init__(self):
        if llvm is None or ir is None:
            raise RuntimeError(
                "LLVM JIT unavailable. Install llvmlite to enable JIT compilation."
            )
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        self._engine = self._create_execution_engine()

    def compile(self, program: Program) -> JITCompilationResult:
        module, func = self._build_module(program)
        llvm_ir = str(module)
        self._add_module(module)
        func_ptr = self._engine.get_function_address(func.name)
        return JITCompilationResult(llvm_ir=llvm_ir, function_pointer=func_ptr)

    def compile_to_ir(self, program: Program) -> str:
        module, _ = self._build_module(program)
        return str(module)

    def execute(self, program: Program) -> float:
        result = self.compile(program)
        func_ptr = result.function_pointer
        func = ctypes.cast(func_ptr, ctypes.CFUNCTYPE(ctypes.c_double))
        return float(func())

    def _create_execution_engine(self):
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()
        backing_mod = llvm.parse_assembly("")
        return llvm.create_mcjit_compiler(backing_mod, target_machine)

    def _add_module(self, module):
        llvm_module = llvm.parse_assembly(str(module))
        llvm_module.verify()
        self._engine.add_module(llvm_module)
        self._engine.finalize_object()
        self._engine.run_static_constructors()

    def _build_module(self, program: Program):
        module = ir.Module(name="sportsbetlang_jit")
        func_type = ir.FunctionType(ir.DoubleType(), [])
        function = ir.Function(module, func_type, name="sbl_main")
        entry_block = function.append_basic_block(name="entry")
        builder = ir.IRBuilder(entry_block)
        env: Dict[str, ir.AllocaInstr] = {}
        last_value: Optional[ir.Value] = None

        for statement in program.statements:
            last_value = self._emit_statement(builder, env, statement)

        if last_value is None:
            last_value = ir.Constant(ir.DoubleType(), 0.0)
        if not builder.block.is_terminated:
            builder.ret(self._coerce_to_double(builder, last_value))
        return module, function

    def _emit_statement(self, builder: ir.IRBuilder, env: Dict[str, ir.AllocaInstr], node: ASTNode):
        if isinstance(node, Assignment):
            value = self._emit_expression(builder, env, node.value)
            if node.name not in env:
                env[node.name] = self._create_entry_block_alloca(builder, node.name)
            builder.store(self._coerce_to_double(builder, value), env[node.name])
            return value
        if isinstance(node, ReturnStatement):
            value = self._emit_expression(builder, env, node.value) if node.value else ir.Constant(ir.DoubleType(), 0.0)
            builder.ret(self._coerce_to_double(builder, value))
            return value
        return self._emit_expression(builder, env, node)

    def _emit_expression(self, builder: ir.IRBuilder, env: Dict[str, ir.AllocaInstr], node: ASTNode):
        if isinstance(node, NumberLiteral):
            return ir.Constant(ir.DoubleType(), node.value)
        if isinstance(node, BooleanLiteral):
            return ir.Constant(ir.IntType(1), 1 if node.value else 0)
        if isinstance(node, Identifier):
            if node.name not in env:
                raise JITCompilationError(f"Undefined variable '{node.name}' in JIT context.")
            return builder.load(env[node.name], name=f"{node.name}_value")
        if isinstance(node, UnaryOp):
            operand = self._emit_expression(builder, env, node.operand)
            if node.operator == TokenType.MINUS:
                return builder.fsub(ir.Constant(ir.DoubleType(), 0.0), self._coerce_to_double(builder, operand))
            if node.operator == TokenType.NOT:
                operand_bool = self._coerce_to_bool(builder, operand)
                return builder.xor(operand_bool, ir.Constant(ir.IntType(1), 1))
            raise JITCompilationError(f"Unsupported unary operator '{node.operator.name}'.")
        if isinstance(node, BinaryOp):
            left = self._emit_expression(builder, env, node.left)
            right = self._emit_expression(builder, env, node.right)
            return self._emit_binary_op(builder, node.operator, left, right)
        raise JITCompilationError(f"Unsupported node type for JIT: {type(node).__name__}.")

    def _emit_binary_op(self, builder: ir.IRBuilder, operator: TokenType, left: ir.Value, right: ir.Value):
        left_val = self._coerce_to_double(builder, left)
        right_val = self._coerce_to_double(builder, right)
        if operator == TokenType.PLUS:
            return builder.fadd(left_val, right_val)
        if operator == TokenType.MINUS:
            return builder.fsub(left_val, right_val)
        if operator == TokenType.MULTIPLY:
            return builder.fmul(left_val, right_val)
        if operator == TokenType.DIVIDE:
            return builder.fdiv(left_val, right_val)
        if operator == TokenType.MODULO:
            return builder.frem(left_val, right_val)
        if operator == TokenType.EQUAL:
            return builder.fcmp_ordered("==", left_val, right_val)
        if operator == TokenType.NOT_EQUAL:
            return builder.fcmp_ordered("!=", left_val, right_val)
        if operator == TokenType.LESS_THAN:
            return builder.fcmp_ordered("<", left_val, right_val)
        if operator == TokenType.GREATER_THAN:
            return builder.fcmp_ordered(">", left_val, right_val)
        if operator == TokenType.LESS_EQUAL:
            return builder.fcmp_ordered("<=", left_val, right_val)
        if operator == TokenType.GREATER_EQUAL:
            return builder.fcmp_ordered(">=", left_val, right_val)
        if operator == TokenType.AND:
            return builder.and_(self._coerce_to_bool(builder, left), self._coerce_to_bool(builder, right))
        if operator == TokenType.OR:
            return builder.or_(self._coerce_to_bool(builder, left), self._coerce_to_bool(builder, right))
        raise JITCompilationError(f"Unsupported binary operator '{operator.name}'.")

    def _coerce_to_double(self, builder: ir.IRBuilder, value: ir.Value) -> ir.Value:
        if isinstance(value.type, ir.DoubleType):
            return value
        if isinstance(value.type, ir.IntType) and value.type.width == 1:
            return builder.uitofp(value, ir.DoubleType())
        raise JITCompilationError(f"Unsupported value type for numeric coercion: {value.type}.")

    def _coerce_to_bool(self, builder: ir.IRBuilder, value: ir.Value) -> ir.Value:
        if isinstance(value.type, ir.IntType) and value.type.width == 1:
            return value
        if isinstance(value.type, ir.DoubleType):
            return builder.fcmp_ordered("!=", value, ir.Constant(ir.DoubleType(), 0.0))
        raise JITCompilationError(f"Unsupported value type for boolean coercion: {value.type}.")

    def _create_entry_block_alloca(self, builder: ir.IRBuilder, name: str) -> ir.AllocaInstr:
        entry_builder = ir.IRBuilder(builder.function.entry_basic_block)
        entry_builder.position_at_beginning(builder.function.entry_basic_block)
        return entry_builder.alloca(ir.DoubleType(), name=name)
