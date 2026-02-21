---
tags:
  - 程式語言/Rust
aliases: 
來源:
  - "[[Rust 權威指南]]"
新建日期: 2024-02-12 21:13:49
---

# 概念
引用概念，是從[[Rust 所有權|使用權]]衍生出來的
主要因為，如果所有都是權限，那很容易一直傳傳傳
會造成效能上的問題(一直釋放重寫)
所以才出現引用，引用簡單講
**我借給你值，但晚點要還我**
其實在底層看，就是新增一個指針，指著變數這樣
使用方式是在變數前面加上 **&**

> [!question]
> Q:那跟所有權差在哪??
> 其實就是差在權限處理上，所有權擁有所有權力，能對變數做任何事情
> 引用只能，讀+寫而已
> Q:那為何不直接用所有權?
> 引用能改善效能，並且保護變數，避免消失
> 
> **所以 "所有權" 跟 "引用" 是互補情況**

```Rust title:"引用範例"
fn main() {
    let s1 = String::from("hello");

    let len = calculate_length(&s1); //這邊用引用所以s1不會被釋放

    println!("The length of '{}' is {}.", s1, len);//所以 s1 len都讀的到
}

fn calculate_length(s: &String) -> usize {
    s.len()
}
```

![](../../../../Source來源筆記/圖片/Rust%20引用/Pasted%20image%2020240212220014.png)

## 可變引用

可變引用就是在 & 前加上 mut
但是!!，可變引用不能無限增加，因為會出現
多個引用改數值，會對記憶體造成問題
所以Rust限制說同時間只能存在**一個**可變引用，多個不可變引用
同時，程式順序也規定，不能出現可變一動，不可變也動到(指針跑掉了)


```Rust title:"可變引用範例"
fn main() { 
let mut s = String::from("hello"); 
change(&mut s); 
} 

fn change(some_string: &mut String) { 
some_string.push_str(", world"); 
}

---
OutPut : hello world
```

```Rust title:"引用順序問題"
let mut s = String::from("hello"); 
let r1 = &s; // 没问题 
let r2 = &s; // 没问题 
let r3 = &mut s; // 大问题 如果這變動到了，變成r1 r2指針就斷掉了
println!("{}, {}, and {}", r1, r2, r3);
```

## 懸垂引用

其實很好理解就是，引用的指針斷掉了，懸在那裏

```Rust title:"懸垂引用"
fn dangle() -> &String { // dangle 返回一个字符串的引用

    let s = String::from("hello"); // s 是一个新字符串

    &s // 返回字符串 s 的引用
} // 这里 s 离开作用域并被丢弃。其内存被释放。
  // 危险！
```


# 解引用
有時在數據傳遞時，是直接丟引用過去，但這時讀不到數據
就需要解引用，方法就是在變數前面加上 ** * ** 就行

# 小結

引用，實際上來看就是創造一個新的物件指針，指向記憶體位置
也因此Rust檢查器會對於這新的引用物件進行管控
**不管如何，變數的指針，如果有可能為空時，Rust就會報錯**