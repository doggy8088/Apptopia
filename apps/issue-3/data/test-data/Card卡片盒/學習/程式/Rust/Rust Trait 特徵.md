---
tags: 程式語言/Rust  
aliases: 
來源: 
- "[[Rust 權威指南]]"
- "[[Rust 编程语言入门教程 2021]]"
- "[[為你自己學 Rust 系列]]"
新建日期: 2024-03-30 18:56:43
---


# 概念

這是Rust獨有的東西，也是撐起Rust核心的概念
要理解的話可以想成是將[[0.5.設計模式#3.多態|Interface]]+[[0.5.設計模式#2.1 抽象 (被歸類在繼承裡面)|抽象方法abstract]]+[[0.5.設計模式#2.1 抽象 (被歸類在繼承裡面)|虛方法(virtual)]]混在一起的概念

## Trait特徵
特徵宣告是用`trait`當關鍵字並在後面添加所需內容
只是特徵裡面只能放入函式和常數兩個東西
函式部分容許有預設邏輯
使用方式跟[[Rust Struct#Struct Function 結構方法]]一樣
加上`impl`就可以`&self`部分也是一樣
特徵也可以作為參數或返回值，基本上就把他當成C# interfaces那樣可以宣告的物件

```rust title:"特徵範例"
pub trait Test {
	const a: u32;  //常數
	fn IamTest(&self) -> String; //等同Interface 
	fn IamTest2();  //Interface 但是無法讀到Struct資料
	fn IanTest3(&self) {  //等同虛方法概念
    println!("Helloworld");  
}
```

```rust title:"特徵範例"
pub trait Summary {
    fn summarize(&self) -> String;
}

pub struct NewsArticle {
    pub headline: String,
    pub location: String,
    pub author: String,
    pub content: String,
}

impl Summary for NewsArticle {
    fn summarize(&self) -> String {
        format!("{}, by {} ({})", self.headline, self.author, self.location)
    }
}
```

```rust title:"特徵作為參數"
pub fn notify(item: &impl Summary) {
    println!("Breaking news! {}", item.summarize());
}

pub fn notify<T: Summary>(item: &T) {
    println!("Breaking news! {}", item.summarize());
}
```


### Trait孤兒原則

Trait有個設定原則，**禁止拿外部的Traic，設定外部的程式**
舉個例子
- ✅ 拿Rust標準庫的Trait設定自己程式碼
- ✅自己程式碼Trait設定Rust標準庫
- ✅自己程式碼Trait設定自己的程式碼
- ❌拿Rust標準庫的Trait設定Rust標準庫

這最主要是防止有人亂搞Traic，來搞亂外部庫之間的關係
也算是避免過度耦合，以及防止程式出Bug情況


