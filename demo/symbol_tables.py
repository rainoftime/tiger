from dataclasses import dataclass
from typing import TypeVar, Generic, Optional

# 定义一个类型变量T，用于泛型编程
T = TypeVar("T")


@dataclass
class ScopeMarker:
    """标记作用域的开始，这是一个简单的数据类，不包含任何字段
    用作栈中的标记，表示一个新的作用域的起始点"""
    pass


class SimpleSymbolTable(Generic[T]):
    """简单的符号表实现，支持嵌套作用域
    
    符号表是编译器/解释器中的重要数据结构，用于存储标识符和它们的属性
    这个实现使用栈和字典的组合来支持嵌套作用域和变量查找
    泛型参数T允许符号表存储任何类型的值
    """
    def __init__(self):
        """初始化符号表
        
        stack: 用于跟踪标识符添加顺序和作用域边界的栈
        bindings: 存储标识符及其值的字典，每个标识符对应一个值列表
        """
        self.stack = []  # 用于跟踪添加顺序和作用域
        self.bindings = {}  # 存储所有绑定，key是标识符，value是该标识符所有绑定值的列表

    def add(self, identifier: str, value: T):
        """添加新的绑定到当前作用域
        
        Args:
            identifier: 要绑定的标识符名称
            value: 与标识符关联的值
            
        将标识符添加到栈中，并在bindings字典中更新其值列表
        """
        self.stack.append(identifier)  # 将标识符压入栈，记录添加顺序
        # 为标识符添加新值，如果标识符不存在则创建新列表
        self.bindings[identifier] = self.bindings.get(identifier, []) + [value]

    def find(self, identifier: str) -> Optional[T]:
        """查找给定标识符的最新绑定
        
        Args:
            identifier: 要查找的标识符
            
        Returns:
            标识符的最新绑定值，如果不存在则返回None
            
        符号表查找遵循"最近绑定优先"原则，返回最后添加的值
        """
        if identifier in self.bindings and self.bindings[identifier]:
            return self.bindings[identifier][-1]  # 返回最近添加的绑定值
        return None  # 标识符不存在时返回None

    def begin_scope(self):
        """开始一个新的作用域
        
        在栈中添加一个ScopeMarker实例，标记新作用域的开始
        作用域用于实现变量的局部可见性和生命周期管理
        """
        self.stack.append(ScopeMarker())  # 压入作用域标记

    def end_scope(self):
        """结束当前作用域，移除该作用域中的所有绑定
        
        从栈顶开始弹出元素，直到遇到ScopeMarker为止
        同时从bindings中移除对应的值
        这个过程模拟了局部变量离开作用域时的内存释放
        """
        # 持续弹出栈中元素直到遇到ScopeMarker
        while len(self.stack) > 0 and not isinstance(self.stack[-1], ScopeMarker):
            identifier = self.stack.pop()  # 弹出标识符
            self.bindings[identifier].pop()  # 移除最近的绑定值
            
            # 如果该标识符没有剩余绑定，从字典中删除它，避免内存泄漏
            if not self.bindings[identifier]:
                self.bindings.pop(identifier)
                
        # 移除作用域标记本身
        if self.stack:
            self.stack.pop()


# 使用示例：一个简单的变量作用域模拟
if __name__ == "__main__":
    # 创建一个存储整数值的符号表
    symbol_table = SimpleSymbolTable[int]()
    
    # 全局作用域
    symbol_table.add("x", 10)
    symbol_table.add("y", 20)
    print(f"全局作用域 - x: {symbol_table.find('x')}, y: {symbol_table.find('y')}")
    
    # 进入第一个嵌套作用域
    symbol_table.begin_scope()
    symbol_table.add("x", 30)  # 覆盖全局的x
    symbol_table.add("z", 40)  # 新变量z
    print(f"第一个嵌套作用域 - x: {symbol_table.find('x')}, y: {symbol_table.find('y')}, z: {symbol_table.find('z')}")
    
    # 再嵌套一个作用域
    symbol_table.begin_scope()
    symbol_table.add("y", 50)  # 覆盖全局的y
    print(f"第二个嵌套作用域 - x: {symbol_table.find('x')}, y: {symbol_table.find('y')}, z: {symbol_table.find('z')}")
    
    # 结束最内层作用域
    symbol_table.end_scope()
    print(f"返回第一个嵌套作用域 - x: {symbol_table.find('x')}, y: {symbol_table.find('y')}, z: {symbol_table.find('z')}")
    
    # 结束第一个嵌套作用域
    symbol_table.end_scope()
    print(f"返回全局作用域 - x: {symbol_table.find('x')}, y: {symbol_table.find('y')}, z: {symbol_table.find('z')}")

# 输出示例:
# 全局作用域 - x: 10, y: 20
# 第一个嵌套作用域 - x: 30, y: 20, z: 40
# 第二个嵌套作用域 - x: 30, y: 50, z: 40
# 返回第一个嵌套作用域 - x: 30, y: 20, z: 40
# 返回全局作用域 - x: 10, y: 20, z: None