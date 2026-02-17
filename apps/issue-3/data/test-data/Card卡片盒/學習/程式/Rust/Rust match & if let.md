---
tags:
  - 程式語言/Rust
aliases:
  - match
  - if let
來源:
  - "[[Rust 權威指南]]"
新建日期: 2024-02-21 22:41:42
---

# 概念

其實match & if let並不是[[Rust Enum枚舉]]專用
他可以用於單純的變數、[[Rust Struct|Struct]]上面，都可以
只是Enum限制，變成說只能使用這方式，來讓Enum讀出數據

## match

就是C# Switch，
只不過在Rust裡被要求安全的情況
match會要求輸入的條件的所有可能性
例如:輸入i8的話條件就要0~255全部這樣
但這不可能嘛，所以match有兩個特殊符號代替
**"other" 和 "_"** 兩者意思是一樣
差別在於other可以在後續設定讀到數據
"_"就不行

```Rust title:"match範例"
#[derive(Debug)] 
enum UsState {
Alabama,
Alaska,// --snip-- } 

enum Coin { 
Penny,
Nickel, 
Dime,
Quarter(UsState), 
} 

fn value_in_cents(coin: Coin) -> u8 { 
match coin { 
	Coin::Penny => 1, 
	Coin::Nickel => 5, 
	Coin::Dime => 10, 
	Coin::Quarter(state) => { println!("State quarter from {:?}!", state); 25 } 
	} 
} 

fn main() { 
value_in_cents(Coin::Quarter(UsState::Alaska));
}
```

```Rust title:"Match other _例子"
let dice_roll = 9;
match dice_roll { 
3 => add_fancy_hat(),
7 => remove_fancy_hat(), 
other => move_player(other),//<<這邊other就可以放入變數，"_"就什麼都沒
}
```

## if let

他會出現原因在於match太囉唆，所以後來Rust推出if let
就是 **"除此條件外，剩下全部丟棄"** ，
只不過Rust也提醒，if let 不會窮舉所以有一定程度的不安全，
所以要**小心使用**

```Rust title:"if let"
//下面兩告是邏輯等價

let mut count = 0; 
match coin { 
Coin::Quarter(state) => println!("State quarter from {:?}!", state),
_ => count += 1, 
}

let mut count = 0; 
if let Coin::Quarter(state) = coin { 
println!("State quarter from {:?}!", state); 
} else { 
count += 1; 
}

```