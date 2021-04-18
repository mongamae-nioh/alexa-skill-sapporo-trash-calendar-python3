convert_dict = {
    "中央区": "chuo",
    "北区": "kita",
    "南区": "minami",
    "東区": "higashi",
    "西区": "nishi",
    "豊平区": "toyohira",
    "厚別区": "atsubetsu",
    "清田区": "kiyota",
    "手稲区": "teine",
    "白石区": "shiroishi"
}

class ComfirmWard:
    def __init__(self, ward):
        self.ward = ward
    
    @property
    def is_exist(self) -> bool:
        if self.ward in convert_dict:
            return True

    @property
    def alpha_name(self) -> str:
        return convert_dict[self.ward]