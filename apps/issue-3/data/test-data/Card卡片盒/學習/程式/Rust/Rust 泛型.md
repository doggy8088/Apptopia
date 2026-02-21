---
tags: 程式語言/Rust  
aliases:
- 泛型
來源: 
- "[[Rust 權威指南]]"
- "[[Rust 编程语言入门教程 2021]]"
- "[[為你自己學 Rust 系列]]"
新建日期: 2024-03-21 23:29:04
---


# 概念
基本上跟C#是一樣的，只是Rust可以在[[Rust Enum枚舉|Enum]]上使用


```rust title:"Rust泛型範例"
struct Rectangle<T> {
    width: T,
    height: T,
}

fn add_number<T>(a: T, b: T) -> T {
    a + b
}
```

```rust title:"泛型限制"
//泛型限制說，T必須實現Add這特徵才行
fn add_number<T: std::ops::Add<Output = T>>(a: T, b: T) -> T {
    a + b
}

//但越寫會越長所以可以用Where來縮短
fn calc<T>(a: T, b: T, c: T) -> T
where T: Add<Output = T> + Sub<Output = T>
{
    a + b - c
}
```


