---
tags: 
- 程式語言/Rust  
aliases: 
來源: "[[Rust 權威指南]]"
新建日期: 2024-02-19 21:43:48
---

# println 輸出

基本功，print輸出，輸出時在打上 **{:?}** **{:#?}**
要記得要在需要Debug的Struct或是Function上加上 **\#\[derive(Debug)\] **
可以顯示更多資料

或是使用dbg!()函式，也可以顯示
但是要注意這函式，雖然強大，但會讓程式碼很髒

```Rust
#[derive(Debug)] 
struct Rectangle { width: u32, height: u32, } 

fn main() { 
let rect1 = Rectangle { width: 30, height: 50, }; 
println!("rect1 is {:?}", rect1); 
dbg!(rect1);
}
```
