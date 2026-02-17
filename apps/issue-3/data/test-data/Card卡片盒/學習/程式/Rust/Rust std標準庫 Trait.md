---
tags: 程式語言/Rust 
aliases: 
來源:  
新建日期: 2024-07-20 23:31:30
---

這文章用於紀錄Rust std標準庫裡的 Trait

# Struct 相關
## Display (Print顯示)
用於實作 print，讓Strcut可以顯示在外面，不用`{:?}`

## Default (Struct預設值)
無須use庫，Rust核心就有，
功能就是能直接設定預設值，效用跟C#的建構子差不多
就是該Struct新增時，就有預設數據，避免空數據問題

## From 和 Into
> https://rustwiki.org/zh-CN/rust-by-example/conversion/from_into.html#from-%E5%92%8C-into

這兩是一體兩面，
Form就是實作將一個Struct轉型成另一個Struct
Into就是From的倒過來，只不過實際上用不到，因為實作From就自動實作into


## Iterator 迭代器
迭代器是一Trait，讓實現的Struct可以迭代，
讓該Struct自For中循環，或是手動用程式Next下去，
也就是實現C#的Foreach跑Struct
因為Rust預設上Struct是沒有實現Iterator所以才這麼麻煩

```rust
struct Counter {
    count: u32,
    max: u32,
}

impl Counter {
    fn new(max: u32) -> Counter {
        Counter { count: 0, max }
    }
}

impl Iterator for Counter {
    type Item = u32;

    fn next(&mut self) -> Option<Self::Item> {
        if self.count < self.max {
            self.count += 1;
            Some(self.count)
        } else {
            None
        }
    }
}

fn main() {
    let counter = Counter::new(5);

    for num in counter {
        println!("計數: {}", num);
    }
}

```

像這案例，struct Counter實現Iterator後
`for num in counter`就會呼叫`fn next`來時做迭代功能

## Peekable 包裝器

Peekable可以當成將[[#Iterator 迭代器]]包裝後的Struct
[[#Iterator 迭代器]]有個缺點，當Next時會拋棄數據
Peekable則是會一直返回第一個，直到你Next他為止
雖然結果上看差不多，至少Peekable可以在程式上先進行判斷在Next

```rust
fn main() {
    // 創建一個範圍迭代器
    let iter = (1..5).peekable();

    // 使用 peekable 包裝迭代器
    let mut peekable_iter = iter.peekable();

    println!("當前值: {:?}",peekable_iter.peek());
    println!("拋棄第一個值 {:?}", peekable_iter.next());
    println!("拋棄後的當前值: {:?}",peekable_iter.peek());

}

```




# Error相關

## 實作Error  
使用這個Error時，必定要實作[[#Display]]用於輸出
這個Error就是 [[Rust 錯誤訊息#可恢復訊息 - 例外Resulf<T,E>]]的那個**E**
也就是說可以設定一個Struct OR Enum 使用Error
當函式返回時，輸出Err()就會丟出設定好的Error

```rust
use std::fmt::Display;  
  
// 自定义错误类型  
#[derive(Debug)]  
pub enum ExprError {  
    Parse(String),  
}  
  
impl std::error::Error for ExprError {}  
  
impl Display for ExprError {  
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {  
        match self {  
            Self::Parse(s) => write!(f, "{}", s),  
        }  
    }  
}  
  
fn test() -> Result<i32, ExprError> {  
    Err(ExprError::Parse("test".to_string()))  
}  
  
fn main() {  
    let result = test();  
    println!("{:?}", result);  
}
```

像這例子，ExprError是一Enum，
當test()回傳Err時，將錯誤數據塞到Enum裡
這樣在println!時也就可以輸出字串出來

std::error::Error好處在於，能設定自己要的Error類型，
透過這方式，可以打包數據丟回上一層作處理
在C#中如果傳例外出去，是可以把數據扔出去，
但實在是不太會去做，畢竟出例外就是準備爆了
Rust這方式其實也是安全性上的問題，因為Rust報例外就是要程式員處理



# 重載操作符 + - * / == !=

## 重載 "== !=" PartialEq 
```rust
#[derive(Debug)]
struct Point {
    x: i32,
    y: i32,
}

// 手動實現 PartialEq 特徵
impl PartialEq for Point {
    fn eq(&self, other: &Self) -> bool {
        self.x == other.x && self.y == other.y
    }
}

fn main() {
    let point1 = Point { x: 1, y: 2 };
    let point2 = Point { x: 1, y: 2 };
    let point3 = Point { x: 2, y: 3 };

    println!("point1 == point2: {}", point1 == point2); // true
    println!("point1 == point3: {}", point1 == point3); // false
}

```

## 重載 "+"  std::ops::Add 

```rust
use std::ops::Add;

#[derive(Debug)]
struct Point {
    x: i32,
    y: i32,
}

impl Add for Point {
    type Output = Point;

    fn add(self, other: Point) -> Point {
        Point {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}

fn main() {
    let point1 = Point { x: 1, y: 2 };
    let point2 = Point { x: 3, y: 4 };
    let result = point1 + point2;
    println!("{:?}", result); // Point { x: 4, y: 6 }
}

```

## 重載 "-"  std::ops::Sub

```rust
use std::ops::Sub;

#[derive(Debug)]
struct Point {
    x: i32,
    y: i32,
}

impl Sub for Point {
    type Output = Point;

    fn sub(self, other: Point) -> Point {
        Point {
            x: self.x - other.x,
            y: self.y - other.y,
        }
    }
}

fn main() {
    let point1 = Point { x: 3, y: 4 };
    let point2 = Point { x: 1, y: 2 };
    let result = point1 - point2;
    println!("{:?}", result); // Point { x: 2, y: 2 }
}

```


## 重載 "*"  std::ops::Mul
```rust
use std::ops::Mul;

#[derive(Debug)]
struct Point {
    x: i32,
    y: i32,
}

impl Mul<i32> for Point {
    type Output = Point;

    fn mul(self, scalar: i32) -> Point {
        Point {
            x: self.x * scalar,
            y: self.y * scalar,
        }
    }
}

fn main() {
    let point = Point { x: 1, y: 2 };
    let result = point * 3;
    println!("{:?}", result); // Point { x: 3, y: 6 }
}

```

## 重載 "> < >= <="  PartialOrd
```rust
use std::cmp::Ordering;

#[derive(Debug, PartialEq)]
struct Point {
    x: i32,
    y: i32,
}

// 實現 PartialOrd 特徵
impl PartialOrd for Point {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        let self_distance = (self.x.pow(2) + self.y.pow(2)) as f64;
        let other_distance = (other.x.pow(2) + other.y.pow(2)) as f64;
        self_distance.partial_cmp(&other_distance)
    }

    fn lt(&self, other: &Self) -> bool {
        self.x < other.x || (self.x == other.x && self.y < other.y)
    }

    fn le(&self, other: &Self) -> bool {
        self.x < other.x || (self.x == other.x && self.y <= other.y)
    }

    fn gt(&self, other: &Self) -> bool {
        self.x > other.x || (self.x == other.x && self.y > other.y)
    }

    fn ge(&self, other: &Self) -> bool {
        self.x > other.x || (self.x == other.x && self.y >= other.y)
    }
}

fn main() {
    let point1 = Point { x: 1, y: 2 };
    let point2 = Point { x: 2, y: 3 };

    println!("point1 < point2: {}", point1 < point2); // true
    println!("point1 <= point2: {}", point1 <= point2); // true
    println!("point1 > point2: {}", point1 > point2); // false
    println!("point1 >= point2: {}", point1 >= point2); // false
}

```
## 重載 "/"  std::ops::Div
```rust
use std::ops::Div;
## 重載 "/"  std::ops::Div

#[derive(Debug)]
struct Point {
    x: i32,
    y: i32,
}

impl Div<i32> for Point {
    type Output = Point;

    fn div(self, scalar: i32) -> Point {
        Point {
            x: self.x / scalar,
            y: self.y / scalar,
        }
    }
}

fn main() {
    let point = Point { x: 6, y: 8 };
    let result = point / 2;
    println!("{:?}", result); // Point { x: 3, y: 4 }
}

```

- `std::ops::Rem` 用於定義取模 (`%`)
- `std::ops::Neg` 用於定義負號 (`-`)
- `std::ops::BitAnd` 用於定義按位與 (`&`)
- `std::ops::BitOr` 用於定義按位或 (`|`)
- `std::ops::BitXor` 用於定義按位異或 (`^`)
- `std::ops::Shl` 用於定義左移 (`<<`)
- `std::ops::Shr` 用於定義右移 (`>>`)



# 其他
