# Own 1.0.0 : Early Software
made by `Codingmc8` using `Python3` + `Lark`

## Setup

### Requirement
* `lark`
* `py-cpuinfo`
* `psutil`
* `Python3.8+`

### installing dependencies
```bash
pip install lark py-cpuinfo psutil
```
or
```bash
pip install -r requirements.txt
```

### How to use ?
1. **Single file**
```bash
own myfile.own
```

2. **Multi files**
```bash
own -mf myfile.own main.own
```

3. **CLI access** : say hi to `@1`
```bash
own myfile.own alex
```

## Update 1.0.0
``` txt
- added 13 keyword
- added argument input using @
- added math operators and math expression
- added support for int, string, boolean and null data type
- added array and object support
- simple command line information
```

## Update 1.0.1
```txt
- added import system (FFI method)
- now only support stdos for manage file or folder
- simple package system
```

## Update 1.0.2
```txt
- added typedef syntax
- added ternary operators
- update for, func, if system
- removed import system
```

## Update 1.0.3
```txt
- added const syntax
```

## Update 1.0.4
```txt
- added struct syntax
```

## Update 1.0.5
```txt
- added import syntax
- added ++ and --
```

## Update 1.0.6
```txt
- added sysinfo library
- added uuid library
- added basic os management library
```

## Example
### echo
```
echo "Hello, World"
echo "Hello:", @1

let x = "Hello"
echo x, "World"
```

### let
```
let empty
let number = 10
let string = "Hello, World"

let boolean = true
let array = [number, string, boolean]
let object = {all: array}
let range = [1..5]

// with ++
let eleven = number++

// with --
let ten = eleven--
```

### const
**basic const**
```
// with value
const say = "Hello, World"
```

**with default value**
```
typedef RangeMe : 10 ^ 2
const RangeMe me
```

**with change value**
```
typedef RangeMe : 10 ^ 2
const RangeMe me = 10 ^ 3
```

**error const**
```
// its error! null value
const my

// its error! update value is not allowed
const me = 20
me = 10
```

### for & if & else & break & continue
**print out number 0-3**
```
let i = 0
for (i < 3){
    echo i
    i += 1
}
```

**loop 0-n**
```
let running = true
let i = 0

for (running) {
    echo i
    i += 1
}
```

**repeat until number 10**
```
let running = true
let i = 0

for (running) {
    echo i
    i += 1

    if (i == 10) {
        break
    } else {
        continue
    }
}
```

**one line for if else**
```
let running = true
let i = 0

for(running) {
    let max = (i == 10) ? 10 : i
    echo max

    i += 1
    if(i >= 10) running = false
}
```

### func & return
**no param**
```
func hi() {
    echo "Hi"
}
```

**with parameter**
```
func hi_param(name) {
    echo "Hi", name
}
```

**with argument input**
```
func hi_input() {
    echo "Hi", @1
}
```

**with return and parameter**
```
func hi_ret_param(name) {
    return "Hi", name
}
```

**with default parameter**
```
func hi_default(name="Alex") {
    return name
}
```

**with expression param**
```
func hi_expr(value = 1 ? 1 : 0) {
    return value
}
```

**with one line code, for example... i write hi_default()**
```
func hi_default(name="Alex") return name
```

### typedef
```
typedef Number : 1
typedef String : "Hello, World"
typedef Boolean : true

typedef Home : getHome()
typedef Range : 1..5
```

**for interpolared string**
```
// information about home workspace
typedef Home : getHome()

Home home
typedef I_String : "Welcome {home}"
```

### struct
**struct declaration and struct access**
```
// declaration
struct Point {
    let point = 0

    func getScore(score) {
        let p = score ? score += 1 : score -= 1
        echo p
    }
}

// access
Point p

p.point = 10
p.getScore(p.point)
```

### Comment & Multi-Comment
```
// this is comment

/* this is multi-comment */
```

### Expression symbols
* **Arithmetic**: `+`, `-`, `*`, `/`, `^` (exponentiation)
* **Assignment**: `=`, `+=`, `-=`, `*=`, `/=`, `^=`
* **Comparison**: `==`, `!=`, `<`, `>`, `<=`, `>=`
* **Logical**: `&&` (AND), `||` (OR), `!` (NOT)
* **Ternary**: `?`, `:`

## Standard Library
| OS management                   | UUID                 | SysInfo               |
| ------------------------------- | -------------------- | --------------------- |
| `move(old, new)`                | `uuid()`             | `osinfo()`            |
| `rename(old, new)`              | `random(length)`     | `cpuinfo()`           |
| `copy(old, new)`                | `seed(length)`       | `gpuinfo()`           |
| `system(command, ...)`          | `choice(start, end)` | `raminfo()`           |
| `mkdir(name_or_path, ...)`      |                      | `storageinfo()`       |
| `rmdir(name_or_path, ...)`      |                      | `battery()`           |
| `touch(name_or_path, ...)`      |                      | `computer_and_bios()` |
| `rmdir(name_or_path, ...)`      |                      |                       |
| `write(name_or_path, content)`  |                      |                       |
| `append(name_or_path, content)` |                      |                       |
| `listdir(path, ...)`            |                      |                       |
| `chdir(path)`                   |                      |                       |
| `exists(path)`                  |                      |                       |

## Support
- `int`, `string`, `boolean`, `null` data type
- support custom datatype
- `.own` extension
- argument input using `@` symbols
- `array` and `object` access

## Notes
* this language use `0-based-indexing`
* not support `float` data type
* support one line code for `if` `else` `func` and `for`
* `struct` only support `struct`, `func`, `typedef`, `let` and `const`