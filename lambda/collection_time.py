import datetime

now2 = datetime.datetime.now().time()
today = datetime.date.today()

str_today = '2021-04-24'
date_today = datetime.datetime.strptime(str_today, '%Y-%m-%d')
date_today2 = date_today.date()

if today == date_today2:
    print('true')
else:
    print('false')

print(now2)
print(today,type(today))

print(date_today, type(date_today))
print(date_today2, type(date_today2))


limit = datetime.time(8,30) # AM8:30
print(limit)

def check_time_exceeded(now) -> bool:
    return now > limit


b = check_time_exceeded(now2)
print(b)