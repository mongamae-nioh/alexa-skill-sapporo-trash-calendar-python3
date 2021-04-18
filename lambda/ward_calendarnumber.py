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

wardcalno = {
    "chuo": list(range(1,6)),
    "kita": list(range(1,6)),
    "minami": list(range(1,7)),
    "higashi": list(range(1,6)),
    "nishi": list(range(1,4)),
    "toyohira": list(range(1,4)),
    "atsubetsu": list(range(1,4)),
    "kiyota": list(range(1,2)),
    "teine": list(range(1,2)),
    "shiroishi": list(range(1,4)),
}

class ComfirmWard:
    def __init__(self, ward:str):
        self.ward = ward
    
    @property
    def is_not_exist(self) -> bool:
        if not self.ward in convert_dict:
            return True

    @property
    def alpha_name(self) -> str:
        return convert_dict[self.ward]

class CalendarNoInWard:
    def __init__(self, ward):
        self.ward = ward
    
    def is_not_exist(self, number:str) -> bool: # Because Alexa recognizes it as a string
        # because list starts zero.
        calendar_number = int(number) - 1
        if not calendar_number in wardcalno[self.ward]:
            return True