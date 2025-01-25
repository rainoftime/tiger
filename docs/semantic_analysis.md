## 3. 语义分析 (Semantic Analysis)

### 概述
负责类型检查和语义验证，确保程序满足 Tiger 语言的静态语义规则。

### 主要组件
- **`analyzers.py`**: 语义分析器的核心实现，包含类型检查和变量绑定
- **`types.py`**: 类型系统实现，定义了 INT、STRING、NIL、RECORD、ARRAY 等类型
- **`table.py`**: 符号表管理，支持嵌套作用域和变量查找
- **`environment.py`**: 类型环境(tenv)和变量环境(venv)的维护

### 主要功能
- **类型检查**
    ```python
    def visit_OpExp(self, exp):
        left = self.visit(exp.left)
        right = self.visit(exp.right)
        if exp.oper in [PLUS, MINUS, TIMES, DIVIDE]:
            self.check_int(left)
            self.check_int(right)
            return INT()
    ```
    - 算术运算要求整数类型
    - 比较运算支持整数和字符串
    - 逻辑运算返回整数类型
    - 数组下标必须为整数
    - 记录字段访问类型匹配

- **变量分析**
    ```python
    def visit_VarDec(self, dec):
        init = self.visit(dec.init)
        if dec.typ:
            expected = self.actual_ty(self.trans_ty(dec.typ))
            self.check_types(init, expected)
        self.venv.enter(dec.name, VarEntry(init))
    ```
    - 变量声明类型检查
    - 变量引用作用域验证
    - 函数参数类型匹配
    - 循环变量范围检查
    
- **符号表实现**
    ```python
    class Table:
        def enter(self, key, value):
            self.table[key] = value
            
        def look(self, key):
            return self.table.get(key)
            
        def begin_scope(self):
            self.scopes.append({})
            
        def end_scope(self):
            self.scopes.pop()
    ```

### 错误处理
- 类型不匹配
- 未声明变量引用
- 重复变量定义
- 非法数组下标
- 未知记录字段

### 实现细节
参考 `analyzers.py`、`types.py` 和 `table.py` 中的具体代码实现。

---