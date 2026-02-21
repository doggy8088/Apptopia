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
新建日期: 2026-02-14 00:39:27
---

# 概念

Zig Enum是跟C#那樣的
塞內容，最多塞數字，不像[Rust Enum枚舉](../Rust/Rust%20Enum枚舉.md)可以塞Struct
不過Zig Enum可以塞函式，但感覺有啥用就是了.....
Zig支援像是[Rust match](../Rust/Rust%20match%20&%20if%20let.md)的Switch
而且跟Rust要求窮舉，這算是Zig比較獨特的地方

```rust
const std = @import("std");

const Color = enum {
    red,
    blue,
    green,
    others,

    pub fn from_string(str: []const u8) Color {
        if (std.mem.eql(u8, str, "Red")) {
            return Color.red;
        } else if (std.mem.eql(u8, str, "Blue")) {
            return Color.blue;
        } else if (std.mem.eql(u8, str, "Green")) {
            return Color.green;
        } else {
            return Color.others;
        }
    }
};

  

pub fn main() void {
    const my_color = Color.from_string("Red");
    
    switch (my_color) {
        Color.red => std.debug.print("is red\n", .{}),
        Color.blue => std.debug.print("is blue\n", .{}),
        Color.green => std.debug.print("is green\n", .{}),
        Color.others => std.debug.print("is other\n", .{}),
    }

}
```


