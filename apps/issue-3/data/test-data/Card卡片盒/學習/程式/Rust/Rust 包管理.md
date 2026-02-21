---
tags: 
- 程式語言/Rust  
aliases: 
來源: 
- "[[Rust 權威指南]]"
- https://www.youtube.com/playlist?list=PL3azK8C0kje1DUJbaOqce19j3R_-tIc4_
- https://www.readfog.com/a/1653777218753630208
- https://stackoverflow.com/questions/36604010/how-can-i-build-multiple-binaries-with-cargo
- https://ithelp.ithome.com.tw/articles/10335657
- https://ithelp.ithome.com.tw/articles/10334833
新建日期: 2024-02-23 15:55:52
---

> [!NOTE] 注意
>  在這章節，[[Rust 權威指南]]寫的很爛
>  所以推薦是去 [Rust 编程语言入门教程 2021](https://www.youtube.com/playlist?list=PL3azK8C0kje1DUJbaOqce19j3R_-tIc4_)
>  這個講的比較好

# 概念

在Rust中分成三個
- Package
- Crate
- Module

## Package

Package只出現在Cargo上面，
會有一個**Cargo.toml**檔案
可以認為是一個項目，一個項目裡面有多個專案(Crate)

## Crate 

這在多個教學裡，說法都不同
> [為你自己學 Rust 套件（Crate）](https://ithelp.ithome.com.tw/articles/10335657)
> [Rust 入门教程 7.1 Package, Crate, Module](https://youtu.be/2wb607Jl4CE?si=1ctxSGwtZyHVE9Tx)
> [[Rust 權威指南]]

實際上看傾向說這是一個專案，
一個Crate可以有多個binary，但只能有0或1個library
binary就是可執行文件，也就是main
library很好理解就是運行用的函式庫


>[!note] 一個專案多個 binary
>  https://stackoverflow.com/questions/36604010/how-can-i-build-multiple-binaries-with-cargo
>  講是這樣但看過Cargo程式碼，人家直接接資料呼叫對應腳本
>  這真的有沒有用真不知


## Module 

這最好理解，就真的只是模組，
也就是C#的namespace
Rust關鍵字 **mod**

# 樹 Root

這是Rust最重要的概念
Rust Crate 有一個根，這根就是 main lib
所有的Mod必須建立在這2根上面，
為何這樣設計，根據AI說明
主要是安全、再來是封裝
所有屬於這專案的Module都只會屬於這Crate，每個Module有名有姓有家
不該屬於的只會出現在其他Library上
Cargo可以設定多個工作目錄(Crate)，這樣就可以在一個項目上分成多個不同專案去處理
如此達成安全跟封裝的概念

```Rust title:"Crate樹範例"
mod front_of_house {
	mod hosting { 
		fn add_to_waitlist() {} 
		fn seat_at_table() {} 
	} 

	mod serving { 
		fn take_order() {} 
		fn serve_order() {} 
		fn take_payment() {} 
	} 
}

crate //<這就是 main OR lib
 └── front_of_house //剩下這些都是Module
     ├── hosting
     │   ├── add_to_waitlist
     │   └── seat_at_table
     └── serving
         ├── take_order
         ├── serve_order
         └── take_payment
```

# Module設定

現在就是如何設定Module
Rust關鍵字 **mod** 如果要公開 **pub**
從子mod呼叫到父mod可以用**Super**關鍵字
私有項目只能呼叫到平級或是下級
這些基本上跟C#差不多

main呼叫函式，有**絕對路徑** **相對路徑**兩種
但這很麻煩，所以大多用 **use(就是C#using)** 處理
use還有個功能，因為Rust特性，Crate是基本都是獨立的，
所以會出現不同Crate會有同一個名稱的東西
可以用**use 模組 as 名稱**方式取別名

```Rust title:"Module設定"
mod nation {
    pub mod government {
        pub fn govern() {}
    }

    mod congress {
        pub fn legislate() {}
    }
    
    mod court {
        fn judicial() {
            super::congress::legislate();
        }
    }
}

fn main() {
    nation::government::govern(); //相對路徑
    crate::nation::government::govern(); //絕對路徑
}
```

```Rust title:"取別名"
mod nation {
    pub mod government {
        pub fn govern() {}
    }
    pub fn govern() {}
}
    
use crate::nation::government::govern;
use crate::nation::govern as nation_govern;

fn main() {
    nation_govern();
    govern();
}
```

### Mod; & Mod{} 差異
在Rust中 `mod XXX;` `mod XXX{}`有很大的差異， 
`mod XXX;`意思是引入在src/路徑/XXX 下的文件
`mod XXX{}` 意思是這段東西代表著mod XXX
意思不同，

```Rust
mod aTest //這就代表，main引用src下的叫做aTest的腳本

fn main(){}
```

#### main & lib 禁止互相mod
根據[[#Mod; & Mod{} 差異]]可知mod本身差異
那能不能說`main mod lib ??` 答案是:不行
必須是 `main use lib`
因為Rust編譯器是將main lib當成root來看
所以如果 lib 有在`mod 其他模塊`的話會出現鬼打牆問題
編譯器偵測main時，會說mod lib的東西要放在src下
偵測到lib時，會說lib東西要在src/lib下
然後就鬼打牆了

```rust
//這千萬不行雖然邏輯沒錯，但編譯器會鬼打牆
mod lib
fn main(){}

//這才對
use lib
fn main(){}
```
