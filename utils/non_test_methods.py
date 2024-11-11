import csv, random
from datetime import datetime, timedelta
from urllib.parse import quote_plus

def open_csv_file(filepath=str):
    with open(filepath, "r") as file:
        reader = csv.DictReader(file)
        return list(reader)

def generateFlightsDates(): #1st date 3-10days / 2nd date 15-30
    dates_list = {}
    
    dates_list["depart_date"] = quote_plus((datetime.now() + timedelta(days=random.randint(3,10))).strftime("%m/%d/%Y"))
    dates_list["return_date"] = quote_plus((datetime.now() + timedelta(days=random.randint(15,30))).strftime("%m/%d/%Y"))

    return dates_list

def generateRandomCardNumber():
    return random.randrange(10**15, 10**16)

def processCancelRequestBody(ids_list=list, names_list=list):

    cgi_part = ".cgifields="+"&.cgifields=".join(names_list) # соединение массива по "джойнеру": &.cgifields=
    static_part = "&removeFlights.x=62&removeFlights.y=14" 
    flights_part = "flightID="+"&flightID=".join(ids_list) # соединение массива по "джойнеру": &flightID=
    todelete_part = f"{names_list[random.randrange(0, int(len(names_list)))]}=on" # формирование случайного значения из листа names_list по случайному индексу
    
    result = f"{todelete_part}&{flights_part}&{cgi_part}&{static_part}" # формирование результирующей строки с помощью конкатенации строк
    
    return result

    
    

    


    

