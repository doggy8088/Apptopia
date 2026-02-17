---
tags: 
- 程式語言/Rust 
aliases: 
來源: 
- "[[Rust 權威指南]]"
- "[[Rust 编程语言入门教程 2021]]"
新建日期: 2024-03-19 19:57:31
---

>[!info] 注意
>  在[[Rust 權威指南]]中，寫的很亂
>  即使在 [[Rust 编程语言入门教程 2021]]中也是簡單帶過
>  所以只能小心注意

# 概念

## String? str?

文字的類型在Rust裡有兩個關鍵字

1. str
在Rust核心裡，無法被宣告成可變
即使宣告了，也只能使用引用 **&str**，概念上說更接近於 **字**
而不是字串

2. String 
在標準庫裡面，也是最常用的跟其他語言的String是差不多的東西，

主要是Rust為安全性，所以區分成2個
將可變常用的歸類在String而當實際要進行處理時，就將String進行切片變成引用(&str)來處理，因為str是屬於不可變類型，所以在Rust中講到字串指的基本上是 **String** **&str**這兩種


```rust title:"String宣告方式"
let mut s = String::new();
let data = "initial contents"; 
let s = data.to_string(); 
let s = "initial contents".to_string();
```


## UTF-8?

是的，Rust原生支持 UTF-8，所以可以打字都不會有亂碼~~~~

```rust title:"Rust UTF-8"
    let hello = String::from("السلام عليكم");
    let hello = String::from("Dobrý den");
    let hello = String::from("Hello");
    let hello = String::from("שָׁלוֹם");
    let hello = String::from("नमस्ते");
    let hello = String::from("こんにちは");
    let hello = String::from("안녕하세요");
    let hello = String::from("你好");
    let hello = String::from("Olá");
    let hello = String::from("Здравствуйте");
    let hello = String::from("Hola");
```

## 新增 插入 刪除

### 新增

- 使用 `+` 運算子將兩個字串相加，但是會喪失所有權
- 使用 `String::from()` 函數將字串字面量轉換為 `String` 類型的字串
- 使用`format!`連接多個字串

### 加入

- 使用 `push()` 方法將單個字元加入字串尾部。
- 使用 `push_str()` 方法將字串字面量加入字串尾部。

### 插入

- 使用 `insert()` 方法將單個字元插入字串指定位置。
- 使用 `insert_str()` 方法將字串字面量插入字串指定位置。

### 刪除

- 使用 `pop()` 方法刪除字串尾部的單個字元。
- 使用 `truncate()` 方法將字串截斷到指定長度。
- 使用 `clear()` 方法清空字串。


```rust
// 新增 
let s1 = "Hello" + " "; 
let s2 = String::from("world!"); 
let s3 = s1 + s2; println!("{}", s3); 
// 輸出: Hello world! 

// 加入 
let mut s4 = String::from("Hello"); 
s4.push(' '); 
s4.push_str("world!"); 
println!("{}", s4); 
// 輸出: Hello world! 

// 插入 
let mut s5 = String::from("Hello"); 
s5.insert(5, ','); 
s5.insert_str(6, " "); 
println!("{}", s5); 
// 輸出: Hello, world!

// 刪除 
let mut s6 = String::from("Hello world!"); 
s6.pop(); 
s6.truncate(5);
println!("{}", s6); 
// 輸出: Hello
```

## 好用函式format!

可以將輸入字串，串在一起並輸出String
```Rust
format!("{}, by {} ({})", self.headline, self.author, self.location)
```