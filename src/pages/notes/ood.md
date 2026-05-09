---
layout: ../../layouts/Layout.astro
title: Object-Oriented Design
---

# Intro to Object Oriented Design

## OOD 三大特性: 封装 / 继承 / 多态

封装

继承

多态

## Object v.s. Process-Oriented

常见的面向对象编程语言: Java、C++、C#、Python、Go语言等

常见的面向过程编程语言: C、Fortran

面向对象: 易维护、易复用、易扩展: 

- 面向对象中的类调用时需要实例化, 比较消耗资源; 比如单片机、嵌入式开发、Linux/Unix 等一般采用面向过程开发, 性能是最重要的因素.

面向过程: 性能高

- 封装、继承、多态性的特性 ⇒ 可以设计出低耦合的系统 ⇒ 系统更加灵活易维护.

## S.O.L.I.D. Principles

S – Single responsibility principle 单一责任原则

O – Open close principle 开放封闭原则

L – Liskov substitution principle 里氏替换原则

I – Interface segregation principle 接口分离原则

D – Dependency inversion principle 依赖反转原则

S.单一责任

- 一个类只有一项工作, e.g.: 一个格式化数据打印的类, 类中的成员函数可以有 Json / String / List 格式化输出函数等等. 单一责任指这个类的唯一工作就是格式化输出数据.

O.开放封闭

- 对象或实体应对扩展开放, 对修改封闭 (open to extension, close to omodification)

L.里氏替换

- 任何一个子类或派生类应该可以替换它们的基类或父类

I.接口分离

- 不应该强迫一个类实现它用不上的接口

D.依赖反转

- 抽象不应该依赖于具体实现, 具体实现应该依赖于抽象. High-level 的实体不应该依赖于 low-level 的实体抽象不应该依赖于具体实现, 具体实现应该依赖于抽象 High-level 的实体不应该依赖于 low-level 的实体.

![](/notes/ood/media/image1.png)

解析: 

抽象类不允许被直接创建对象, 其他类的特性依旧存在. 

抽象类的实现应在继承该类的子类中去具体实现. 

抽象类中只负责定义该抽象方法. 由于 abstract methods 需要在继承后的子类中实现, 因此不可以与 final / private / static 共存.

![](/notes/ood/media/image2.png)

解析:

当父类的某些方法不确定时, 可以用 abstract 关键字来修饰该方法. 用 abstract 来修饰该类 [abstract class]. 一个类中一旦有抽象方法, 必须定义成抽象类. 子类在继承父类的时候一定要实现父类中的抽象方法, 并且会自动继承除构造函数以外的 Public 和 Protect 方法, 子类可以重写这些方法. 此外, 子类也可以自定义自身的方法.

## 5 C 解题法

Clarify: 确定答题范围 / 题目中的歧义

Core objects: 确定题目所涉及的类 (输入 / 输出), 以及类之间的映射关系

Cases: 确定题目中所需要实现的场景和功能

Classes: 通过类图的方式, 具体填充题目中涉及的类

Correctness: 检查自己的设计, 是否满足关键点

## e.g. Elevator System

在设计电梯系统的 Core Object 时需要考虑的 Object 之间的对应关系

- Request 和 Elevator System

- Elevator System 和 Elevator

- Elevator 和 Elevator Button

注释: 可以把 Elevator 看成 Elevator System 的输出

![](/notes/ood/media/image3.png)

解析: 在 UML 类图当中, 每个方法和属性都会用前缀修饰符来表示其访问级别.

若没有前缀修饰符: 则此方法或属性 Package 内都可访问, 在不同 Package 内不能直接访问.

若有修饰符

- '+': Public, 能在任何地方都能直接访问;

- '-': Private, 只能通过类内部访问;

- '#' Protected, 在同一个 Package 内可以访问，在另一个 Package 内需要通过子类继承才能进行访问

![](/notes/ood/media/image4.png)

解析: 使用ENUM相当于提前定义了一个类只能从一组值当中选择，比如定义一个 ENUM COLOR，可选的值为 RED, YELLOW, BLUE. 这样的方法和使  / Integer 做为值相比使得代码的可读性大大提升；同时这样的 ENUM 告诉编译器传递进来的值只能从红黄蓝三色当中选取，避免错误；同样这个定义过的 ENUM 可以在任何地方被使用。但 ENUM 从运行速度上来说和其他做法并没有太大区别。

![](/notes/ood/media/image5.png)

在 Strategy Pattern 中，我们通常使用 Interface 来是先实现多种策略的封装，这种模式符合 SOLID 原则中的哪一项？

# OOD for Management System

课前测验

![](/notes/ood/media/image6.png)

![](/notes/ood/media/image7.png)

管理类类解题方法 / 思路：思考 use cases:

之前 Reserve

之中 Serve

之后 Check Out

Parking Lot

Clarify

Core Object

Case

Class

Correctness

Design Pattern： Singleton Design Pattern。

![](/notes/ood/media/image8.png)

---

图书馆

![](/notes/ood/media/image9.png)

例子

找到提问主体

几种车

几层停车场

支持什么种类的停车位

不必要信息

不必要 dependency

动态车进出会修改静态停车场信息

把自己想象成车 vs 停车场(blackbox题目本身）。later

protected 变量：size

good practice: 

- acccess modifer： public private protected

- exception：full 停步了车、invalid ticket。

signleton 基本式在多线程有问题

线程式 performance 不好

further 可以参考静态内部类：静态内部类其实就是加载外部类时并不需要立即加载内部类，在这里加载ParkingLot的时候并没有加载LazyParkingLot，只有调用了getInstance（），才会第一次加载LazyParkingLot。因而保证了线程安全，也能保证单例的唯一性。

![](/notes/ood/media/image10.png)

为什么要把_instance放进内部类，而不是直接定义一个private static final ParkingLot _instance = new ParkingLot() 在ParkingLot的class里面，然后由一个public static ParkingLot getInstance()的函数去得到这个_instance

答：首先要搞清为什么这里要用singleton：

保证ParkingLot只有单一的实例，保证我们不会重复创建，而是始终指向同一个对象。

其次，还要理解为什么用内部类：

LazyParkingLot虽然可以独立存在，但只被ParkingLot使用。如果把LazyParkingLot的功能放在ParkingLot里去实现又会违反单一责任原则。

# OOD for Reservation System

上节课Parking Lot的例子我们只考虑了Serve和Checkout，并没有涉及Reserve，因为Reserve是管理类里比较特殊的一个题型。

今天这节课，我们会再用一道管理类的题目做一个例子，用上节课的方法设计出基本情况，再基于这样的设计去拓展Reserve的Use Case。

![](/notes/ood/media/image11.png)

![](/notes/ood/media/image12.png)

![](/notes/ood/media/image13.png)

例子 

Restaurant 

其实设计餐馆和设计停车场非常的类似，我们可以把选座看成是停车，吃完离席是离开停车场 ；唯一的不同点也是难点就在于客人需要去点餐，需要去创建Order。

contents

5c。分析完这道题目的Clarify， Core Object以及Cases；下面我们来看一下如何把他们扩展成最终的Classes。

Classes。以上的思路都可以看作是一个基本的管理类题目的设计，也是对上节课的一个回顾。那么，我们如何在原有设计的基础上，把它变成一个预定类的设计呢？

预定类解题思路。现在我们就一起来看看如何去设计一个可以Reserve的餐厅。

reservation 设计思路

reservation class

Hotel Reservation System、

5c

classes

lru

![](/notes/ood/media/image14.png)

return result list

方法二是简化

since 所有 tables same。而不是返回 list 让 user 选坐在大厅还是吧台 etc

# OOD for Real Life Object

![](/notes/ood/media/image15.png)

不知道你有没有注意到，虽然我们的VendingMachine类里面已经实现了Selectitem(), Insert coin(), Execute transaction(), Cancel transaction()这几个方法，但是当我的Vending Machine在不同的状态下，这些方法的具体操作其实是不同的。那么我们又该怎么办呢？这里就再来介绍一种新的Design Pattern——State Design Pattern。

![](/notes/ood/media/image16.png)

讲完了Vending Machine的设计，我们再来看一道实物类的设计题Coffee Maker；虽然同为实物类设计，但是他们的思路又略有不同。

又开了一阵咖啡店后，我发现先随着时代的进步，有越来越多的新的Topping加入了菜单中，我们店的咖啡杯写不下更多的Topping了，那我这时候该如何让我的咖啡店能继续开下去呢？这里介绍今天要学的第二个Design Pattern——Decorator Design Pattern。

![](/notes/ood/media/image17.png)

在实物类设计里，还有一种Design Pattern和以上两种都不相同。我们先来看一看题目，借助题目，老师来介绍今天的最后一种Design Pattern——Factory Design Pattern。

e.g. kindle

![](/notes/ood/media/image18.png)

![](/notes/ood/media/image19.png)

Strategy Design Pattern和Factory Design 到底有什么区别？

# OOD for Games

![](/notes/ood/media/image20.png)

游戏

不要 input-output 思考方式。要另一种

since 游戏包含很多状态

e.g. 中国象棋

e.g. Black Jack

![](/notes/ood/media/image21.png)

Design Pattern Review

能不能悔棋

平局：

请求平局需要是同一回合内双反都请求平局

https://us.jiuzhang.com/problem/design-tic-tac-toe/

https://leetcode.com/discuss/interview-question/125218/design-a-vending-machine
