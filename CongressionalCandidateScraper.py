from bs4 import BeautifulSoup
import requests
import re
import csv
from enum import Enum


class CongressionalCandidate:
    def __init__(self, name, party, office_name, incumbent_status, bp_id, bp_bio_link, bp_img_link):
        self.name = name
        self.party = party
        self.office_name = office_name
        self.incumbent_status = incumbent_status
        self.ballotpedia_id = bp_id
        self.ballotpedia_bio_link = bp_bio_link
        self.ballotpedia_img_link = bp_img_link

    # for printing to console
    def __str__(self):
        return (f"Candidate(name: {self.name}, party: {self.party}, office: {self.office_name}, incumbent_status: {self.incumbent_status},"
                f"bp_id: {self.ballotpedia_id}, bp_bio_link: {self.ballotpedia_bio_link}, bp_img_link: {self.ballotpedia_img_link})")


class OfficeType(Enum):
    HOUSE = "House"
    SENATE = "Senate"


class CongressionalCandidateScraper:
    """This class scrapes either House or Senate candidates from ballotpedia for 2024 elections"""
    def __init__(self):
        html_content = self.get_html_content_for_soup_from_url()
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.headers = ['name', 'party', 'office_name', 'incumbent_status', 'bp_id', 'bp_bio_link', 'bp_img_link']

    @staticmethod
    def get_html_content_for_soup_from_url():
        url = "https://ballotpedia.org/List_of_congressional_candidates_in_the_2024_elections"
        response = requests.get(url)
        return response.text

    def scrape_candidates_by_state(self, state: str, congressional_seat_type: OfficeType, write_to_csv: bool):
        table_pattern = re.compile(f'{congressional_seat_type.value}{state}\d+')
        table_to_scrape = self.soup.find('table', {'id': table_pattern})

        if table_to_scrape:
            scraped_candidates_for_state = self.scrape_candidates_from_table(table=table_to_scrape)

            if write_to_csv:
                self.write_candidates_to_csv(state, congressional_seat_type, scraped_candidates_for_state)

            return scraped_candidates_for_state
        else:
            raise TypeError(f"There are no {congressional_seat_type} candidates found for the state of {state}")

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
                bp_id=bp_bio_link_split_last_part,
                bp_bio_link=bp_bio_link,
                bp_img_link=bp_img_link
            )

            candidates.append(cand)
        return candidates

    def write_candidates_to_csv(self, state, congressional_seat_type, candidates):
        csv_file_name = f"{state}_{congressional_seat_type.value}_candidates.csv"

        with open(csv_file_name, mode='w', newline='') as file:
            writer = csv.writer(file)

            # Write the header
            writer.writerow(self.headers)

            # Write the data
            for candidate in candidates:
                writer.writerow([candidate.name, candidate.party, candidate.office_name, candidate.incumbent_status,
                                 candidate.ballotpedia_id, candidate.ballotpedia_bio_link, candidate.ballotpedia_img_link])


if __name__ == "__main__":
    scraper = CongressionalCandidateScraper()  # create instance of scraper class

    # Specify the state in camel-case (ie "California", "NewYork", etc) and congress office type Enum (OfficeType
    # SENATE or HOUSE and whether to write to CSV file or not)
    candidates = scraper.scrape_candidates_by_state(state="Wisconsin",
                                                    congressional_seat_type=OfficeType.SENATE,
                                                    write_to_csv=True)
    # for printing
    # for cand in candidates:
    #     print(cand.__str__())
