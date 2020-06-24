from pandas import DataFrame


def json_convert_to_dataframe(json_data):
    if "resultTable" not in json_data:
        return json_data

    table = json_data["resultTable"]
    headers = table["headers"]
    rows = table["rows"]
    columns = []
    for h in headers:
        for v in h.values():
            columns.append(v)

    data = []
    for row in rows:
        cells = row["cells"]
        cell_data = []
        for cell in cells:
            for cell_value in cell.values():
                cell_data.append(cell_value)
        data.append(cell_data)

    return DataFrame(data=data, columns=columns)
