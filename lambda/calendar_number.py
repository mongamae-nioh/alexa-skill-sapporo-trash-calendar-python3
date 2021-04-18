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

class CalendarNoInWard:
    def __init__(self, ward):
        self.ward = ward
    
    def is_not_exist(self, number:int) -> bool:
        # because list starts zero.
        calendar_number = number - 1
        if not calendar_number in wardcalno[self.ward]:
            return True

a = CalendarNoInWard('nishi')

if a.is_not_exist(2):
    print('no exist')
else:
    print("ok")