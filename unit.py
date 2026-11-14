from pathlib import Path
from lark import Lark
from lark.visitors import Interpreter
import sys

GRAMMAR = Path(__file__).parent / "Grammer" / "grammer.lark"

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class BreakSignal(Exception): pass
class ContinueSignal(Exception): pass

class ArrayObject:
    def __init__(self, elements): self.elements = elements if elements is not None else []
    def __getitem__(self, index): return self.elements[index]
    def __repr__(self): return f"[{', '.join(repr(e) for e in self.elements)}]"

class DictObject:
    def __init__(self, elements): self.elements = dict(elements)

    def get(self, key):
        if key not in self.elements:
            raise KeyError(f"Key '{key}' not registered!")
        return self.elements[key]

    def set(self, key, value):
        self.elements[key] = value
        return value
    
    def __repr__(self):
        items = [f"{repr(k)}: {repr(v)}" for k, v in self.elements]
        return f"{{{', '.join(items)}}}"

class FunctionObject:
    def __init__(self, name, param, block, closure):
        self.name = name
        self.param = param
        self.block = block
        self.closure = closure
    def __repr__(self): return f"<function {self.name}({', '.join(self.param)})>"

class Environment(Interpreter):
    def __init__(self, source_dir):
        super().__init__()
        self.env = {}
        self.source_dir = Path(source_dir).resolve()
        self.packages = set()

        terminal = sys.argv[1:] if len(sys.argv) > 1 else []
        self.env["@"] = ArrayObject(terminal)

    def start(self, tree):
        result = None
        for child in tree.children:
            result = self.visit(child)
        return result

    def unit(self, tree): return self.visit(tree.children[0])
    def args(self, tree): return self.visit(tree.children[0])
    def expr(self, tree): return self.visit(tree.children[0])
    def number(self, tree): return int(tree.children[0])
    def string(self, tree): return str(tree.children[0])[1:-1]
    def boolean(self, tree): return str(tree.children[0]) == "true"
    def var(self, tree): return self.search(str(tree.children[0]))

    def search(self, name):
        if name not in self.env:
            raise NameError(f"Undefined '{name}' variable!")
        return self.env[name]

    def register(self, tree):
        name, value = tree.children
        value = self.visit(value)
        self.env[str(name)] = value
        return value

    def empty_value(self, tree):
        name = str(tree.children[0])
        self.env[name] = None
        return None

    def update(self, tree):
        name, value = tree.children
        value = self.visit(value)
        self.env[str(name)] = value
        return value

    def _compound(self, tree, operation):
        name, value = tree.children
        value = self.visit(value)
        self.env[str(name)] = operation(self.search(str(name)), value)
        return self.env[str(name)]

    def add_equal(self, tree): return self._compound(tree, lambda a, b: a + b)
    def min_equal(self, tree): return self._compound(tree, lambda a, b: a - b)
    def mul_equal(self, tree): return self._compound(tree, lambda a, b: a * b)
    def div_equal(self, tree): return self._compound(tree, lambda a, b: a / b)
    def domain_equal(self, tree): return self._compound(tree, lambda a, b: a ** b)

    def add(self, tree): return self.visit(tree.children[0]) + self.visit(tree.children[1])
    def sub(self, tree): return self.visit(tree.children[0]) - self.visit(tree.children[1])
    def mul(self, tree): return self.visit(tree.children[0]) * self.visit(tree.children[1])
    def div(self, tree): return self.visit(tree.children[0]) / self.visit(tree.children[1])
    def domain(self, tree): return self.visit(tree.children[0]) ** self.visit(tree.children[1])

    def d_equal(self, tree): return self.visit(tree.children[0]) == self.visit(tree.children[1])
    def n_equal(self, tree): return self.visit(tree.children[0]) != self.visit(tree.children[1])
    def less_than(self, tree): return self.visit(tree.children[0]) < self.visit(tree.children[1])
    def greater_than(self, tree): return self.visit(tree.children[0]) > self.visit(tree.children[1])
    def lt_equal(self, tree): return self.visit(tree.children[0]) <= self.visit(tree.children[1])
    def gt_equal(self, tree): return self.visit(tree.children[0]) >= self.visit(tree.children[1])
    def and_logic(self, tree): return bool(self.visit(tree.children[0])) and bool(self.visit(tree.children[1]))
    def or_logic(self, tree): return bool(self.visit(tree.children[0])) or bool(self.visit(tree.children[1]))
    def not_logic(self, tree): return not self.visit(tree.children[0])

    def array(self, tree):
        elements = [self.visit(child) for child in tree.children]
        return ArrayObject(elements)

    def pair(self, tree):
        key = str(tree.children[0])
        value = self.visit(tree.children[1])
        return key, value

    def dict(self, tree):
        pairs = {}
        for i in tree.children:
            k, v = self.visit(i)
            pairs[k] = v
        return DictObject(pairs)

    def let_array(self, tree):
        name, value = tree.children
        val = self.visit(value)
        self.env[str(name)] = val
        return val

    def arr_index(self, tree):
        name = str(tree.children[0])
        index = tree.children[1]

        array_index = self.visit(index)
        obj = self.search(name)

        if not isinstance(obj, ArrayObject): raise TypeError(f"Variable '{name}' isn't regular array!")
        return obj[array_index]

    def let_dict(self, tree):
        name, value = tree.children
        val = self.visit(value)
        self.env[str(name)] = val
        return val
    
    def obj_access(self, tree):
        name = str(tree.children[0])
        prop_name = str(tree.children[1])
        obj = self.search(name)

        if not isinstance(obj, DictObject): raise TypeError(f"Variable '{name}' isn't regular object!")
        return obj.get(prop_name)

    def obj_assignment(self, tree):
        name = str(tree.children[0])
        prop_name = str(tree.children[1])
        expr = tree.children[2]

        obj = self.search(name)
        if not isinstance(obj, DictObject): raise TypeError(f"Variable '{name}' isn't regular object!")

        val = self.visit(expr)
        return obj.set(prop_name, val)

    def arg_base(self, tree): return self.search("@")
    def arg_base_index(self, tree):
        index = int(tree.children[1])
        arr = self.search("@")

        if not isinstance(arr, ArrayObject): raise TypeError(f"Symbol '@' isn't a valid array!")
        return arr[index]

    def expr_stmt(self, tree): return self.visit(tree.children[0])
    def null_expr(self, tree): return None

    def echo_stmt(self, tree):
        value = [self.visit(i) for i in tree.children]
        print(*value)
        return value

    def return_stmt(self, tree):
        value = self.visit(tree.children[0])
        raise ReturnSignal(value)

    def if_stmt(self, tree):
        condition = self.visit(tree.children[0])
        if condition:
            return self.visit(tree.children[1])

    def block(self, tree):
        result = None
        for child in tree.children:
            result = self.visit(child)
        return result

    def for_stmt(self, tree):
        condition, body = tree.children
        result = None

        while self.visit(condition):
            try:
                result = self.visit(body)
            except ContinueSignal:
                continue
            except BreakSignal:
                break

        return result

    def break_stmt(self, tree): raise BreakSignal()
    def continue_stmt(self, tree): raise ContinueSignal()

    def import_stmt(self, tree):
        package = ".".join(map(str, tree.children[0].children))
        if package in self.packages: raise ImportError(f"Package {package} has already imported!")

        pkg_dir = self.source_dir.joinpath(*package.split("."))
        if not pkg_dir.is_dir(): raise ModuleNotFoundError(f"Package '{package}' not found!")

        file = sorted(pkg_dir.glob("*.own"))
        if not file: raise ImportError(f"Package '{package}' contains no source files!")

        self.packages.add(package)

        for i in file:
            source = i.read_text(encoding='utf-8')
            tree = parser.parse(source)
            self.visit(tree)

    def reg_func(self, tree):
        name = str(tree.children[0])
        param = tree.children[1]
        body = tree.children[2]

        params = []
        if param and hasattr(param, 'children'):
            node = param.children if hasattr(param, 'children') else [param]
            for i in node:
                if hasattr(i, 'children') and i.children:
                    params.append(str(i.children[0]))
                else:
                    params.append(str(i))

        func_obj = FunctionObject(name, param, body, self)
        self.env[name] = func_obj
        return func_obj

    def search_func(self, name):
        if name not in self.env: raise NameError(f"Function {name} not found!")
        obj = self.env[name]
        if not isinstance(obj, FunctionObject): raise TypeError(f"Variable {name} isn't regular function!")
        return obj

    def func_call(self, tree):
        name = str(tree.children[0])
        obj = self.search_func(name)

        exprs = tree.children[1:] if len(tree.children) > 1 else []
        values = [self.visit(args) for args in exprs]

        if len(values) != len(obj.param):
            raise TypeError(f"Function '{name}' expects {len(obj.param)} arguments, got {len(values)}!")

        local_env = Environment(self.source_dir)
        local_env.env = dict(obj.closure)

        for param_name, val in zip(obj.param, values):
            local_env.env[param_name] = val

        result = None
        try:
            local_env.visit(obj.block)
        except ReturnSignal as e:
            result = e.value

        return result
parser = Lark(
    GRAMMAR.read_text(),
    parser='lalr'
)