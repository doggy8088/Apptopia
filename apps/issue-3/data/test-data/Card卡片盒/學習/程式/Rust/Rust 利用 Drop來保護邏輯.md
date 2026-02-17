---
tags:
  - 程式語言/Rust
aliases:
  - Drop
  - 保護程式
  - 防護
  - Rust
來源:
  - https://rustwiki.org/zh-CN/rust-by-example/trait/drop.html
  - https://medium.com/@otukof/build-your-text-editor-with-rust-part-2-74e03daef237
新建日期: 2024-04-19 15:02:50
---

# 概念
Drop原本概念是，當這變數離開時，釋放掉該記憶體位置
只不過，在Rust中有個小技巧
就是讓一Struct(Manager之類重要的)實現Drop，
如果發生[[Rust 錯誤訊息#不可恢復訊息 - 恐慌 panic!|恐慌]]這樣惡性問題
因為Rust在發生時，為了保護程式碼，會逐一**釋放(Drop)**
所以可以透過這方式，將如果發生恐慌時的保護措施寫在Drop裡
這樣的話，可以減少程式的破壞，也可以想辦法救些資料回來這樣

```rust
struct CleanUp;

impl Drop for CleanUp {

    fn drop(&mut self) {
		    //保護程式碼的邏輯
			println!("離開");
    }

}
```