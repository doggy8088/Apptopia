---
tags : 
- 程式語言/C加加 
aliases :
來源 :
- "[[C++程式設計的樂趣_範例實作與專題研究的程式設計課]]"
- https://www.bilibili.com/video/BV1rb411d7mS/?p=54&share_source=copy_web&vd_source=25481608d8c6a8616f5a36f674ebd840
新建日期 : 2023-06-07 15:38:40
---

# 範本
首先最重要的一點**他不是C# 的泛型**雖然感覺很像
C++範本意思呢，就是這段函式或是Class只是一個**範本**無須編譯，用到在編譯
有點類似筆記範本，寫一個範本放在那，要用時就填寫上去這樣

## template function 範本函式
用法是 template \<  typename type \>
template是關鍵字，
typename只是一個單純的關鍵字，讓編譯器自己判斷型態這樣，也可以用int.....之類取代
type 就是變數名稱

```C
#include <iostream>
using namespace std;

template <typename type>
void Print(type value)
{
    cout<< value << endl;
}

int main()
{
    Print(5);
    Print<int>(5);//多加上<int>是強制讓編譯器認定是int這樣
}
```

## template class 範本類
範本類，一樣，用template \<  typename type \>方式處理

```C
#include <iostream>
#include <string>
using namespace std;

template <typename T, int size>
class Array {
  private:
  T m_Array[size];

  public:
  int GetSize() {
    return size;
  }
};

int main() {
  Array<string, 10> array;
  cout << array.GetSize() << endl;
}

```

### 範本小結

其實在[影片](https://www.bilibili.com/video/BV1rb411d7mS/?p=54&share_source=copy_web&vd_source=25481608d8c6a8616f5a36f674ebd840)中有說明，其實有些公司式禁止使用範本的
因為容易發生說，到後面已經搞不懂輸出出來的是什麼程式碼，
但多一個方法也是寫程式方便的做法

### 跟C#理解
範本跟C#的泛型相比，其實差異很大，雖然對結果要求是一樣的，
C++範本主要是給編譯器去執行他，有點類似動態方式生出程式碼
C#則是一個規則建立好，之後複製他這樣

所以如果站在物件導向上來看的話，
C++範本是以多型為原則而設計的
C#的則是以繼承為原則設計的，
差異在這邊


