---
tags:
  - 程式語言/Rust
aliases: 
來源:
  - "[[Rust 權威指南]]"
新建日期: 2024-02-13 00:58:04
---

# 概念
切片這東西跟[[Python 基本#List 切片|Python切片]]是同一個概念
只是Rust是建立在[[Rust 引用]]上面
還有切片一率都是**只讀**的

```Rust 
    let s = String::from("hello world");

    let hello = &s[0..5];
    let world = &s[6..11];
```

![](../../../../Source來源筆記/圖片/Slice%20切片/Pasted%20image%2020240219143429.png)