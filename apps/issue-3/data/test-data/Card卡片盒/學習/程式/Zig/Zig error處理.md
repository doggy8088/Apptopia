---
tags:
  - 程式語言/C
  - 程式語言/C加加
  - 程式語言/Zig
aliases:
來源:
  - https://codeberg.org/ziglings/exercises/#ziglings
  - https://course.ziglang.cc
  - https://www.runoob.com/zig/zig-tutorial.html
新建日期: 2026-02-16 00:38:55
---

這是Zig比較特別的了，
Zig在error處理上，不像Rust要求窮舉方式處理
也不像C++ C# 那樣丟出來不管
Zig要求必須處理，但是將控制權給你，
簡單講Zig是我要你知道有error處理，但弄不弄是你的事情

用法上就是`try` `catch` `catch|value|`
`try`意思就是我知道有錯誤，所以解包吧
`catch` `catch|value|`就是如果有錯就執行 `|value|`就是抓到的error

錯誤宣告方面，可以用`||`方式將不同的error合併
宣告部分是`Err!u8`要用 `!`做宣告

```zig
const print = @import("std").debug.print;

const MyError = error{
    OutOfRange,
    NotFound,
};

pub fn main() void {
    const value = do_something() catch |err| {
        print("Error: {}\n", .{err});
        return;
    };
    print("Value: {}\n", .{value});
}

fn do_something() MyError!u8 {
    return MyError.OutOfRange;
    // return 1;
}

//輸出
Error: error.OutOfRange
```