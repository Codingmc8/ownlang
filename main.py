from pathlib import Path
from lark import Lark
from lark.visitors import Interpreter
import sys

GRAMMAR = Path(__file__).parent / "grammer.lark"

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class BreakSignal(Exception): pass
class ContinueSignal(Exception): pass

def format_val(v):
    if v is True: return "true"
    elif v is False: return "false"
    elif v is None: return "null"
    return repr(v)

class ArrayObject:
    def __init__(self, elements): self.elements = elements if elements is not None else []
    def __getitem__(self, index): return self.elements[index]

    def __repr__(self):
        items = []
        for e in self.elements:
            if isinstance(e, (ArrayObject, DictObject)): items.append(repr(e))
            elif e is True: items.append("true")
            elif e is False: items.append("false")
            elif e is None: items.append("null")
            else: items.append(repr(e))
        return f"[{', '.join(items)}]"

class DictObject:
    def __init__(self, elements): self.elements = dict(elements)

    def get(self, key):
        if key not in self.elements: raise KeyError(f"Key '{key}' not registered!")
        return self.elements[key]

    def set(self, key, value):
        self.elements[key] = value
        return value

    def __repr__(self):
        items = []
        for k, v in self.elements.items():
            if isinstance(v, (ArrayObject, DictObject)): val_str = repr(v)
            elif v is True: val_str = "true"
            elif v is False: val_str = "false"
            elif v is None: val_str = "null"
            else: val_str = repr(v)
            items.append(f"{repr(k)}: {val_str}")
        return f"{{{', '.join(items)}}}"

class FunctionObject:
    def __init__(self, name, param, block, closure):
        self.name = name
        self.param = param
        self.block = block
        self.closure = closure

    def __repr__(self): return f"<function {self.name}({', '.join(self.param)})>"

class PythonObject:
    def __init__(self, name, func):
        self.name = name
        self.func = func
    def __repr__(self): return f"<python-function {self.name}>"

class Environment(Interpreter):
    def __init__(self, source_dir, cli_args=None):
        super().__init__()
        self.env = {}
        self.source_dir = Path(source_dir).resolve()
        self.packages = set()

        terminal = cli_args if cli_args is not None else (sys.argv[2:] if len(sys.argv) > 2 else [])
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
        if name not in self.env: raise NameError(f"Undefined '{name}' variable!")
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
        if not isinstance(arr, ArrayObject): raise TypeError("Symbol '@' isn't a valid array!")
        return arr[index]

    def expr_stmt(self, tree): return self.visit(tree.children[0])
    def null_expr(self, tree): return None

    def echo_stmt(self, tree):
        values = [self.visit(i) for i in tree.children]
        formatted = []
        for v in values:
            if v is True: formatted.append("true")
            elif v is False: formatted.append("false")
            elif v is None: formatted.append("null")
            else: formatted.append(v)
        print(*formatted)
        return values

    def return_stmt(self, tree):
        value = self.visit(tree.children[0])
        raise ReturnSignal(value)

    def if_stmt(self, tree):
        condition = self.visit(tree.children[0])
        if condition: return self.visit(tree.children[1])
        elif len(tree.children) > 2: return self.visit(tree.children[2])
        return None

    def block(self, tree):
        result = None
        for child in tree.children: result = self.visit(child)
        return result

    def for_stmt(self, tree):
        condition, body = tree.children
        result = None
        while self.visit(condition):
            try: result = self.visit(body)
            except ContinueSignal: continue
            except BreakSignal: break
        return result

    def break_stmt(self, tree): raise BreakSignal()
    def continue_stmt(self, tree): raise ContinueSignal()

    def import_stmt(self, tree):
        package = ".".join(map(str, tree.children[0].children))
        if package in self.packages:
            return

        lib_dir = self.source_dir / "lib"
        if not lib_dir.exists():
            lib_dir = Path("lib").resolve()

        py_lib_file = lib_dir / f"{package.replace('.', '/')}.py"
        if py_lib_file.is_file():
            import importlib.util
            import sys

            spec = importlib.util.spec_from_file_location(f"lib.{package}", py_lib_file)
            py_mod = importlib.util.module_from_spec(spec)
            
            sys.modules[f"lib.{package}"] = py_mod
            spec.loader.exec_module(py_mod)
            self.packages.add(package)

            for attribute in dir(py_mod):
                attr_value = getattr(py_mod, attribute)
                if callable(attr_value) and getattr(attr_value, "__module__", None) == py_mod.__name__:
                    self.env[attribute] = PythonObject(attribute, attr_value)
            return

        pkg_dir = lib_dir.joinpath(*package.split("."))
        if not pkg_dir.is_dir():
            pkg_dir = self.source_dir.joinpath(*package.split("."))
            if not pkg_dir.is_dir():
                raise ModuleNotFoundError(f"Package '{package}' not found!")

        files = sorted(pkg_dir.glob("*.own"))
        if not files: raise ImportError(f"Package '{package}' contains no source files!")
        self.packages.add(package)

        for f in files:
            source = f.read_text(encoding='utf-8')
            tree = parser.parse(source)
            self.visit(tree)

    def reg_func(self, tree):
        name = str(tree.children[0])
        param = tree.children[1]
        body = tree.children[2]

        params = []
        if param and hasattr(param, "children"):
            for i in param.children:
                if i is not None: params.append(str(i))
        elif param is not None: params.append(str(param))

        func_obj = FunctionObject(name, params, body, self)
        self.env[name] = func_obj
        return func_obj

    def search_func(self, name):
        if name not in self.env: raise NameError(f"Function {name} not found!")
        obj = self.env[name]
        if not isinstance(obj, FunctionObject):
            raise TypeError(f"Variable {name} isn't regular function!")
        return obj

    def func_call(self, tree):
        name = str(tree.children[0])

        if name in self.env and isinstance(self.env[name], PythonObject):
            py_obj = self.env[name]
            exprs = tree.children[1:] if len(tree.children) > 1 else []
            values = [self.visit(args) for args in exprs if args is not None]
            return py_obj.func(*values)

        obj = self.search_func(name)

        exprs = tree.children[1:] if len(tree.children) > 1 else []
        values = [self.visit(args) for args in exprs if args is not None]
        has_rest = obj.param and obj.param[-1] == "..."

        local_env = Environment(self.source_dir, cli_args=[])
        local_env.env = dict(obj.closure.env)
        local_env.packages = self.packages

        if has_rest:
            fixed_params_count = len(obj.param) - 1
            if len(values) < fixed_params_count:
                raise TypeError(f"Function '{name}' requires at least {fixed_params_count} arguments!")

            fixed_values = values[:fixed_params_count]
            rest_values = values[fixed_params_count:]

            for p_name, val in zip(obj.param[:-1], fixed_values): local_env.env[p_name] = val
            local_env.env["..."] = ArrayObject(rest_values)
        else:
            if len(values) != len(obj.param):
                raise TypeError(f"Function '{name}' expects {len(obj.param)} arguments, got {len(values)}!")
            for p_name, val in zip(obj.param, values): local_env.env[p_name] = val

        try: return local_env.visit(obj.block)
        except ReturnSignal as ret: return ret.value

parser = Lark(
    GRAMMAR.read_text(encoding="utf-8"),
    parser="lalr"
)

def version():
    changelog_path = Path("CHANGELOG.txt")
    if not changelog_path.is_file(): return "1.0.0"

    content = changelog_path.read_text(encoding='utf-8').strip()
    if not content: return "1.0.0"

    lines = [b.strip() for b in content.split("\n\n") if b.strip()]
    if lines:
        latest_block = lines[-1]
        first_line = latest_block.splitlines()[0].strip()
        return first_line
    return "1.0.0"

VERSION = version()

def helpme():
    print("usage: own [-mf] <file1> [file2] ...\n")
    print(f"{VERSION}")

def main():
    args = sys.argv[1:]

    if not args:
        helpme()
        return

    if args[0] == "-mf":
        file_paths = args[1:]
        if not file_paths:
            print("Error: No files specified after -mf!")
            return

        base_dir = Path(file_paths[0]).parent
        env = Environment(base_dir, cli_args=[])

        for file_path in file_paths:
            target = Path(file_path)
            if not target.is_file():
                print(f"Error: File {target} not found!")
                continue

            if target.suffix != ".own":
                print(f"Error: File {target} isn't a valid '.own' file!")
                continue

            source = target.read_text(encoding="utf-8")
            tree = parser.parse(source)
            env.visit(tree)

    else:
        file_path = args[0]
        target = Path(file_path)

        if not target.is_file():
            print(f"Error: File {target} not found!")
            return

        cli_args = args[1:]
        env = Environment(target.parent, cli_args=cli_args)
        source = target.read_text(encoding="utf-8")
        tree = parser.parse(source)
        env.visit(tree)

if __name__ == "__main__":
    main()