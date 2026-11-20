# Own 1.0.0 : Early Software
made by `Codingmc8` using `Python3` + `Lark`

## Setup

### Requirement
* `lark`
* `Python3.8+`

### installing dependencies
```bash
pip install lark
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
```

### for & if & else & break & continue
```
// print out number 0-3
let i = 0
for i < 3 {
    echo i
    i += 1
}

// loop 0-n
let running = true
let i = 0

for running {
    echo i
    i += 1
}

// repeat until number 10
let running = true
let i = 0

for running {
    echo i
    i += 1

    if i == 10 {
        break
    } else {
        continue
    }
}
```

### func & return
```
// no parameter
func hi() {
    echo "Hi"
}

// with parameter
func hi_param(name) {
    echo "Hi", name
}

// with argument input
func hi_input() {
    echo "Hi", @1
}

// with return and parameter
func hi_ret_param(name) {
    return "Hi", name
}
```

### import
```
// import with package system
import "path/to/your/library"

// import without package system
import "mylibrary.own"
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

## Support
- `int`, `string`, `boolean`, `null` data type
- `.own` extension
- argument input using `@` symbols
- `array` and `object` access

## Notes
* this language use `0-based-indexing`
* not support `float` data type

## Next Update
* [] better import system