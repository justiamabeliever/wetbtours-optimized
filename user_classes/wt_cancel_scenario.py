from locust import task, SequentialTaskSet, FastHttpUser, HttpUser, constant_pacing, constant_throughput, events
from config.config import cfg, logger
from utils.assertion import check_http_response
from utils.non_test_methods import processCancelRequestBody, open_csv_file
import sys, re, random
from urllib.parse import quote_plus, quote

class CancelFlightTicket(SequentialTaskSet): # класс с задачами (содержит основной сценарий)

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
            # logger.info(f"Test data for users is: {self.test_users_data}")

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

            logger.info(f"USER_SESSION PARAMETER: {self.user_session}")

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

            logger.info(f"chosen username: {self.username} / password: {self.password}")

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
    def uc06_OpenBookedFlightsTab(self):
        self.client.get(
            f'/cgi-bin/welcome.pl?page=itinerary',
            name="req_06_0_OpenBookedFlightsTab_cgi-bin/welcome.pl?page=itinerary",
            allow_redirects=False,
            # debug_stream=sys.stderr
        )

        self.client.get(
            f'/cgi-bin/nav.pl?page=menu&in=itinerary',
            name="req_06_1_OpenBookedFlightsTab_cgi-bin/nav.pl?page=menu&in=itinerary",
            allow_redirects=False,
            # debug_stream=sys.stderr
        )

        with self.client.get(
            f'/cgi-bin/itinerary.pl',
            name="req_06_2_OpenBookedFlightsTab_cgi-bin/itinerary.pl",
            allow_redirects=False,
            # debug_stream=sys.stderr
        ) as response_06_2:
            check_http_response(response_06_2, "Flights List")
        
        self.flight_ids = re.findall(r'<input type=\"hidden\" name=\"flightID\" value=\"(.*)\"', response_06_2.text)
        self.flight_names = re.findall(r'<input type=\"hidden\" name=\"\.cgifields\" value=\"([0-9]{1,4})\"', response_06_2.text)

        logger.info(f"self.flight_ids: {self.flight_ids}")
        logger.info(f"self.flight_names: {self.flight_names}")

    @task
    def uc07_CancelOneTicket(self):
        if self.flight_ids:
            # logger.info('THERE ARE 1 OR MORE TICKETS!')

            req_07_0_body = processCancelRequestBody(self.flight_ids, self.flight_names)

            logger.info(f"req_07_0_body: {req_07_0_body}")

            with self.client.post(
                '/cgi-bin/itinerary.pl',
                name='req_07_0_CancelOneTicket_cgi-bin/itinerary.pl',
                headers=self.post_request_content_type_header,
                data=req_07_0_body,
                # debug_stream=sys.stderr,
                catch_response=True
            ) as r_07_00response:
                pass
                # check_http_response(r_07_00response, "User password was correct")
        else:
            logger.info(f'THERE ARE NO TICKETS FOR TEST USER: {self.username}')
        

class WebToursCancelUserClass(FastHttpUser): # юзер-класс, принимающий в себя основные параметры теста
    wait_time = constant_pacing(cfg.webtours_cancel.pacing)

    host = cfg.url

    logger.info(f'WebToursCancelUserClass started. Host: {host}')

    tasks = [CancelFlightTicket]