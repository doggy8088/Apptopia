---
tags: 程式語言/Rust  
aliases: 
來源: "[[Rust 權威指南]]"
新建日期: 2024-02-19 23:27:29
---

# 概念
Enum概念上，跟其他語言的Enum一樣
差別在於
- Rust Enum可以放入數據
- 可以用[[Rust Struct#Struct Function 結構方法|Impl]]方式帶入函式
光是這兩個就改變很多程式上的寫法

## Rust Enum數據
Rust Enum可以帶入數據，
只不過讀取部分只能用
- [[Rust match & if let#match|match]] 
- [[Rust match & if let#if let|if let]]
這兩種方式讀取

```Rust title:"enum帶入數據"
enum Message { 
Quit,  //無數據
Move { x: i32, y: i32 }, //帶入Struct
Write(String), //字串
ChangeColor(i32, i32, i32),//I32元組 
}
```

```Rust title:"enum數據讀取"
enum CatBreed { 
Persian, 
AmericanShorthair, 
Mix(String, u8), 
} 

fn main() { 
let kitty = CatBreed::Mix(String::from("Kitty"), 8);
let nancy = CatBreed::Persian; greeting(&kitty); 
greeting(&nancy); 
} 

fn greeting(cat: &CatBreed) { 
	match cat { 
	CatBreed::Mix(name, age) => println!("我是米克斯，我叫 {}，我今年 {} 歲", name, age), 
	_ => println!("我是品種貓") } 
	}
```

## Enum 函式
enum可以用[[Rust Struct#Struct Function 結構方法|Impl]]方式帶入函式
跟Struct一樣，加上 **&self** 跟沒加上的有區別
```Rust title:"Enum 函式"
enum Message { 
Quit,
Move { x: i32, y: i32 }, 
Write(String), 
ChangeColor(i32, i32, i32), 
} 

impl Message { 
	fn call(&self) 
	{
		//這邊定義函式
	} 
}
```


# Enum VS Struct

> [!question] enum 跟 struct差異在哪?

根據AI說明，
本質來講，Enum 和 Struct**使用方式**是一樣的
差別在於
- Struct可以有多種數據，
  這些數據視為數據的結合體
- Enum則是，數據的不同狀態

所以當邏輯上是屬於一個東西不同狀態(HTTP狀態404 403那個)，應當用Enum處理

Struct則適用於數據獨立，並且需要靈活運用之狀況
