---
tags:
  - 程式語言/Rust
aliases:
  - Rust例外
  - 例外
  - 恐慌
  - panic!
來源:
  - "[[Rust 權威指南]]"
  - "[[Rust 编程语言入门教程 2021]]"
  - "[[為你自己學 Rust 系列]]"
  - https://stackoverflow.com/questions/54055139/how-to-pass-rust-backtrace-1-when-running-a-rust-binary-installed-in-debian
新建日期: 2024-03-21 19:22:14
---

# 概念

Rust錯誤概念上跟C#的例外有點像，
但在於是Rust強行區分成 **錯誤** **例外** 兩大項
根據AI說法，這是為了安全、明確、不要太複雜
最簡單就是，C#例外一跳，很容易就是一堆`try crach`造成不方便這樣

# 不可恢復訊息 - 恐慌 panic!

很簡單，就是Rust直接掛掉，對！掛掉
但不是電腦掛掉，是終端知道發生什麼，停止程式碼並回朔

```rust title:"Rust恐慌"
panic!("crash and burn");
```

>[!note] 不顯示恐慌回朔
> Rust一般發生panic!時會回朔程式碼，
> 但如果不要回朔就在程式碼加上
>[stackoverflow 回朔恐慌panic方式](https://stackoverflow.com/questions/54055139/how-to-pass-rust-backtrace-1-when-running-a-rust-binary-installed-in-debian)
> ```rust title:"回朔"恐慌
> use std::env;
> fn main() {
>  // 這行要在main裡面才行，1=>回朔 0=>不回朔
> env::set_var("RUST_BACKTRACE", "1");
> }
> ```

>[!note] Rust輸出時不要"恐慌"，減小體積
> 偵測恐慌會增加打包的體積，如果不要只要在
> `cargo.toml`下加上
>```toml title:"打包去除恐慌偵測"
 >[profile.release]
 >panic = 'abort'
>```

# 可恢復訊息 - 例外Resulf<T,E>

Resulf是一個Enum，概念就真的是C#的例外
使用方式也很簡單用`match`去撈就好
下面範例就是用Rust開啟一個檔案
如果在就開啟，不在查看錯誤碼，如果是無此檔案就回傳Error，剩下就panic!
Error可以自訂使用Rust std標準庫[[Rust std標準庫 Trait#實作Error (std error Error)]]就可以
	
```rust title:"Rust Resu範例"
use std::fs::File;
use std::io::ErrorKind;

fn main() {
    let greeting_file_result = File::open("hello.txt");

    let greeting_file = match greeting_file_result {
        Ok(file) => file,
        Err(error) => match error.kind() {
            ErrorKind::NotFound => match File::create("hello.txt") {
                Ok(fc) => fc,
                Err(e) => panic!("Problem creating the file: {:?}", e),
            },
            other_error => {
                panic!("Problem opening the file: {:?}", other_error);
            }
        },
    };
}
```

## 語法糖

像範例看到的，`match`太多就像`if`嵌套太多很煩，所以Rust有語法糖
`unwrap`、`expect`
這兩功能一樣，如果OK就返回，不行就panic!，
差別在於`expect`可以自訂panic!訊息

```rust
use std::fs::File;

fn main() {
    let greeting_file = File::open("hello.txt").unwrap();
    let greeting_file = File::open("hello.txt")
        .expect("hello.txt should be included in this project");
}

//unwrap回傳內容
thread 'main' panicked at 'called `Result::unwrap()` on an `Err` value: Os {
//expect回傳內容
thread 'main' panicked at 'hello.txt should be included in this project: Error

```

## 可恢復消息傳遞 - 例外傳遞

這跟C#很像，就是在程式上寫出可能會出現得例外
宣告方式`fn 函式名稱() -> Result<正常結果,例外>`

```rust title:"Rust例外宣告方式"
use std::fs::File;
use std::io::{self, Read};

fn read_username_from_file() -> Result<String, io::Error> {
    let username_file_result = File::open("hello.txt");

    let mut username_file = match username_file_result {
        Ok(file) => file,
        Err(e) => return Err(e),
    };

    let mut username = String::new();

    match username_file.read_to_string(&mut username) {
        Ok(_) => Ok(username),
        Err(e) => Err(e),
    }
}
```

### 語法糖

像是例子顯示的，如果一直`return match`很麻煩，
所以Rust有個語法糖`?`
意思是如果對，程式就往下，不對這邊就彈例外回去


```rust title:"語法糖修改後"
use std::fs::File;
use std::io::{self, Read};

fn read_username_from_file() -> Result<String, io::Error> {
    let mut username_file = File::open("hello.txt")?;
    let mut username = String::new();
    username_file.read_to_string(&mut username)?;
    Ok(username)
}
```

# 什麼時候用panic! ? 什麼時候是 Result

根據AI和[[Rust 權威指南]]說明，有兩種

1. 驗證階段
如果是在驗證密碼，驗證資料時，出現不可能錯誤，
例如:要數字來字串，這種直接發panic!
因為程式在下去可能會造成資料甚至更多損害，
這時能根據Rust特性，Rust會關閉程式並回朔堆疊方式保護程式碼
發出panic!來確報後續資料安全

2. 原型階段 OR 測試
這情況就好解釋，畢竟在測試和設計，總會有問題

剩下情況大致就是發例外為準

>[!abstract] 總結
>Rust會這樣設計在於對程式碼安全的設計與考量，
>尤其panic!設計，不像其他語言一旦掛掉，可能危及資料或是程式碼
>這些也是用於安全考量

