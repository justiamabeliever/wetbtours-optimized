from locust import task, SequentialTaskSet, FastHttpUser, HttpUser, constant_pacing, constant_throughput, events
from config.config import cfg, logger
from utils.assertion import check_http_response
from utils.non_test_methods import generateRandomCardNumber, open_csv_file, generateFlightsDates, generateFlightsDates
import sys, re, random
from urllib.parse import quote_plus, quote

class PurchaseFlightTicket(SequentialTaskSet): # класс с задачами (содержит основной сценарий)

    test_users_csv_filepath = './test_data/user_creds.csv'
    test_flights_data_csv_filepath = './test_data/flight_details.csv'
    
    test_users_data = open_csv_file(test_users_csv_filepath)
    test_flights_data = open_csv_file(test_flights_data_csv_filepath)

    post_request_content_type_header = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    def on_start(self):
        @task
        def uc00_getHomePage(self) -> None:
            logger.info(f"Test data for users is: {self.test_users_data}")

            self.client.get(
                '/WebTours/',
                name="req_00_0_getHomePage_/WebTours/",
                allow_redirects=False,
                # debug_stream=sys.stderr
            )

            self.client.get(
                '/WebTours/header.html',
                name="req_00_1_getHomePage_/WebTours/header.html",
                allow_redirects=False,
                # debug_stream=sys.stderr
            )
            r_02_url_param_signOff = 'true'
            self.client.get(
                f'/cgi-bin/welcome.pl?signOff={r_02_url_param_signOff}',
                name="req_00_2_getHomePage_cgi-bin/welcome.pl?signOff=true",
                allow_redirects=False,
                # debug_stream=sys.stderr
            )

            with self.client.get(
                f'/cgi-bin/nav.pl?in=home',
                name="req_00_3_getHomePage_/cgi-bin/nav.pl?in=home",
                allow_redirects=False,
                catch_response=True
                # debug_stream=sys.stderr
            ) as req00_3_response:
                check_http_response(req00_3_response, 'name="userSession"')
                # print(f"\n___\n req_00_3 response text: {req00_3_response.text}\n___\n")
            
            self.user_session = re.search(r"name=\"userSession\" value=\"(.*)\"\/>", req00_3_response.text).group(1)

            # logger.info(f"USER_SESSION PARAMETER: {self.user_session}")

            self.client.get(
                f'/WebTours/home.html',
                name="req_00_4_getHomePage_/WebTours/home.html",
                allow_redirects=False,
                # debug_stream=sys.stderr
            )

        @task
        def uc01_LoginAction(self) -> None:
            self.user_data_row = random.choice(self.test_users_data)
            logger.info(self.user_data_row)

            self.username = self.user_data_row["username"]
            self.password = self.user_data_row["password"]

            self.firstname = self.user_data_row["firstname"]

            # logger.info(f"chosen username: {self.username} / password: {self.password}")

            r01_00_body = f"userSession={self.user_session}&username={self.username}&password={self.password}&login.x=50&login.y=11&JSFormSubmit=off"

            with self.client.post(
                '/cgi-bin/login.pl',
                name='req_01_0_LoginAction_/cgi-bin/login.pl',
                headers=self.post_request_content_type_header,
                data=r01_00_body,
                # debug_stream=sys.stderr,
                catch_response=True
            ) as r_01_00response:
                check_http_response(r_01_00response, "User password was correct")

        uc00_getHomePage(self)
        uc01_LoginAction(self)

    @task
    def uc02_OpenFlightsTab(self):
        # generate uuid 6B29FC40-CA47-1067-B31D-00DD010662DA
     
   # logger.info(f"{uuid}: ")
        self.client.get(
            f'/cgi-bin/welcome.pl?page=search',
            name="req_02_0_OpenFlightsTab_cgi-bin/welcome.pl?page=search",
            allow_redirects=False,
            # debug_stream=sys.stderr
        )

        self.client.get(
            f'/cgi-bin/nav.pl?page=menu&in=flights',
            name="req_02_1_OpenFlightsTab_cgi-bin/nav.pl?page=menu&in=flights",
            allow_redirects=False,
            # debug_stream=sys.stderr
        )

        self.client.get(
            f'/cgi-bin/reservations.pl?page=welcome',
            name="req_02_2_OpenFlightsTab_cgi-bin/reservations.pl?page=welcome",
            allow_redirects=False,
            # debug_stream=sys.stderr
        )

    @task
    def uc03_FindFlight_InputParams(self):
        self.flights_data_row = random.choice(self.test_flights_data)

        depart = self.user_data_row["depart"]
        arrive = self.user_data_row["arrive"]
        self.seat_pref = self.flights_data_row["seat_pref"]
        self.seat_type = self.flights_data_row["seat_type"]

        dates_dict = generateFlightsDates()   

        r03_00_body = f"advanceDiscount=0&depart={depart}&departDate={dates_dict["depart_date"]}&arrive={arrive}&returnDate={dates_dict["return_date"]}&numPassengers=1&seatPref={self.seat_pref}&seatType={self.seat_type}&findFlights.x=56&findFlights.y=9&.cgifields=roundtrip&.cgifields=seatType&.cgifields=seatPref"
        # logger.info(f"uc03 request body: {r03_00_body}")
        
        
        with self.client.post(
            '/cgi-bin/reservations.pl',
            name='req_03_0_FindFlight_InputParams_/cgi-bin/reservations.pl',
            headers=self.post_request_content_type_header,
            data=r03_00_body,
            # debug_stream=sys.stderr,
            catch_response=True
        ) as r_03_0response:
            check_http_response(r_03_0response, "Flight departing from")
            self.outboundFlight = re.search(r"name=\"outboundFlight\" value=\"(.*)\" checked=\"checked\"", r_03_0response.text).group(1)
            # logger.info(f"____self.outboundFlight: {self.outboundFlight}")

    @task
    def uc04_ChooseFightOption(self):
        r04_00_body = f"outboundFlight={quote(self.outboundFlight)}&numPassengers=1&advanceDiscount=0&seatType={self.seat_type}&seatPref={self.seat_pref}&reserveFlights.x=61&reserveFlights.y=9"
        # logger.info(f"uc04 request body: {r04_00_body}")
        
        with self.client.post(
            '/cgi-bin/reservations.pl',
            name='req_04_0_ChooseFightOption_/cgi-bin/reservations.pl',
            headers=self.post_request_content_type_header,
            data=r04_00_body,
            # debug_stream=sys.stderr,
            catch_response=True
        ) as r_04_0response:
            check_http_response(r_04_0response, "Total for 1 ticket(s) is =")

    @task
    def uc05_ConfirmFlightBooking(self):
        self.firstname = self.user_data_row["firstname"]
        self.lastname = self.user_data_row["lastname"]
        self.street = self.user_data_row["street"]
        self.cityProvince = self.user_data_row["cityProvince"]
        self.exp_date = self.flights_data_row["exp_date"]

        r05_00_body = f"firstName={self.firstname}&lastName={self.lastname}&address1={quote(self.street)}&address2={quote(self.cityProvince)}&pass1={quote(self.firstname+ ' ' + self.lastname)}&creditCard={generateRandomCardNumber()}&expDate={quote(self.exp_date)}&oldCCOption=&numPassengers=1&seatType={self.seat_type}&seatPref={self.seat_pref}&outboundFlight={quote(self.outboundFlight)}&advanceDiscount=0&returnFlight=&JSFormSubmit=off&buyFlights.x=30&buyFlights.y=11&.cgifields=saveCC"
        # logger.info(f"uc05 request body: {r05_00_body}")
        
        with self.client.post(
            '/cgi-bin/reservations.pl',
            name='req_05_0_ConfirmFlightBooking_cgi-bin/reservations.pl',
            headers=self.post_request_content_type_header,
            data=r05_00_body,
            # debug_stream=sys.stderr,
            catch_response=True
        ) as r_05_0response:
            check_http_response(r_05_0response, "Thank you for booking through Web Tours.")
            # logger.info("WebToursBaseUserClass: uc05_ConfirmFlightBooking done!")
        

class WebToursBaseUserClass(FastHttpUser): # юзер-класс, принимающий в себя основные параметры теста
    wait_time = constant_pacing(cfg.webtours_base.pacing)

    host = cfg.url

    logger.info(f'WebToursBaseUserClass started. Host: {host}')

    tasks = [PurchaseFlightTicket]