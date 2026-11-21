from pathlib import Path
from lark import Lark
from lark.visitors import Interpreter
import sys, re, importlib.util
import os, shutil, uuid

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
    def __init__(self, name, param, block, closure, defaults=None, is_rest=False):
        self.name = name
        self.param = param
        self.block = block
        self.closure = closure
        self.defaults = defaults
        self.is_rest = is_rest

    def __repr__(self): return f"<function {self.name}({', '.join(self.param)})>"

class PythonObject:
    def __init__(self, name, func):
        self.name = name
        self.func = func
    def __repr__(self): return f"<python-function {self.name}>"

class RangeObject:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        if start <= end: self.elements = list(range(start, end + 1))
        else: self.elements = list(range(start, end - 1, -1))

    def __repr__(self): return f"[{', '.join(map(str, self.elements))}]"

class StructObject:
    def __init__(self, name, body, instance):
        self.name = name
        self.body = body
        self.instance = instance

    def __repr__(self): return f"<struct {self.name}>"

class StructInstance:
    def __init__(self, struct_def):
        self.struct_def = struct_def
        self.fields = {}

        local_env = Environment(struct_def.instance.source_dir, [])
        local_env.env = dict(struct_def.instance.env)

        for child in struct_def.body: local_env.visit(child)
        self.fields = dict(local_env.env)

    def get_key(self, key):
        if key not in self.fields: raise KeyError(f"Struct instance not have attribute '{key}'")
        return self.fields[key]

    def set_key(self, key, value):
        if key not in self.fields: raise KeyError(f"Struct instance not have attribute '{key}'")
        self.fields[key] = value
        return value

    def __repr__(self): return f"<struct-instance {self.struct_def.name}>"

class Environment(Interpreter):
    def __init__(self, source_dir, cli_args=None):
        super().__init__()
        self.env = {}
        self.source_dir = Path(source_dir).resolve()
        self.const = set()

        terminal = cli_args if cli_args is not None else (sys.argv[2:] if len(sys.argv) > 2 else [])
        self.env["@"] = ArrayObject(terminal)
        self.typedefs = {}

    def start(self, tree):
        result = None
        for child in tree.children:
            result = self.visit(child)
        return result

    def range_expr(self, tree):
        one = self.visit(tree.children[0])
        end = self.visit(tree.children[1])

        if not isinstance(one, int) and not isinstance(end, int):
            raise TypeError("range bounderies must be a int")
        return RangeObject(one, end)

    def unit(self, tree): return self.visit(tree.children[0])
    def args(self, tree): return self.visit(tree.children[0])
    def expr(self, tree): return self.visit(tree.children[0])

    def number(self, tree): return int(tree.children[0])

    def string(self, tree):
        raw = str(tree.children[0])[1:-1]
        pattern = r'\${([^}]+)}'

        def replace(match):
            expr_str = match.group(1).strip()
            try:
                if expr_str in self.env: val = self.env[expr_str]
                else:
                    sub_tree = parser.parse(expr_str)
                    val = self.visit(sub_tree)

                if val is True: return "true"
                elif val is False: return "false"
                elif val is None: return "null"

                return str(val)
            except Exception as e:
                return f"<eval-error: {expr_str}>"

        arg_str = re.sub(pattern, replace, raw)
        return arg_str

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
        if name in self.const: raise TypeError(f"Variable '{name}' is a constanta!")

        value = self.visit(value)
        self.env[str(name)] = value
        return value

    def _compound(self, tree, operation):
        name, value = tree.children
        if name in self.const: raise TypeError(f"Variable '{name}' is constanta!")

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

    def inc(self, tree):
        name = str(tree.children[0])
        tree.children = [name, 1]
        return self.add_equal(tree)

    def dec(self, tree):
        name = str(tree.children[0])
        tree.children = [name, 1]
        return self.min_equal(tree)

    def ternary_logic(self, tree):
        condition = self.visit(tree.children[0])
        if condition: return self.visit(tree.children[1])
        else: return self.visit(tree.children[2])

    def array(self, tree):
        elements = []
        for child in tree.children:
            val = self.visit(child)
            if isinstance(val, RangeObject):
                elements.extend(val.elements)
            else:
                elements.append(val)
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

        if isinstance(obj, StructInstance): return obj.get_key(prop_name)
        elif isinstance(obj, DictObject): return obj.get(prop_name)
        raise TypeError(f"Variable '{name}' isn't a struct or object!")

    def obj_assignment(self, tree):
        name = str(tree.children[0])
        prop_name = str(tree.children[1])
        expr = tree.children[2]
        obj = self.search(name)
        val = self.visit(expr)

        if isinstance(obj, StructInstance): return obj.set_key(prop_name, val)
        elif isinstance(obj, DictObject): return obj.set(prop_name, val)
        raise TypeError(f"Variable '{name}' isn't a struct or object!")

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
            if isinstance(v, RangeObject): formatted.append(" ".join(map(str, v.elements)))
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
        elif len(tree.children) > 2 and tree.children[2] is not None:
            return self.visit(tree.children[2])
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

    def typedef_stmt(self, tree):
        name = str(tree.children[0])
        value = self.visit(tree.children[1])
        self.typedefs[name] = value
        return value

    def typed_register(self, tree):
        type_name = str(tree.children[0])
        var = str(tree.children[1])

        if type_name in self.typedefs and isinstance(self.typedefs[var], StructObject):
            struct_def = self.typedefs[type_name]
            instance = StructInstance(struct_def)

            self.env[var] = instance
            return instance

        if len(tree.children) > 2 and tree.children[2] is not None:
            val = self.visit(tree.children[2])
        else: val = None

        if type_name not in self.typedefs: raise TypeError(f"Unknown type '{type_name}'")
        self.env[var] = val
        return val

    def typed_default_register(self, tree):
        type_name = str(tree.children[0])
        var = str(tree.children[1])

        if type_name not in self.env: raise NameError(f"Undefined type '{type_name}'")
        default = self.env[type_name]
        if default is None:
            raise TypeError(f"Cannot initialize variable '{var}': default value from '{type_name}' is null/empty!")

        self.env[var] = default
        return default

    def struct_stmt(self, tree):
        name = str(tree.children[0])
        body = tree.children[1:]
        struct_obj = StructObject(name, body, self)

        self.typedefs[name] = struct_obj
        self.env[name] = struct_obj
        return struct_obj

    def break_stmt(self, tree): raise BreakSignal()
    def continue_stmt(self, tree): raise ContinueSignal()

    def execute_external(self, path):
        if not hasattr(path, 'loaded_modules'): self.loaded_modules = set()
        resolved = path.resolve()
        if resolved in self.loaded_modules: return

        self.loaded_modules.add(resolved)
        source = path.read_text(encoding="utf-8")
        tree = parser.parse(source)

        sub_env = Environment(path.parent, [])
        sub_env.env = self.env

        sub_env.loaded_modules = self.loaded_modules
        sub_env.visit(tree)

    def reg_func(self, tree):
        name = str(tree.children[0])
        param = tree.children[1]
        body = tree.children[2]

        params = []
        default = {}
        is_rest = False

        if param and hasattr(param, "children"):
            for item in param.children:
                if item is None: continue
                if hasattr(item, "data") and item.data == "param_with_default":
                    p_name = str(item.children[0])
                    params.append(p_name)
                    if len(p_name) > 1: default[p_name] = item.children[1]
                elif str(item) == "...":
                    is_rest = True
                    params.append("...")
        elif param is not None: params.append(str(param))

        func_obj = FunctionObject(name, params, body, self, defaults=default, is_rest=is_rest)
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
        passed_values = [self.visit(args) for args in exprs if args is not None]

        local_env = Environment(self.source_dir, cli_args=[])
        local_env.env = dict(obj.closure.env)
        local_env.packages = self.packages

        params = obj.param
        has_rest = getattr(obj, "is_rest", False)
        defaults = getattr(obj, "defaults", {})

        if has_rest:
            fixed_params = [p for p in params if p != "..."]
            fixed_count = len(fixed_params)

            for i, p_name in enumerate(fixed_params):
                if i < len(passed_values): local_env.env[p_name] = passed_values[i]
                elif p_name in defaults: local_env.env[p_name] = local_env.visit(defaults[p_name])
                else: raise TypeError(f"Function '{name}' missing required argument '{p_name}'!")
            
            rest_vals = passed_values[fixed_count:]
            local_env.env["..."] = ArrayObject(rest_vals)
        else:
            val_idx = 0

            for p_name in params:
                if val_idx < len(passed_values):
                    local_env.env[p_name] = passed_values[val_idx]
                    val_idx += 1
                elif p_name in defaults: local_env.env[p_name] = local_env.visit(defaults[p_name])
                else: raise TypeError(f"Function '{name}' missing argument for '{p_name}'!")
            
            if val_idx < len(passed_values):
                raise TypeError(f"Function '{name}' expects {len(params)} arguments, got {len(passed_values)}!")

        try: return local_env.visit(obj.block)
        except ReturnSignal as ret: return ret.value

    def const_stmt(self, tree):
        name = str(tree.children[0])
        value = tree.children[1]

        if name in self.env: raise NameError(f"Variable '{name}' have been declarated before!")
        self.const.add(name)
        
        self.env[name] = value
        return value

    def const_alias_stmt(self, tree):
        alias = str(tree.children[0])
        name = str(tree.children[1])

        if alias not in self.typedefs and alias not in self.env:
            raise TypeError(f"Unknown type/alias '{alias}'")
        if name in self.env: raise NameError(f"Variable '{name}' have been declarated before!")

        if len(tree.children) > 2 and tree.children[2] is not None: value = self.visit(tree.children[2])
        else: value = self.env.get(alias, None)

        self.const.add(name)
        self.env[name] = value
        return value

    def import_stmt(self, tree):
        parts = [str(child) for child in tree.children]
        current_path = self.source_dir

        for i, part in enumerate(parts):
            folder = current_path / part
            file = current_path / f"{part}.own"

            if folder.is_dir(): current_path = folder
            elif file.is_file():
                target = file
                if i < len(parts) - 1: raise ImportError(f"Cannot revolved path: '{part}' is a file, not a directory!")
                return self.reload(target, parts[-1])
            else:
                direct = current_path / part
                if direct.is_file(): return self.reload(direct, part)
                raise ImportError(f"Package or module '{'.'.join(parts[:i+1])}' not found!")

    def reload(self, path, module_alias):
        resolved_path = path.resolve()
        if not hasattr(self, 'module_storage'): self.module_storage = {}

        if resolved_path in self.module_storage: module_env = self.module_storage[resolved_path]
        else:
            source = resolved_path.read_text(encoding='utf-8')
            tree = parser.parse(source)

            module_env = Environment(resolved_path.parent, [])
            module_env.visit(tree)
            self.module_storage[resolved_path] = module_env

        module_container = DictObject(module_env.env)
        self.env[module_alias] = module_container
        return module_container

parser = Lark(
    GRAMMAR.read_text(encoding="utf-8"),
    parser='earley'
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