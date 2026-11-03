
def get_region(plate):
    regions = {
        "01": "Toshkent shahri",
        "10": "Toshkent viloyati",
        "20": "Sirdaryo viloyati",
        "25": "Jizzax viloyati",
        "30": "Samarqand viloyati",
        "40": "Farg'ona viloyati",
        "50": "Namangan viloyati",
        "60": "Andijon viloyati",
        "70": "Qashqadaryo viloyati",
        "75": "Surxondaryo viloyati",
        "80": "Buxoro viloyati",
        "85": "Navoiy viloyati",
        "90": "Xorazm viloyati",
        "95": "Qoraqalpog'iston Respublikasi"
    }

    plate = plate.upper().strip().replace(" ", "")

    if len(plate) < 2:
        return "Noma'lum hudud"

    code = plate[:2]

    for start, region in regions.items():
        if code == start:
            return region

    # Kodlar oraliqlarini ham tekshirish
    number = int(code) if code.isdigit() else -1

    if 1 <= number <= 9:
        return "Toshkent shahri"
    elif 10 <= number <= 19:
        return "Toshkent viloyati"
    elif 20 <= number <= 24:
        return "Sirdaryo viloyati"
    elif 25 <= number <= 29:
        return "Jizzax viloyati"
    elif 30 <= number <= 39:
        return "Samarqand viloyati"
    elif 40 <= number <= 49:
        return "Farg'ona viloyati"
    elif 50 <= number <= 59:
        return "Namangan viloyati"
    elif 60 <= number <= 69:
        return "Andijon viloyati"
    elif 70 <= number <= 74:
        return "Qashqadaryo viloyati"
    elif 75 <= number <= 79:
        return "Surxondaryo viloyati"
    elif 80 <= number <= 84:
        return "Buxoro viloyati"
    elif 85 <= number <= 89:
        return "Navoiy viloyati"
    elif 90 <= number <= 94:
        return "Xorazm viloyati"
    elif 95 <= number <= 99:
        return "Qoraqalpog'iston Respublikasi"

    return "Noma'lum hudud"


# Sinov
print(get_region("80 A 777 QA"))
print(get_region("01 B 123 CD"))
print(get_region("60 C 555 AA"))
