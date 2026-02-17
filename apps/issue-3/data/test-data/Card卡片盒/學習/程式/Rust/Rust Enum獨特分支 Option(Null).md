---
tags: 程式語言/Rust 
aliases: 
- Rust Null
- Null
來源: "[[Rust 權威指南]]"
新建日期: 2024-02-22 02:12:36
---

# 概念

這是Enum裡最獨特的東西，代表 **Null**

> [!question] 為啥Rust會有Null，不是說安全嗎??
> Rust是安全，但也是會有出現Null情況
> 例如:開啟一個不存在的文件，就必須回Null，總不能回例外

```Rust title:"Option"
enum Option<T> { 
None, //<代表Null
Some(T), //<代表資料
}
```

如果回個奇怪的數據，會造成程式上問題??
其實不會，因為當數據回來時，編譯器實際上當成不同東西

```Rust title:"Rust Option返回數據"
let x: i8 = 5; 
let y: Option<i8> = Some(5); 

let sum = x + y; 
//編譯過不了，因為在Rust裡 Option(i8) 跟 i8 是不同東西
```

剩下的基本上就跟[[Rust Enum獨特分支 Option(Null)|Enum]]差不多了
用[[Rust match & if let]]來處理
