---
tags: 程式語言/Rust 
aliases: 別名
來源: "[[Rust 權威指南]]"
新建日期: 2024-07-21 00:43:34
---

這個很好解釋就是幫設定好的類型制定一個別名
例如
```rust
// 自定义错误类型  
#[derive(Debug)]  
pub enum ExprError {  
    Parse(String),  
}

pub type TestResult<T> = Result<T, ExprError>;
```
這意思是設定一個[[Rust 錯誤訊息#可恢復訊息 - 例外Resulf<T,E>|例外]]
名字叫`TestResult`類型就是 OK->泛型 和 Err->ExprError
