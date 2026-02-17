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
新建日期: 2026-02-14 02:41:15
---

這其實就跟一般一樣`if`，`else`、`elseif`
也跟C#一樣有三元運算子`const c = if (a > b) "A" else "B";`

比較特別是Null if 語法糖`if (object)|value|`就這樣，
意思是如果object**不是**null則value就是數據
一般上會加上else，用以拋null錯誤

```zig title:"Null IF"
const std = @import("std");

pub fn main() void {
    var a: ?u8 = 32;
    check(a);

    a = null;
    check(a);
}

fn check(a: ?u8) void {
    if (a) |value| { // Capture
        std.debug.print("Value: {}\n", .{value});
    } else {
        std.debug.print("Value: null\n", .{});
    }
}
```


# switch

這Switch比較特別，它跟[Rust match](../Rust/Rust%20match%20&%20if%20let.md)依樣
是對於輸入要窮舉的，算是跟C\C++最不一樣的地方

```zig
const print = @import("std").debug.print;

pub fn main() void {
    const http_code: u16 = 404;

    print("Statue: ", .{});
    switch (http_code) {
        400 => {
            print("Bad Request", .{});
        },
        403 => {
            print("Forbidden", .{});
        },
        404 => {
            print("Not Found", .{});
        },
        418 => {
            print("I'm a teapot", .{});
        },
        else => {
            @panic("Unknown");
        },
    }
}
```