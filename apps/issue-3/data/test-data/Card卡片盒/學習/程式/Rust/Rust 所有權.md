---
tags:
  - 程式語言/Rust
aliases: 
來源:
  - "[[Rust 權威指南]]"
新建日期: 2024-02-12 17:47:00
---

# 概念
所有權在Rust很重要，
主要在防止記憶體洩漏([[C++ 指標#指標危險性|指針危險性]])，
原理就是，跟蹤所有變數，當變數不在需要就釋放掉
這有個好處
- 保護記憶體
- 取消回收機制(因為一沒用就釋放，自然不用回收CG)

定義上有3條規則
1. Rust 中的每一個值都有一個 **所有者（owner)**。
2. 值在**任一時刻有且只有一個**所有者。
3. 當所有者（變數）離開**作用域**，這個值將被丟棄。

## 作用域
這理解很簡單就是 **{}** 被大括號括住的區域
```Rust title:"作用域"
fn main() {  //作用域 A
	let a: i32 = 1;  
    {  //作用域 B
        let arrayA: [i32; 5] = [1, 2, 3, 4, 5];  
    }  //B 釋放  
} //A釋放
```

## 權限

這是使用權基本，
Rust規定，如果是會讓記憶體空間**更動**的數值類型(String，List之類)
則**禁止**出現**淺拷貝**，也就是同時有2指針指在他身上情況
如果是**不更動**(i32，bool <=因為一宣告，記憶體空間就固定了)則可以
但並非一定這樣，如果採用**深拷貝**，則沒有這問題
因深拷貝，是**複製**記憶體空間，所以就沒有指針問題
所以當發生新變數賦值，則會拋棄舊變數

```Rust title:"權限範例"
let s1 = String::from("hello");
let s2 = s1; 
println!("{}, world!", s1); //s1被移交到s2上，s1已經被釋放了
---
let s1 = String::from("hello"); 
let s2 = s1.clone(); 
println!("s1 = {}, s2 = {}", s1, s2); //這是深拷貝，所以 s1 s2都在
---
let x = 5; 
let y = x; 
println!("x = {}, y = {}", x, y);//因為x y都屬於不會變動，所以支持淺拷貝

```

### 函數情況
如果是導入到函數，也是一樣，遵循權限原則
類似String的，釋放
i32的保留，

```Rust title:"函數情況權限範例"
fn main() {
    let s1 = gives_ownership();         // gives_ownership 将返回值
                                        // 转移给 s1

    let s2 = String::from("hello");     // s2 进入作用域

    let s3 = takes_and_gives_back(s2);  // s2 被移动到，takes_and_gives_back 中
                                        // 釋放變數s2
                                        // 函式将返回值移给 s3
}  // 这里，s3 移出作用域并被丢弃。
   //s2 也移出作用域，但s2早已被移走，
  // 所以什么也不会发生。s1 离开作用域并被丢弃

fn gives_ownership() -> String {             
    let some_string = String::from("yours"); // some_string 进入作用域。

    some_string                              // 返回 some_string 
                                             // 并移出给调用的函数
}

// takes_and_gives_back 将传入字符串并返回该值
fn takes_and_gives_back(a_string: String) -> String { // a_string 进入作用域
                                                      // 

    a_string  // 返回 a_string 并移出给调用的函数
}
```

### 更動的數值類型??
像是String這種，會隨者改變數值而增減記憶體空間的
在Rust底層裡，當它被更動時就會自動釋放
並且這有汙染性質，即使只是[[Rust Struct|Struct]]裡有一個，也會被當成更動的數值


# 小結
其實逗那麼大圈，就一句話

**Rust禁止淺拷貝，轉移就釋放變數 **
**除非他是深拷貝，或是I32之類固定記憶體寬度**
