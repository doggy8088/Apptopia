---
tags: 
- 程式語言/Rust 
aliases: 
來源: 
- "[[Rust 權威指南]]"
- "[[Rust 编程语言入门教程 2021]]"
新建日期: 2024-03-19 23:22:52
---

# 概念
就是C#的字典(Dictionary)，
遍歷部分，基本上跟[[Rust Vector#遍歷]]差不多，不要動hashMap
資料輸入到hashMap後使用權會消失的
比較大的差異在於，Rust替換數據時不能直接 **=** 處理，
一定要 `insert` 為了安全建議上用 `entry` 確認數據是否存在

```rust title:"HashMap宣告"
    use std::collections::HashMap;

    let mut scores = HashMap::new();

    scores.insert(String::from("Blue"), 10);
    scores.insert(String::from("Yellow"), 50);

    for (key, value) in &scores {
        println!("{key}: {value}");
    }
```


```rust title:"替換hashMap數據"
    let mut scores = HashMap::new();
    scores.insert(String::from("Blue"), 10);
    //entry是檢測是否有這數據存在
    scores.entry(String::from("Yellow")).or_insert(50);
    scores.entry(String::from("Blue")).or_insert(50);

    println!("{:?}", scores);
```
