import pandas as pd
import mysql.connector
from mysql.connector import errorcode
from cursor import MyCursor

def create_database(cursor, db_name):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)
        
def create_db():
    db_name = "test2"
    
    tables = {}
    
    tables["hotel"] = (
        "CREATE TABLE `hotel` ("
        "hotel_id BIGINT(11) NOT NULL AUTO_INCREMENT,"
        "name varchar(255),"
        "country varchar(255),"
        "city varchar(255),"
        "street varchar(255),"
        "house_number varchar(6),"
        "zip_code varchar(7),"
        "PRIMARY KEY (`hotel_id`)"
        ") ENGINE=InnoDB;")
        
    tables["room"] = (
        "CREATE TABLE `room` ("
        "room_id BIGINT(11) NOT NULL AUTO_INCREMENT,"
        "room_type varchar(16),"
        "number_of_beds INT(11),"
        "price FLOAT(11),"
        "hotel_id BIGINT(11),"
        "PRIMARY KEY (`room_id`),"
        "CONSTRAINT `hotel-room` FOREIGN KEY (`hotel_id`) REFERENCES `hotel`(`hotel_id`) "
        "   ON DELETE CASCADE ON UPDATE RESTRICT"
        ") ENGINE=InnoDB;")
    
    tables["room_facilities"] = (
        "CREATE TABLE `room_facilities` ("
        "room_facility_id BIGINT(11) NOT NULL AUTO_INCREMENT,"
        "name varchar(255),"
        "description varchar(255),"
        "PRIMARY KEY (`room_facility_id`)"
        ") ENGINE=InnoDB;")
    
    tables["room_connect_room_facilities"] = (
        "CREATE TABLE `room_connect_room_facilities` ("
        "room_id BIGINT(11),"
        "room_facility_id BIGINT(11),"
        "PRIMARY KEY (`room_id`, `room_facility_id`),"
        "FOREIGN KEY (`room_id`) REFERENCES `room`(`room_id`),"
        "FOREIGN KEY (`room_facility_id`) REFERENCES `room_facilities`(`room_facility_id`)"
        ") ENGINE=InnoDB;")
    
    tables["user"]= (
        "CREATE TABLE `user` ("
        "user_id BIGINT(11) NOT NULL AUTO_INCREMENT,"
        "first_name varchar(255),"
        "last_name varchar(255),"
        "date_of_birth DATE,"
        "country varchar(255),"
        "city varchar(255),"
        "street varchar(255),"
        "house_number varchar(6),"
        "zip_code varchar(7),"
        "email varchar(255),"
        "phone_number varchar(255),"
        "PRIMARY KEY (`user_id`)"
        ") ENGINE=InnoDB;")
    
    tables["reservation"] = (
        "CREATE TABLE `reservation` ("
        "reservation_id BIGINT(11) NOT NULL AUTO_INCREMENT,"
        "checkout_date DATE,"
        "checkin_date DATE,"
        "number_of_guests INT(11),"
        "surcharge TINYINT(1),"
        "room_id BIGINT(11),"
        "user_id BIGINT(11),"
        "PRIMARY KEY (`reservation_id`),"
        "CONSTRAINT `room-reservation` FOREIGN KEY (`room_id`) REFERENCES `room`(`room_id`) "
        "   ON DELETE CASCADE ON UPDATE RESTRICT,"
        "CONSTRAINT `user-reservation` FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`) "
        "   ON DELETE CASCADE ON UPDATE RESTRICT"
        ") ENGINE=InnoDB;")

    tables["booking"] = (
        "CREATE TABLE `booking` ("
        "booking_id BIGINT(11) NOT NULL AUTO_INCREMENT,"
        "special_request varchar(255),"
        "payment_method varchar(255),"
        "date DATE,"
        "payment_status TINYINT(1),"
        "reservation_id BIGINT(11),"
        "PRIMARY KEY (`booking_id`),"
        "CONSTRAINT `reservation-booking` FOREIGN KEY (`reservation_id`) REFERENCES `reservation`(`reservation_id`) "
        "   ON DELETE CASCADE ON UPDATE RESTRICT"
        ") ENGINE=InnoDB;")
    
    tables["account"] = (
        "CREATE TABLE `account` ("
        "account_id BIGINT(11) NOT NULL AUTO_INCREMENT,"
        "password varchar(255),"
        "role varchar(255),"
        "loyalty_points INT(11),"
        "user_id BIGINT(11),"
        "PRIMARY KEY (`account_id`),"
        "CONSTRAINT `user-account` FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`) "
        "   ON DELETE CASCADE ON UPDATE RESTRICT"
        ") ENGINE=InnoDB;")

    tables["review"] = (
        "CREATE TABLE `review` ("
        "review_id BIGINT(11) NOT NULL AUTO_INCREMENT,"
        "rating FLOAT(11),"
        "comment varchar(255),"
        "date DATE,"
        "account_id BIGINT(11),"
        "hotel_id BIGINT(11),"
        "PRIMARY KEY (`review_id`),"
        "CONSTRAINT `account-review` FOREIGN KEY (`account_id`) REFERENCES `account`(`account_id`) "
        "   ON DELETE CASCADE ON UPDATE RESTRICT,"
        "CONSTRAINT `hotel-review` FOREIGN KEY (`hotel_id`) REFERENCES `hotel`(`hotel_id`) "
        "   ON DELETE CASCADE ON UPDATE RESTRICT"
        ") ENGINE=InnoDB;")
    
    tables["hotel_facilities"] = (
        "CREATE TABLE `hotel_facilities` ("
        "hotel_facility_id BIGINT(11) NOT NULL AUTO_INCREMENT,"
        "name varchar(255),"
        "description varchar(255),"
        "PRIMARY KEY (`hotel_facility_id`)"
        ") ENGINE=InnoDB;")
    
    tables["hotel_connect_hotel_facilities"] = (
        "CREATE TABLE `hotel_connect_hotel_facilities` ("
        "hotel_id BIGINT(11),"
        "hotel_facility_id BIGINT(11),"
        "PRIMARY KEY (`hotel_id`, `hotel_facility_id`),"
        "FOREIGN KEY (`hotel_id`) REFERENCES `hotel`(`hotel_id`),"
        "FOREIGN KEY (`hotel_facility_id`) REFERENCES `hotel_facilities`(`hotel_facility_id`)"
        ") ENGINE=InnoDB")
    
    tables["place_of_interest"] = (
        "CREATE TABLE `place_of_interest` ("
        "place_of_interest_id BIGINT(11) NOT NULL AUTO_INCREMENT,"
        "name varchar(255),"
        "description varchar(255),"
        "country varchar(255),"
        "city varchar(255),"
        "street varchar(255),"
        "house_number varchar(6),"
        "zip_code varchar(7),"
        "PRIMARY KEY (`place_of_interest_id`)"
        ") ENGINE=InnoDB")
    
    tables["hotel_connect_place_of_interest"] = (
        "CREATE TABLE `hotel_connect_place_of_interest` ("
        "hotel_id BIGINT(11),"
        "place_of_interest_id BIGINT(11),"
        "PRIMARY KEY (`hotel_id`, `place_of_interest_id`),"
        "FOREIGN KEY (`hotel_id`) REFERENCES `hotel`(`hotel_id`),"
        "FOREIGN KEY (`place_of_interest_id`) REFERENCES `place_of_interest`(`place_of_interest_id`)"
        ") ENGINE=InnoDB")
    
    # mydb = mysql.connector.connect(
    #     host="localhost",  # port erbij indien mac
    #     user="root",
    #     password="",
    # )
    c1 = MyCursor()
    
    mydb = c1.get_mydb()
    mycursor = c1.get_mycursor()
    # mycursor = mydb.cursor()
    print(type(mycursor))
    print(type(mydb))
    try:
        mycursor.execute("USE {}".format(db_name))
    except mysql.connector.Error as err:
        print("Database {} does not exists.".format(db_name))
    #     if err.errno == errorcode.ER_BAD_DB_ERROR:
    #         create_database(mycursor, db_name)
    #         print("Database {} created successfully.".format(db_name))
    #         mydb.database = db_name
    #     else:
    #         print(err)
    #         exit(1)
    # for table_name in tables:
    #     table_description = tables[table_name]
    #     try:
    #         print("Creating table {}: ".format(table_name), end='')
    #         mycursor.execute(table_description)
    #     except mysql.connector.Error as err:
    #         if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
    #             print("already exists.")
    #         else:
    #             print(err.msg)
    #     else:
            # print("OK")

    # mycursor.close()
    # mydb.close()
    

    
def main():
    df = pd.read_csv("Lijst_hotels_MRA_2012.csv", sep=";")
    df_hotel = df[["hotel_naam_2012", "straat", "postcode", "huisnummer", "plaats"]]
    df_hotel = df_hotel.rename(
        columns={
            "hotel_naam_2012": "name",
            "straat": "street",
            "postcode": "zip_code",
            "huisnummer": "house_number",
            "plaats": "city",
        }
    )
    df_hotel["country"] = "Netherlands"
    
    mydb = mysql.connector.connect(
        host="localhost",  # port erbij indien mac
        user="root",
        password="",
        database="hotel_project_yc_2401",
    )

    mycursor = mydb.cursor()
    
    add_hotel = ("INSERT INTO hotel "
               "(name, street, zip_code,  house_number, city, country) "
               "VALUES (%s, %s, %s, %s, %s, %s)")
    for i, row in df_hotel.iterrows():
        hotel_values = tuple([v for _,v in row.items()])
        mycursor.execute(add_hotel, hotel_values)
    mydb.commit()

    mycursor.close()
    mydb.close()

if __name__ == "__main__":
    create_db()
