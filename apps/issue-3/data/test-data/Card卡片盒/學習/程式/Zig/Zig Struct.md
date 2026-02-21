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
新建日期: 2026-02-14 00:22:27
---

# 概念

Zig要取代C，所以不像C++那樣有Class功能，只有Struct
不過Struct裡面，有數據有函式，感覺也像Class

宣告Struct時，要用const，一樣要外部能用要用pub
Struct沒有建構子跟解構子，不像C#那樣寫上去就自動處理，
一般來說，會在Struct裡加入`init`函式當成建構子，
是當成程式人員的一個習慣，Struct建立就呼叫`init`釋放Struct就叫`deinit`


```zig
const std = @import("std");

const Point = struct {
    x: f32,
    y: f32,
    pub fn init(x: f32, y: f32) Point {
        return Point{ .x = x, .y = y };
    }
};

const Line = struct {
    p1: Point,
    p2: Point,
};

pub fn main() void {
    const l1 = Line{
        .p1 = Point.init(10, 12.5),
        .p2 = Point.init(20.2, 110),
    };
    std.debug.print("X: {d}, Y: {d}\n", .{ l1.p1.x, l1.p1.y });
    std.debug.print("X: {d}, Y: {d}  ", .{ l1.p2.x, l1.p2.y });
}
```
