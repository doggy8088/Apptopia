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
新建日期: 2026-02-14 01:23:17
---

# 概念

這概念在C# Java是沒有的
它意思是這樣，先設定一個結構，
但這結構裡的所有變數，是**共用**同一個記憶體空間
所以實際上在union只會存在一個變數是有東西的

它在官方文件是這樣描述.
>`union` 用來定義多型別單一值。
>如有某一個數值在概念上可以用多種型別表達，但同時只會是一種型別的話，就可以用 `union` 處理。
>`union` 的大小取決於其內部**最大**的成員。
>相較於 `struct` 是將所有成員加總，`union` 則是將所有成員「重疊」在同一個位址。

舉個例子，像是403、404、405這些，
他們是互斥的，因為錯誤只會是一種，所以就能設定union，
這樣就可以節省記憶體空間，不然用Struct設定，就會變成大一包


```zig
const std = @import("std");

const Result = union {
    int: u8,
    boolean: bool,
};

pub fn main() void {
    const res1 = Result{ .int = 32 };
    const res2 = Result{ .boolean = true };
    std.debug.print("Result: {}\n", .{res1.int});
    std.debug.print("Result: {}\n", .{res2.boolean});

    // Error
    // std.debug.print("Result: {}\n", .{res1.boolean});
    // std.debug.print("Result: {}\n", .{res2.int});
}

//輸出
Result: 32
Result: true
```

##  Tagged union(enum)

這是將union + enum 合在一起，
這好處就是**必定**只會是一個enum設定
配合[switch](Zig%20Enum.md)就能更好的設定狀態

```zig
const std = @import("std");

const Result = union(enum) {
    int: u8,
    boolean: bool,

    pub fn print(self: Result) void {
        switch (self) {
            Result.int => |value| std.debug.print("int: {}\n", .{value}),
            Result.boolean => |value| std.debug.print("boolean: {}\n", .{value}),
        }
    }
};

pub fn main() void {
    const res1 = Result{ .int = 32 };
    res1.print();

    const res2 = Result{ .boolean = true };
    res2.print();
}

//輸出
int: 32
boolean: true
```

