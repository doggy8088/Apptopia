---
tags: 
- 程式語言/Rust 
aliases: 
來源: "[[Rust 權威指南]]"
新建日期: 2024-02-24 02:55:37
---

# 概念

就是C# List 

```Rust title:"Vector 宣告方式"
	//兩種都可以看自己喜歡，Rust有自動辨識
    let v: Vec<i32> = Vec::new(); 
    let v = vec![1, 2, 3];

	//新增數字到List
	v.push(4); 
```

## 讀取

Vector 讀取方式有兩個
- &
- get()

差異在於 **&** 如果超出範圍就直接掛掉 **get()**則是會跳[[Rust Enum獨特分支 Option(Null)|Null]]

```rust title:"Rust讀取Vector" 
    let v = vec![1, 2, 3, 4, 5];
    
    let third: &i32 = &v[2];
    //let third: &i32 = &v[100]; //<<這樣直接掛給你看
    println!("The third element is {third}");

	//這個超出也只會是Null用以保護程式
    let third: Option<&i32> = v.get(100); 
    match third {
        Some(third) => println!("The third element is {third}"),
        None => println!("There is no third element."),
    }
```

### 遍歷

Rust Vector雖然可以用for遍歷並進行更改，
唯一要注意是，對於**Vector本身**的更改
因為[[Rust 所有權#更動的數值類型??]]和[[Rust 引用#懸垂引用]]
這些對安全性的設計，在遍歷過程中，如果對Vector進行
添加、刪除等操作，Rust會過不了的

```rust title:"遍歷並更改數據"
let mut people = vec![  
    Person { name: String::from("Alice") },  
    Person { name: String::from("Bob") },  
];  
//這邊只更改"數據"本身，但"Vector"本身並未更改
for i in 0..people.len() {  
    people[i].name = String::from("Charlie");   
}
```


## Vector使用權

跟[[Rust 所有權#更動的數值類型??|更動數值的所有權]]差不多
Vector也屬於長度不固定的類型，所以一旦更動就會釋放掉記憶體
下面操作會讓Rust編譯器判定不行

```rust title:"Vector 使用權問題"
    let mut v = vec![1, 2, 3, 4, 5];

    let first = &v[0];

    v.push(6);//這邊無法加入，因為有不可變引用，所以禁止變更

    println!("The first element is: {first}"); 
```


## Vector Enum

這是[[Rust 權威指南]]提到的，
就是將Vector裡放入[[Rust Enum枚舉|Enum]]，
因為Rust的Enum可以放入數據，這樣的話就可以利用Vector存放大量不同數據了

>[!question] 為何這樣做
> 根據AI說明，這樣做好處在於方便
> 並且可以限制資料種類 
> 講是這樣，但感覺真沒必要，用Struct包Enum也行啊
