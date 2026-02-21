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
新建日期: 2026-02-14 02:06:21
---

# 概念

其實沒很難
就是這變數可以**Null**，對就這樣
因為Zig原則上禁止Null，但有的時候真的不知道，所以才有
使用很簡單，在宣告前面加上 **?** 就是`?u8`這樣

```zig
const std = @import("std");

pub fn main() void {
    var value: ?u8 = null;
    std.debug.print("Value: {?}\n", .{value});

    if (value == null) {
        value = 32;
    }
    std.debug.print("Value: {?}", .{value});
}

//輸出
Value: null
Value: 32
```

## orelse  unreachable

這兩是Zig的，算是語法糖的一種

orelse是指說，如果是Null那就執行**什麼**來賦予數值
unreachable就是，如果是Null就爆炸，不過如果在**ReleaseFast(快速模式)** 下會忽略掉，如果要真的爆炸可以接 **@panic("訊息")** 這就是直接炸了
unreachable語法糖是`.?`

```Zig
const std = @import("std");

fn getDefaultValue() u8 {
    std.debug.print("執行了 getDefaultValue!\n", .{});
    return 0;
}

pub fn main() void {
    var opt_value: ?u8 = null;

    // 當 opt_value 是 null，才會呼叫 getDefaultValue()
    const final_val = opt_value orelse getDefaultValue();
    
    std.debug.print("結果: {}\n", .{final_val});
}
```

```Zig

const value = opt_value orelse unreachable;
// 或者
const value = opt_value orelse @panic("為什麼這裡會是 null？");

```