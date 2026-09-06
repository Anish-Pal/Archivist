import re


def extract_citation_number(answer):

    numbers = re.findall(
        r"【(\d+)】",
        answer
    )

    converted_numbers = []

    for number in numbers:
        number = int(number)
        converted_numbers.append(number)

    unique_numbers = set(converted_numbers)

    sorted_numbers = sorted(unique_numbers)

    return sorted_numbers
    



def get_citations(answers , citations_map):

    numbers = extract_citation_number(answers)

    results = []

    for number in numbers:

        citation = citations_map.get(number)

        if citation is None:
            continue

        results.append({
            "number": number,
            "source": citation["source"],
            "page": citation["page"]
        })

    return results

    

