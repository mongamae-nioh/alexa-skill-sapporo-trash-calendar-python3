trashtype = {
    1: "燃やせるごみ、スプレー缶類",
    2: "燃やせないごみ、乾電池、ライター",
    3: "容器、プラ",
    4: "びん、缶、ペット",
    5: "'雑がみ",
    6: "枝、葉、くさ",
    7: "収集なし"
}

def typecheck(typenumber) -> str:
    return trashtype[typenumber]
