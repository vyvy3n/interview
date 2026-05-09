---
layout: ../../layouts/Layout.astro
title: System Design
---

# Intro & News Feed System

System Design 特别是针对后端工程师, especially 全栈工程师必须.

下面哪个不是常见的用做消息队列 (Message Queue) 的软件

# Design User System: Datebase & Cache

QPS/RPS: Queries per second (QPS) is a common measure of the amount of search traffic an information retrieval system, such as a search engine or a database, receives during one second. The term is used more broadly for any request-response system, more correctly called requests per second (RPS).

## 2.1 用户系统设计 & QPS

4S - Storage: QPS 与 常用数据存储系统

- MySQL / PosgreSQL 等 SQL 数据库的性能

  - 约 1k QPS 这个级别

- MongoDB / Cassandra 等 硬盘型NoSQL 数据库的性能

  - 约 10k QPS 这个级别

- Redis / Memcached 等 内存型NoSQL 数据库的性能

  - 100k ~ 1m QPS 这个级别

Note: 以上数据根据机器性能和硬盘数量及硬盘读写速度会有区别. 能处理大数量级的 database 读写也相应会慢一些

Q: 那 10k 到 100k 选什么呢?

- 看需求。可以使用单台redis或者使用多台Cassandra的集群，又或者如果你的场景需要高可靠性的事务支持，但是读多写少，那就MySQL做持久化+memcached做cache优化。不同的数据库有不同的功能，这里列出的QPS只是为了告诉你各个数据库的承载能力，不是说xxxQPS就一定要用xxx数据库，QPS不是唯一决定因素，需要结合实际需求分析。

Q: 注册, 登录, 信息修改使用哪种数据库可以满足?

- MySQL ✓

- Cassandra ✓

- Redis ✓

- Memcached ❌: Memcached 不能持久化存储数据, 不适合用来存储用户信息

Q: 为什么Mysql只支持1k 的QPS,但facebook 依然会选择。 facebook的QPS应该远高于1k吧

- 单机1k左右，但是facebook的是mysql集群，QPS肯定不是这个量级的

Q: memcached 可以单独使用吗？如果对于需要持久化的数据，是不是不能单独使用memcached ? 一般最常用与之搭配的数据库是什么

可以的

是的

memcached+ mysql

## 2.2 什么是缓存

- Q: 文件系统可以用作缓存么？如果可以，可以做什么的缓存？用来做网络请求的缓存 / 用来做计算结果的缓存 / 用来做数据库的缓存

- A: 缓存的目的是让访问变得更快。文件系统的访问比网络访问快，一些耗时很长的计算得到的结果也可以缓存在文件中，但是文件系统的访问速度和数据库的访问速度基本上是差不多，所以一般不会用文件系统来做数据库的缓存，意义不大。

Q: redis，memcached会比普通的存储贵吗

A: 你可以去 AWS 看一下价格。 redis memcached 用 memory 多，肯定比主要用 disk 的机器要贵的。

Cache: LRU \ LFU

## 2.3 Cache 如何优化 Database 数据读取

![](/notes/system-design/media/image1.png)

类似记忆化搜索

![](/notes/system-design/media/image2.png)

Q: 没有可能第一个执行失败，第二个执行成功？

A: 不可能。程序的执行是顺序执行的，第一个语句执行出错以后，第二个语句就不会执行了，用户会收到整个 setUser 操作失败的信息。

Q:能否给数据库和缓存的操作加锁来保证数据一致性？

A:加锁以后只能保证在同一个数据上的操作顺序执行，但是无法执行“回滚”，也就是说如果第一个操作成功，第二个操作失败了，也会导致数据的不一致。

另外互斥锁（mutex）是多线程内共享的，多进程内无法共享。如果要加锁，只能使用分布式锁，比如 Zookeeper，但是这会导致读取效率急剧降低。得不偿失。

AND

多进程的内容空间不一样 （多线程可以）

mutex 变量并没法共享

甚至不是多进程 是多机器

cahce 本来为了加速

加锁反而减速

业界 practice: 因为读多写少

这样只有当 getUser 很多而且遇到 cache miss (line 9-10) 才会 inconsistent

[单选题]User Table 的 Cache Hit Rate 一般有多少？

20% \ 50% \ 95% \ 98%

⇒ 98%

hit rate = cache hit / (cache hit + cache miss)

解决方案: ttl

system design 中 solution 通常不完美 yes

## 2.4 写多读少怎么优化

Sharding

![](/notes/system-design/media/image3.png)

A C E G H
