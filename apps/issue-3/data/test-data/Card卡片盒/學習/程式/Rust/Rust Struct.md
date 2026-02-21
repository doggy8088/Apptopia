---
tags:
  - 程式語言/Rust
aliases: 
來源:
  - "[[Rust 權威指南]]"
新建日期: 2024-02-19 17:12:16
---

Rust沒有Class概念，有的是Struct + [[Rust Trait 特徵]]這兩個
Struct 基本上跟其他語言的Struct差不多，用於宣告數據結構

# Struct

Struct 基本上就直接宣告就好，

```Rust title:"Struct宣告"
struct User { 
active: bool, 
username: String, 
email: String, 
sign_in_count: u64, 
}
```

Rust Struct 有個 語法糖 **".."**
就是在宣告後面加上 .. 就會將設定來源的Struct數據輸入進去
但要注意，如果來源的Struct含有[[Rust 所有權#權限|會變動的數據類型]]
則來源的Struct會釋放掉，除非新數據有改掉

```Rust title:"Struct轉移"
let user1 = User { 
email: String::from("someone@example.com"), 
username: String::from("someusername123"), 
active: true, 
sign_in_count: 1, }; 

let user2 = User { 
email: String::from("another@example.com"), 
..user1 };// <<代表，除了email數據外，剩下數據都由user1來
```

```Rust title:"Struct轉移但不想要權消失"
fn main() { 
let user1 = User { 
email: String::from("someone@example.com"), 
username: String::from("someusername123"), 
active: true, 
sign_in_count: 1, }; 

let user2 = User { 
email: String::from("another@example.com"), 
..user1 }; } //<<如果這樣寫 user1會釋放掉讀不到

let user3 = User { 
email: String::from("another@example.com"), 
username: String::from("AAAAAAAAAAAA"), 
..user1 
};} //<<這樣寫 user1就不會釋放
```

## Tuple Struct 元組結構體

基本上[[Python 基本#元組(tuple)]]一樣，就只是不用一直打這樣子
只是Tuple Struct 不能給予名字，所以還是用Struct

```Rust title:"元組結構體"
struct Color(i32, i32, i32);
struct Point(i32, i32, i32);

fn main() {
    let black = Color(0, 0, 0);
    let origin = Point(0, 0, 0);
}
```

## unitStruct 單位結構體

這基本上不會用，這主要是用在那種程式碼有要回傳之類的，可能出現

```Rust 
struct AlwaysEqual; 
fn main() { 
let subject = AlwaysEqual;
}
```

# Struct Function 結構方法

就是將函式附在Struct下，類似C# Class下包在裡面的函式概念
使用**impl**關鍵字，來表示要對該Struct加入函式
如果在函式裡加上 **&self**，這樣代表，這函式可以讀到Struct裡的變數
如果沒有，則是單純函式掛在該Struct下面
用C#比喻就是，&self函式就是單純Class下的函式
沒有的就是Static函式，外部呼叫就是透過Class名來找到他
Rust也是，如果沒有&self的話，要用 **::** 來呼叫

```Rust
#[derive(Debug)]  
struct Rectangle {  
    width: u32,  
    height: u32,  
}  
  
impl Rectangle {  
    fn area(&self) -> u32 {  //單純Class函式
        self.width * self.height  
    }  
  
    fn iamTest() -> String {  //類似Static函式
        return String::from("AAAAA");  
    }  
}  
  
fn main() {  
    let rect1 = Rectangle { width: 30, height: 50 };  
    println!("{}", rect1.area());  
    println!("{}", Rectangle::iamTest());  
}
```

