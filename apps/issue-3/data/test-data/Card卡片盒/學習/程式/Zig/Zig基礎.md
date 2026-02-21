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
新建日期: 2026-02-13 01:53:45
---

# 概念
> Zig目前暫時還未1.0 (2026年0.16版)

Zig是取代[C\C++ ](C++%20MOC.md)而誕生的
他不像[Rust](Rust%20MOC.md)採用[生命週期](../../Card卡片盒/學習/程式/Rust/Rust%20生命週期.md)或是[所有權](../../Card卡片盒/學習/程式/Rust/Rust%20所有權.md)這種方式去開發
Zig的核心是**去掉隱藏的邏輯面**也就是開發上，不要存在邏輯語意不明的地方

Zig可以無縫接上C\C++語言只要用 @cimport 就可以
同時Zig有個更遠大的目標，不單單是取代C\C++
是讓Zig成為C\C++標準編譯器，這樣可以直接接上C\C++龐大的歷史遺留，並讓Zig寫新版部分，核心邏輯就可以沿用舊函式庫，最後統一編譯

# 語法

基礎上語法跟[C++](../C_C++/C++%20紀錄.md)很像

不過語法有幾點
1. 要求一定要有初始值(其實可以給undefined，但沒弄好編譯器報錯)
2. Zig會自動識別數據類型，但建議上最好手動寫上去
3. 要加上 pub 才能被外部其他程式調用 (var禁止)
4. var會嚴格執行，如果宣告後後面沒有用，編譯器會報錯
5. if的布林值只有true false 不像C 可以用1代表true

```Zig

const std = @import("std");


pub fn main() void {
    std.debug.print("Hello world!\n", .{});
    
    // var 可變 const不可變
    var a:u8 =0;
    const b:u8 =0;
    
    //函數可以放在變數裡
    const op = my_fun; // 賦值 
    const value = op(6); 
    std.debug.print("Value {d}\n", .{value});
   
}

fn my_fun(a: u8) u8 { 
	return a * 2; 
}

```

## 數值
跟Rust很像，宣告時加在後面

- `i8` 代表有號、8 bit 長度的整數
- `u8` 代表無號、8 bit 長度的整數
- `i16` 代表有號、16 bit 長度的整數
- `u128` 代表無號、128 bit 長度的整數
- `f32` 代表 32 bit 長度的浮點數
- `f64` 代表 64 bit 長度的浮點數
- `isize` 代表有號、指標長度的整數
- `usize` 代表無號、指標長度的整數

表達數值的方式有 2、8、10、16 進制，語法和多數語言相同：

```zig
const dec_int: u8 = 129;
const hex_int: u8 = 0x81;
const oct_int: u8 = 0o201;
const bin_int: u8 = 0b10000001;
```

如果有需要，可以在數字間加上底線 `_` 作爲分隔符，提升可讀性：

```zig
const dec_int: u64 = 1_000_000_000;
const hex_int: u64 = 0xFF12_3456_789A_0001;
const bin_int: u8  = 0b1000_0001;
```

浮點數可以使用科學記號表達：

```zig
const value: f32 = 2.5e6;  // 2500000
```

### 轉型

**整數 $\rightarrow$ 浮點數** **`@floatFromInt(x)`**將整數轉為對應的浮點值。
**浮點數 $\rightarrow$ 整數** **`@intFromFloat(x)`**會直接捨去小數點。
**小整數 $\rightarrow$ 大整數** **`@as(T, x)`**自動提升（如 `u8` 轉 `u16`），因為絕對安全。
**大整數 $\rightarrow$ 小整數** **`@intCast(x)`**可能會溢位，在 Debug 模式下會檢查。

### 運算子

- 數學：`+`、`-`、`*`、`/`、`%`
- 位元：`<<`、`>>`、`&`、`|`、`^`、`~`
- 邏輯：`and`、`or`、`!`
- 比較：`'=='`、`!=`、`>`、`>=`、`<`、`<=`

>> [!warning]
> 注意 **++** 和 ** \** **
> **++** 在Zig這不是像C++那樣+1，
> 是連結兩陣列意思
> ** \** ** 是陣列數據重複幾次

```zig title:"zig++意思"
  const le = [_]u8{ 1, 3 };
  const et = [_]u8{ 3, 7 };
  const leet = le ++ et; //輸出就是{1,3,3,7}
  
  const pattern = "A" ** 5; // 結果是 "AAAAA"
```

### 溢位

Zig有專門為溢位進行設計兩種方式

1. 繞回  255 +% 2  就會變成 1
2. 飽和  245 +| 11 就會是 255
也就是一個是像C#那樣溢為就回到0開始
飽和倒是很好玩，就是Zig先幫你最好max防護這樣

繞回是 `+%` `-%` `*%` 
飽和是 `+|` `-|` `*|`
記法就是繞回 %也就mod
飽和 | 就是一堵牆壁，擋住這樣


## 函式

函式屬於一等公民，
可以當成參數放進變數，或是做為參數放進函式裡
且一定要有明確設定是否有回傳值，沒有要寫**void**
回傳會有 **Null** 需要加上 **?**
回傳會有 **Error** 需要加上 **!**
這樣就可以讓上層函式強制處理

```Zig
const std = @import("std");

fn add(a: u8, b: u8) u8 {
    return a + b;
}

fn sub(a: u8, b: u8) u8 {
    return a - b;
}

// 注意：參數類型必須是 *const fn (...) ...
fn do_something(a: u8, b: u8, op: *const fn (u8, u8) u8) u8 {
    return op(a, b);
}

pub fn main() !void {
    // 這裡用 const 因為 val1 和 val2 沒有被修改
    const val1 = do_something(10, 2, add);
    const val2 = do_something(10, 2, sub);
    std.debug.print("Value1: {d}, Value2: {d}\n", .{ val1, val2 });
}
```

