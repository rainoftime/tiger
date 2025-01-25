## 7. 指令选择 (Instruction Selection)

### 概述
将平台无关的 IR 转换为 RISC-V 汇编指令序列。

### 主要组件
- **`codegen.py`**: 代码生成器实现
    - CodeGen 类: 处理 IR 到 RISC-V 指令的转换
    - InstrGen 类: 处理具体指令生成
    - Matcher 类: 实现树模式匹配
- **`assembly.py`**: 定义 RISC-V 汇编指令
    - RISC-V 基本指令: 算术、逻辑、分支、访存
    - 指令格式和编码
    - 伪指令支持
- **`patterns.py`**: 定义指令选择模式
    - 树模式匹配规则
    - 代价估算函数
    - 重写规则定义

### RISC-V 指令映射
- **算术运算**
    ```python
    def munch_BINOP(self, e):
        # e: BINOP(PLUS, e1, e2)
        # -> add rd, rs1, rs2
        if e.op == PLUS:
            r1 = self.munch_exp(e.left)
            r2 = self.munch_exp(e.right)
            rd = self.frame.new_temp()
            self.emit(ADD(rd, r1, r2))
            return rd
    ```
- **内存访问**
    ```python
    def munch_MEM(self, e):
        # e: MEM(BINOP(PLUS, e1, CONST(n)))
        # -> lw rd, n(rs1)
        addr = self.munch_exp(e.exp)
        rd = self.frame.new_temp()
        self.emit(LW(rd, addr, 0))
        return rd
    ```
- **控制转移**
    ```python
    def munch_CJUMP(self, s):
        # s: CJUMP(op, e1, e2, t, f)
        # -> beq rs1, rs2, label
        r1 = self.munch_exp(s.left)
        r2 = self.munch_exp(s.right)
        self.emit(BEQ(r1, r2, s.true_label))
    ```

### 优化技术
- **指令合并**
    - 加载-存储合并
    - 地址计算优化
    - 常量传播
- **寻址模式选择**
    - 基址寻址
    - 立即数寻址
    - 间接寻址
- **延迟槽填充**
    - 分支延迟槽优化
    - 加载延迟槽处理

### 使用示例
```python
# 生成加法指令
def generate_add(self, dst, src1, src2):
    return ADD(self.temp_map[dst],
              self.temp_map[src1],
              self.temp_map[src2])

# 生成内存加载
def generate_load(self, dst, base, offset):
    return LW(self.temp_map[dst],
             self.temp_map[base],
             offset)
```

### 实现细节
参考 `codegen.py`、`assembly.py` 和 `patterns.py` 的具体实现。

---