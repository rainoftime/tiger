## 8. 活性分析 (Liveness Analysis)

### 概述
分析变量的生存期，为寄存器分配提供依据。

### 主要组件
- **`analyzer.py`**: 实现活性分析算法
    - LivenessAnalyzer 类: 核心分析器实现
    - DataFlowAnalyzer 类: 通用数据流分析框架
    - FlowGraph 类: 控制流图管理
- **`graph.py`**: 构建和维护干涉图
    - InterferenceGraph 类: 干涉图数据结构
    - Node 类: 表示变量的节点
    - Edge 类: 表示干涉关系的边
- **`flow.py`**: 数据流分析框架
    - BasicBlock 类: 基本块表示
    - FlowInfo 类: 数据流信息维护

### 实现细节
- **数据流分析**
    ```python
    class LivenessAnalyzer:
        def analyze_block(self, block):
            in_set = set()
            out_set = set()
            for instr in reversed(block.instrs):
                out_set |= self.get_uses(instr)
                out_set -= self.get_defs(instr)
                in_set = out_set.copy()
    ```
- **干涉图构建**
    ```python
    class InterferenceGraph:
        def add_interference(self, v1, v2):
            if v1 != v2:
                self.add_edge(v1, v2)
                self.add_edge(v2, v1)
    ```

### 优化技术
- **迭代数据流分析**
    - 工作表算法实现
    - 固定点计算
    - 效率优化
- **稀疏数据流表示**
    - SSA 表示支持
    - Use-Def 链维护
    - 到达定义优化

### 使用示例
```python
analyzer = LivenessAnalyzer()
flow_graph = analyzer.build_flow_graph(instructions)
live_info = analyzer.analyze(flow_graph)
interference_graph = build_interference_graph(live_info)
```

---

## 9. 寄存器分配 (Register Allocation)

### 主要组件
- **`allocator.py`**: 寄存器分配器实现
    - RegAllocator 类: 图着色分配器
    - ColoringAllocator 类: Kempe 算法实现
    - SpillManager 类: 处理寄存器溢出
- **`coloring.py`**: 图着色算法实现
    - GraphColoring 类: 着色算法核心
    - SimplifyWorklist 类: 简化工作表
    - SpillWorklist 类: 溢出工作表
- **`spill.py`**: 处理寄存器溢出
    - SpillCode 类: 生成溢出代码
    - MemoryManager 类: 管理栈帧空间

### 实现细节
- **图着色算法**
    ```python
    class GraphColoring:
        def color_graph(self):
            while self.simplify_worklist:
                node = self.simplify_worklist.pop()
                self.stack.push(node)
                self.remove_node(node)
            
            while self.stack:
                node = self.stack.pop()
                self.select_color(node)
    ```
- **溢出处理**
    ```python
    class SpillManager:
        def generate_spill_code(self, temp):
            # 生成加载指令
            load = self.frame.generate_load(temp, self.offset)
            # 生成存储指令
            store = self.frame.generate_store(temp, self.offset)
            return load, store
    ```

### 优化技术
- **图着色优化**
    - 合并保守性检查
    - 度数约束优化
    - 着色偏好处理
- **溢出代价模型**
    - 循环嵌套层次
    - 使用频率统计
    - 访问模式分析

### 使用示例
```python
allocator = RegAllocator(interference_graph)
coloring = allocator.allocate()
if allocator.has_spills():
    spill_code = allocator.handle_spills()
    # 重新进行分配
    coloring = allocator.reallocate()
```

### 调试支持
- 干涉图可视化
- 着色过程跟踪
- 溢出决策分析