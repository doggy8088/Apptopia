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
新建日期: 2026-02-16 00:24:30
---

迴圈部分則跟一般一樣`while` `for` 兩大項
`break` ， `continue`也有

# while

語法是
`while (count > 0) : (count -= 1) {}`
前面是條件部分，`:`後面意思是，迴圈要進入重複前一定要執行的
這樣可以避免說，忘了寫條件情況，結果進入死迴圈
另一種是
`while (b) |value| {}`
意思就是如果 b 不是 Null 則 value就是值，並進入迴圈

```zig
const print = @import("std").debug.print;

pub fn main() void {
    var count: u8 = 10;
    while (count > 0) : (count -= 1) {
        print("{}, ", .{count});
    }
    print("\nEnd", .{});
}

//輸出
//10, 9, 8, 7, 6, 5, 4, 3, 2, 1,
//End
```


# for

其實zig的for其實更接近C#的foreach
語法是
`for(array,0..)|value,index|{}` 或是
`for(array)|value|{}`
如果要純數字
`for(0..6){}`


```zig
const print = @import("std").debug.print;

pub fn main() void {
    const number_set = [_]u8{ 1, 3, 4, 5, 7, 8 };

    for (number_set, 0..) |num, index| {
        print("Value{}: {}, ", .{ index, num });
    }
}
```