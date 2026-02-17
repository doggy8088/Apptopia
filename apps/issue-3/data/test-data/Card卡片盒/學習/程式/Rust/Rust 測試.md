---
tags: 程式語言/Rust 
aliases:
- 測試
來源: 
- "[[Rust 權威指南]]"
- "[[Rust 编程语言入门教程 2021]]"
- "[[為你自己學 Rust 系列]]"
新建日期: 2024-03-30 18:38:04
---

# 概念

這是透過`cargo`進行Rust程式碼測試只是
必須在`mod`、`fn`上面加上[[Rust 屬性 Attributes|屬性]]`#[cfg(test)]` `#[test]`
才能用`cargo test`進行測試
**assert_eq!** 就是斷言，斷言這數據應該要多少這樣，用來判斷程式碼對錯

```rust title:"Rust測試範例"
#[cfg(test)] 
mod bmi { 
use crate::bmi_calc; 

#[test] 
fn dummy() { 
	let result = 1 + 2; 
	assert_eq!(result, 3); 
} 

#[test] 
fn test_calc() { 
	let result = bmi_calc(180, 65); 
	assert_eq!(result, 20.1); 
	} 
} 

fn bmi_calc<T, U>(height: T, weight: U) -> f64 
where T: Into<f64>, U: Into<f64>, 
{ 
	let h = height.into() / 100.0; 
	let bmi = weight.into() / (h * h); 

	(bmi * 10.0).round() / 10.0 
} 

fn main() {}
```
