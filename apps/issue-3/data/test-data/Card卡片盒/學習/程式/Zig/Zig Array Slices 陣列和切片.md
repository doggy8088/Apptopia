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
新建日期: 2026-02-14 01:45:35
---

基本上陣列就是一般認知那個
切片是跟python學的，就是可以將陣列資料切出一部分都出來
但python那邊切片，有可能會出現實例，但Zig是指針+長度包裝好
切割方式就是 **..** 像是 `[2..6](2,3,4,5 左閉右開)`就是第三個到第六個這樣
字串實際上也是一個陣列喔，只是外面拿到會是一個唯讀陣列指標`* const []u8`

> [!tip] 注意
> 在宣告中`[]u8`指的是說 **u8陣列的切片(包含指針)**
> `[8]u8`則是已經分配好8格子的實體陣列
> `*[]u8`如果這樣宣告是多此一舉，變成雙重指標

>[!warning] 
>在Zig有一種語法是`[*]u8` 這樣，
>這意思就跟C語言是一樣，我有指針，但我不知道長度
>就像把Zig切片，去掉長度保護這樣
>下面是AI評論
> **它是「C 語言指標」在 Zig 裡的化身。**
> **它是危險的**：因為它沒有長度邊界意識。
> **它是橋樑**：用於對接 C Code 或開發底層驅動。
 > **黃金準則**：**能用 `[]T` (切片) 就絕對不用 `[*]T`**。


```zig
const std = @import("std");

pub fn main() void {
    const array = [_]u8{ 1, 2, 3, 4, 5 };
    const slice1 = array[0..2]; // {1, 2}
    const slice2 = array[0..4]; // {1, 2, 3, 4}

    std.debug.print("Slice 1:\n", .{});
    std.debug.print("  {}, {}\n", .{ slice1[0], slice1[1] });
    std.debug.print("  Length: {}\n\n", .{slice1.len});

    std.debug.print("Slice 2:\n", .{});
    std.debug.print("  Length: {}", .{slice2.len});
}
```
