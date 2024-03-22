import csv
import re
from dataclasses import dataclass, fields
from datetime import datetime
from enum import Enum

import requests
from bs4 import BeautifulSoup



@dataclass
class CongressionalCandidate:
    name: str
    party: str
    office_name: str
    incumbent_status: str
    ballotpedia_id: str
    ballotpedia_bio_link: str
    ballotpedia_img_link: str

    # for printing to console
    def __str__(self):
        return (
            f"Candidate(name: {self.name}, party: {self.party}, office: {self.office_name}, incumbent_status: {self.incumbent_status},"
            f"bp_id: {self.ballotpedia_id}, bp_bio_link: {self.ballotpedia_bio_link}, bp_img_link: {self.ballotpedia_img_link})"
        )


class OfficeType(Enum):
    HOUSE = "House"
    SENATE = "Senate"


class CongressionalCandidateScraper:
    """This class scrapes either House or Senate candidates from ballotpedia for 2024 elections"""

    BASE_URL = f"https://ballotpedia.org/List_of_congressional_candidates_in_the_{datetime.now().year}_elections"

    def __init__(self):
        html_content = self.get_html_content_for_soup(self.BASE_URL)
        self.soup = BeautifulSoup(html_content, "html.parser")
        self.headers = [field.name for field in fields(CongressionalCandidate)]

    @staticmethod
    def get_html_content_for_soup(url):
        response = requests.get(url)
        return response.text

    def scrape_candidates_by_state(self, state: str, write_to_csv: bool):
        all_candidates: list[CongressionalCandidate] = []

        for office_type in OfficeType:
            table_pattern = re.compile(f'{office_type.value}{state}\d+')
            table_to_scrape = self.soup.find('table', {'id': table_pattern})

            if table_to_scrape:
                scraped_candidates_for_office: list[CongressionalCandidate] = self.scrape_candidates_from_table(table=table_to_scrape)
                all_candidates.extend(scraped_candidates_for_office)
            else:
                raise TypeError(f"There are no candidates found for the state of {state}")

        if write_to_csv:
            self.write_candidates_to_csv(state, all_candidates)
            return all_candidates


    @staticmethod
    def scrape_candidates_from_table(table):
        candidates = []

        for row in table.find_all('tr')[1:]:  # Skip the first row as it contains headers
            row_data = [td.text for td in row.find_all('td')]
            bp_img_link = row.find('img')['src']
            bp_bio_link = row.find('a')['href']
            candidate_name = row.find('a').text

            sub_detail_span = row.find('span', {'class': 'sub-detail'})
            if sub_detail_span:
                print(f"{row_data}:: subdetail span: {sub_detail_span.text.strip()}")
                incumbent_status = sub_detail_span.text.strip()
            else:
                incumbent_status = None

            bp_bio_link_split = bp_bio_link.split("/")
            bp_bio_link_split_last_part = bp_bio_link_split[-1]

            cand = CongressionalCandidate(
                name=candidate_name.strip(),
                party=row_data[1].strip(),
                office_name=row_data[2].strip(),
                incumbent_status=incumbent_status,
                ballotpedia_id=bp_bio_link_split_last_part,
                ballotpedia_bio_link=bp_bio_link,
                ballotpedia_img_link=bp_img_link,
            )

            candidates.append(cand)
        return candidates

    def write_candidates_to_csv(self, state, candidates):
        csv_file_name = f"{state}_congress_candidates.csv"

        with open(csv_file_name, mode="w", newline="") as file:
            writer = csv.writer(file)

            # Write the header
            writer.writerow(self.headers)

            # Write the data
            for candidate in candidates:
                writer.writerow(
                    [
                        getattr(candidate, field.name)
                        for field in fields(CongressionalCandidate)
                    ]
                )


def get_state_names():
    with open('state_names.txt', 'r') as file:
        state_names = file.readlines()
    state_names = [line.strip() for line in state_names]
    return state_names

if __name__ == "__main__":
    scraper = CongressionalCandidateScraper()  # create instance of scraper class

    # For a SINGLE STATE do this
    # Specify the state in camel-case (ie "California", "NewYork", etc) and congress office type Enum (OfficeType
    # SENATE or HOUSE and whether to write to CSV file or not)
    # candidates = scraper.scrape_candidates_by_state(state="Wisconsin", write_to_csv=True)

    # For MULTIPLE states, edit the 'state_names.txt' file with only the states you want and do this
    state_names = get_state_names()
    for state_name in state_names:
        candidates_for_state = scraper.scrape_candidates_by_state(state=state_name, write_to_csv=True)

    # for printing
    # for cand in candidates:
    #     print(cand.__str__())
