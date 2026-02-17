---
tags : #程式語言/C加加  
aliases :
來源 :
- "[[C++物件導向程式設計實務與進階活用技術]]"
- https://blog.51cto.com/u_15055361/5537014
新建日期 : 2023-06-07 17:19:18
---

# 資料流(Stream)

資料流概念就是，
將二進位資料，流向目的地，最終為我們所用

C++目前有幾個處理IO類別
![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230607202817.png)
![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615133036.png)

## 隨機與循序存取

循序是存取，就是一般常見的txt檔案之類，也就是檔案是有一定規律，
隨機則是，將檔案變成二進制，並切個成固定大小，以隨機方式排列，最重要好處是安全

# C++ 輸入輸出

要執行C++ IO 要引入標頭檔

![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615124010.png)

## 檔案開啟

![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615124131.png)
![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615124413.png)
### 游標操控 

C++ 可以控制游標操控位置，來成說你想寫入的位置或是讀取位置
```C
fileInTest.seekg(0, fileInTest.beg);
```
![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615134542.png)

### 確認檔案開啟是否有誤

![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615124431.png)

### 檔案關閉

切記一定要在C++裡關閉資料流，不然檔案會被鎖住
![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615124555.png)

### 例子

```C
#include <cstdio>
#include <fstream>
#include <iostream>
using namespace std;

int main(){
ifstream fileTest;

fileTest.open("C:\\Users\\Peter\\Desktop\\CPlusPlusTest\\CPlusPlusTest\\Test.txt",ios::out);

    if (fileTest.is_open() == false)
    {
        cout << "檔案無法開啟" << endl;
    }
    else
    {
        cout << "檔案開啟" << endl;
        cout << "檔案關閉資料流" << endl;
        fileTest.close();
    }
}
```



## 操作文字檔

C++ 寫入文字是使用 **<<** 這符號來表示，讀取則是反過來 **>>**
```C
file << "寫入"
fin>>str //讀取
```
C++ 也是有提供方便的函式
![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615125641.png)
![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615125650.png)

### 例子

```C
#include <cstdio>
#include <fstream>
#include <iostream>
using namespace std;

int main()
{
    //寫入
    cout << "寫入測試" << endl;
    cout << endl;

    ofstream fileOutTest;
    fileOutTest.open(
        "C:\\Users\\Peter\\Desktop\\CPlusPlusTest\\CPlusPlusTest\\Test.txt",
        ios::out);

    if (fileOutTest.is_open() == false)
    {
        cout << "檔案無法開啟" << endl;
    }
    else
    {
        cout << "檔案開啟" << endl;
        fileOutTest << "我是測試資料" << endl;
        fileOutTest << "HelloWorld" << endl;
        cout << "檔案關閉資料流" << endl;
        fileOutTest.close();
    }


    //讀取
    cout << endl;
    cout << "讀取測試" << endl;
    cout << endl;

    string str;
    char data[100];
    char oneChar;
    ifstream fileInTest;
    fileInTest.open(
        "C:\\Users\\Peter\\Desktop\\CPlusPlusTest\\CPlusPlusTest\\Test.txt");

    //讀取一個字元
    cout << "讀取一個字元 get" << endl;
    for (size_t i = 0; i < 10; i++)
    {
        fileInTest.get(oneChar);
        cout << oneChar;
    }
    //游標返回開頭
    fileInTest.seekg(0, fileInTest.beg);
    cout << endl;
    cout << endl;

    //讀取資料，直到遇到 換行符號(\n)
    cout << "讀取getline" << endl;
    fileInTest.getline(data,sizeof(data));
    cout << data << endl;
    //游標返回開頭
    fileInTest.seekg(0, fileInTest.beg);
    cout << endl;

    //用">>"讀取
    cout << "讀取 用\">>\"讀取" << endl;
    fileInTest >> str;
    while (fileInTest.eof() == false)
    {
        cout << str << endl;
        fileInTest >> str;
    }

    fileInTest.close();
}
```



## 操作2進制文件

二進制文件，雖然不可讀，但優點在於快速、占用小、可以隨機儲存

![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615133950.png)
![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615134002.png)
![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615134019.png)

![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615134035.png)
![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615134045.png)
![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615134058.png)

### 二進制存取

![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615134504.png)

#### 例子

![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615134700.png)
![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615134720.png)
![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615134735.png)
![](../../../../Source來源筆記/圖片/C++%20輸入輸出/Pasted%20image%2020230615134743.png)