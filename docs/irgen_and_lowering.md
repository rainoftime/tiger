## 5. 中间代码生成 (Intermediate Representation)

### 概述
生成平台无关的中间表示 (IR)，基于树形数据结构实现。

### 主要组件
- **`translate.py`**: IR 代码生成的核心实现
    - Translate 类: 处理 AST 到 IR 的转换
    - Exp 类: 包装 IR 表达式
    - Level 类: 管理嵌套层级和访问链
- **`tree.py`**: 定义 IR 树的节点类型
    - 表达式节点: CONST, NAME, TEMP, BINOP, MEM, CALL
    - 语句节点: MOVE, EXP, JUMP, CJUMP, SEQ, LABEL
- **`fragment.py`**: 代码和数据片段管理
    - ProcFrag: 函数代码片段
    - StringFrag: 字符串常量片段

### IR 节点实现
- **表达式节点**
    ```python
    class CONST(Exp):
        def __init__(self, value: int): ...
    
    class BINOP(Exp):
        def __init__(self, op, left, right): ...
        # op: PLUS, MINUS, MUL, DIV, AND, OR, XOR, ...
    
    class MEM(Exp):
        def __init__(self, exp): ...  # 内存访问
    ```
- **语句节点**
    ```python
    class MOVE(Stm):
        def __init__(self, dst, src): ...
    
    class CJUMP(Stm):
        def __init__(self, op, e1, e2, t, f): ...
        # op: EQ, NE, LT, GT, LE, GE
    ```

### 翻译实现细节
- **表达式翻译**
    - 算术运算: 生成 BINOP 节点
    - 变量访问: 通过 TEMP 或 MEM 节点
    - 函数调用: 生成 CALL 节点
- **控制流翻译**
    - if-then-else: 使用 CJUMP 和标签
    - while 循环: 测试、循环体和跳转
    - for 循环: 初始化、测试和更新
- **数据结构访问**
    - 数组: 计算偏移量的 MEM 访问
    - 记录: 字段偏移量的 MEM 访问

### 优化
- 常量折叠
- 强度削减
- 死代码消除

### 示例
```python
# while 循环的 IR 生成
def translate_while(self, test, body):
    test_label = self.new_label()
    body_label = self.new_label()
    done_label = self.new_label()
    
    return SEQ([
        LABEL(test_label),
        CJUMP(EQ, test, CONST(0), done_label, body_label),
        LABEL(body_label),
        body,
        JUMP(test_label),
        LABEL(done_label)
    ])
```


---