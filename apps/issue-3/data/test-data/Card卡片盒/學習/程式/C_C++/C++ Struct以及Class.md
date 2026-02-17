---
tags : 
- 程式語言/C加加  
aliases :
來源 :
- https://zhuanlan.zhihu.com/p/47808468
- http://c.biancheng.net/view/2235.html
- "[[C++物件導向程式設計實務與進階活用技術]]"
- "[[C++程式設計的樂趣_範例實作與專題研究的程式設計課]]"
新建日期 : 2023-06-07 15:36:43
---
# Struct
在[[C++程式設計的樂趣_範例實作與專題研究的程式設計課]]書中其實作者很推崇Struct
基本裡解就是C#的Struct基本一樣，
只是C語言的Struct不能放入函式，C++的可以

# Class
C 並沒有 Class，是到C++才有的
C++ Class跟C#的完全一樣，基本上就是[[C++ 繼承|繼承]]之類的跟C#不同

# 差異
兩者在C++上差異不大，是有幾個不同
1. Struct不能使用[[C++ 範本|範本]]這功能而已
2. Struct繼承時預設是 **public** Class是**private**
3. Struct成員變數預設是 **public** Class是**private**

# 小結
所以在很多C++書中，會把Struct定義成資料集，Class定義成物件
這樣方便進行區分
