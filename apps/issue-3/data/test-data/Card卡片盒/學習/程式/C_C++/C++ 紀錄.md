---
tags : 
- 程式語言/C加加
aliases :
來源 :
    - "[[C++程式設計的樂趣_範例實作與專題研究的程式設計課]]"
    - "[[C++物件導向程式設計實務與進階活用技術]]"
    - https://www.bilibili.com/video/BV1rb411d7mS/?p=6&share_source=copy_web&vd_source=25481608d8c6a8616f5a36f674ebd840
新建日期 : 2023-05-20 22:47:57
---
# 變數宣告

## 數字

![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230523165458.png)


> [!tip] 小技巧
> 如果數字過大的話能輸入， 單引號  **'** 符號做分隔，編譯器會自動忽略
> ```C
> int i = 65'535
> ```


## 各進制宣告
- 0b 二進制
- 0 開頭是八進制
- 0x 是 十六進制

> [!warning] 八進制注意
> 因為八進制是 0 開頭
> 所以會發生說
> ```C
> 	int A = 0129; 
> 	這樣會有問題因為是0開頭，數字會轉成8進制
> 	但有數字9所以編譯器會直接跳錯誤
> ```

## 浮點數

浮點數預設都是 double
也可以用科學記號方式宣告

![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230523173429.png)
![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230523173524.png)
### printf 列印方式

浮點數 printf 
- %f 有小數點
- %e 科學記號
- %g 是printf自行決定是 %f %e
如果數字較大要加上 l 也就是 %lg 這樣
書上是推薦統一用 **%g** 系列就好

![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230523173607.png)

## 字元

也就是文字變數

![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230523174027.png)

### 特殊字元
![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230523174128.png)

### UniCode字元

用 \\u 開頭
例如 A 就是 "\\u0041"這樣

### printf 列印方式

char 格式化是 %c
如果是wchar_t 是 %lc

## For迴圈

![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230523180004.png)

![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230523180017.png)

### For讀取陣列(就是foreach)

![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230523180051.png)


## const方法

只要在方法後面加上const則該方法，
無法修改該物件的任何狀態

![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230527144954.png)

## extern關鍵字
> https://cloud.tencent.com/developer/article/2099958
類似Static 但是可以給外部進行存取

## function const 
> https://blog.csdn.net/keineahnung2345/article/details/104082539

在函數定義後面加上const就成了const member function，
它的作用是確保在函數裡面不會有成員變數被意外地修改。在const member function內，
如果嘗試去修改任一成員變數，都會造成編譯錯誤。
![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230531165652.png)


# 物件

物件生命週期，基本上跟C#接近
Static為全域，要程式結束釋放，區域變數，當執行完後就釋放

## 刪除物件 delete
>https://www.runoob.com/note/15971

就是刪除物件，並釋放記憶體
如果該物件有解構子的話，就會執行
刪除陣列是用 ** delete[] **

## 靜態變數

要使用靜態變數時，需再後面加上 **::** 來使用

(這是C++ Struct = Class，
所以可以看成是Class裡面包者Static變數和函式，外面main要使用這樣)
![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230527160416.png)

<!--
C++程式設計的樂趣_範例實作與專題研究的程式設計課 
那本真的寫的很爛
後面那些也不知留不留，就註解掉
-->
<!--

## 執行緒靜態(待補 書中是 20章才講)

是在執行緒執行時才存在的靜態
使用thread_local關鍵字

## 案例

這是一個關於物件生命週期案例

![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230527161836.png)
![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230527161911.png)
![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230527161919.png)

根據案例能看到
新增的Class有5個
- 全域靜態  static Tracer
- 執行緒靜態  thread_local Tracer
- 區域變數 Tracer t3 
-  動態宣告變數 const auto* t4
那問題在哪，問題在T4這個上面
在main中動態宣告，但卻沒有delete，所以T4不會運行解構子

根據物件銷毀原則，
T4因為沒Delete所以不會運行解構子
T3因為main執行完了，所以銷毀
T2因為執行緒完了，才執行
T1是整個程式完了，所以執行
所以這案例能看出在C++中物件的生命週期




# 多型
## 執行階段多型
### interface介面
C++ 並沒有支援Interface關鍵字，所以需要有其他方式來處理繼承問題
利用virtual虛方法方式來製作，
用C#講法就是拿 Class +  virtual Function 來製作類似Interface的功能

#### 繼承案例
![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230531165219.png)

在圖中 
1號 virtual跟C#差不多一樣是虛方法的關鍵字
3號 **=0**這個可以理解成 C# 的 **abstract**關鍵字，將函式變成抽象函式
4號 就繼承
5號 override 覆寫方法 跟C#一樣

#### 虛擬解構子
這是書中特別強調的，也就是圖中2號的那個，
在書中解釋是說如果未加上 **解構子** 的話會發生說，
在多型狀態時，如果delete掉物件時，
可能會使解構子無法被觸發

##### 案例

![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230531170904.png)
![](../../../../Source來源筆記/圖片/C++%20紀錄/Pasted%20image%2020230531170924.png)

在案例中可以看到，當再多型 **BaseClass** 時，如果沒有**虛擬解構子**時
並沒法直接呼叫到繼承後的解構子，這也是書中一直提醒的問題





# Printf

> [C++ printf()用法及代碼示例](https://vimsky.com/zh-tw/examples/usage/cpp-programming_library-function_cstdio_printf.html)
> [printf用法大全，C语言printf格式控制符一览表](http://c.biancheng.net/view/159.html)

C++函式需要引入 cstdio
負責輸出文字到控制台
能使用 % 方式來引入參數

```C
#include <cstdio>

int main() {

	printf("Hello World \n");

    int i = 65535;
    printf("%hd\n", i); //這行會有問題，因hd是short用的，但65535已經超過short範圍所以會顯示錯誤
    printf("%d\n", i);

	return 0;
}
```

-->
