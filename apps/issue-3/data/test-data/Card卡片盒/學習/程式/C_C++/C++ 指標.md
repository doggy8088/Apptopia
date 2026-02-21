---
tags : 
- 程式語言/C加加 
aliases : 指針
來源 :
- "[[C++物件導向程式設計實務與進階活用技術]]"
- "[[C++程式設計的樂趣_範例實作與專題研究的程式設計課]]"
- https://www.bilibili.com/video/BV1rb411d7mS/?p=6&share_source=copy_web&vd_source=25481608d8c6a8616f5a36f674ebd840
- https://ithelp.ithome.com.tw/articles/10200288
- https://markdowner.net/skill/162160287443693568
- https://learn.microsoft.com/zh-cn/cpp/extensions/nullptr-cpp-component-extensions?view=msvc-170 
新建日期 : 2023-06-04 14:32:52
---

# 指標

指標也就是，指者記憶體空間的變數
不懂看下圖
![](../../../../Source來源筆記/圖片/C++%20指標/PTNV22D.jpg)

## 宣告指標

只要在宣告關鍵字後面加上 ** * ** 就是宣告
而print方式是 %p
取址方式是在變數前面加上 **&**
解析指標的話，是在變數前面加上 ** * **

### 小節
- 宣告型別後面加 ** * ** ▶️ 宣告指標 例: ** int* addresss**
- 變數前加 **&** ▶️  取記憶體位址  例:  addresss = **&value**
- 在指標 **變數** 前加 ** * **  ▶️ 解析指標內容 例: ** *addresss **  ^29cb0c

```C
int value = 0;
int* value_address = &value;
printf("原本數字 : %d \n", value);
printf("指標 : %p \n", value_address);
printf("指標解析 : %d",*value_address);
printf("\n");

*value_address = 100;

printf("更改數字 : %d \n", value);
printf("指標 : %p \n", value_address);
printf("指標解析 : %d", *value_address);
printf("\n");
```

### 指標用運算子 ->

-> 是指標用的運算子，解析指標內容並使用實體物件
還有種方式，是[[#^29cb0c|解析指標]]來呼叫

```C
class TestClass
{
public:
    void TestFun()
    {
        printf("Hello , I am TestClass Function use \n");
    }
};
int main(){
     TestClass myClass;
    TestClass* myClass_address = &myClass;
    printf("myClass 位置 %p \n",myClass_address);
    printf("使用myClass內函式 \n");
    myClass_address->TestFun();
    (*myClass_address).TestFun();
}
```

## 指標與陣列

指標與陣列關係在於，陣列是一個連續的記憶體空間
指標是單一一個設定關鍵字(int*)的指標
這看起來沒啥問題，但有一個重大問題!!!

### 陣列衰減

>[參考](https://markdowner.net/skill/162160287443693568)

用白話解釋是說，
當指標為函式的參數時，外部傳進陣列時，
函式裡的參數指標，會自動將陣列縮減

啥意思，我也搞不懂
書上跟網路都解釋不清楚

自己解釋是
陣列 = 指標 X 數量 
且陣列在記憶體上是連續的
當陣列傳入函式參數時，因為參數宣告是指標，
指標不可能同時指者多個陣列數據，所以指標就會改成，指向第一個這樣
所以只要多傳入陣列總共有幾個數據，就沒問題了

某種意義上也是C++的怪毛病，因為在C#等後續語言，都是傳入陣列，就是陣列，
C++不能直接傳陣列，要改成傳入陣列指標這樣

#### 案例
![](../../../../Source來源筆記/圖片/C++%20指標/Pasted%20image%2020230524190326.png)
![](../../../../Source來源筆記/圖片/C++%20指標/Pasted%20image%2020230524190333.png)

### 處理陣列衰減

![](../../../../Source來源筆記/圖片/C++%20指標/Pasted%20image%2020230524190743.png)
![](../../../../Source來源筆記/圖片/C++%20指標/Pasted%20image%2020230524190753.png)

###  指標危險性

指標的危險在於，指標實際上是直接控制記憶體位址的，
但實際上如果發生C++邏輯錯誤，就會導致控制到錯誤的位址，
這樣就會造成無法預期的錯誤，輕則數據損失，重則程式掛掉

### nullptr 
> [nullptr](https://learn.microsoft.com/zh-cn/cpp/extensions/nullptr-cpp-component-extensions?view=msvc-170)

nullptr是一關鍵字(在VS裡面是的)，是指標專用，意思是**空的**
白話講就是指標專用 null ，能讓指標預先設定的空給他這樣

## 參照 reference

參照可以理解成安全又簡易的指標，
修正部分指標BUG這樣
使用方式，是在函式參數前面加上 ** & ** 符號

#### 案例
![](../../../../Source來源筆記/圖片/C++%20指標/Pasted%20image%2020230527143541.png)


### 參照和指標

根據書中說法，參照和指標是能互換使用，
但參照無法移動記憶體位置，所以向是陣列就無法使用。




