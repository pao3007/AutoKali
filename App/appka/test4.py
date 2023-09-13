import re


def extract_wavelengths(arr):
    """
    Search for the string containing "WL:" and extract the pattern of numbers.

    Args:
    - arr (list or tuple): The list/tuple containing the strings.

    Returns:
    - list: A list of numbers found after "WL:". If not found, returns an empty list.
    """
    pattern = r'WL:\s*([\d]+[\/\-_][\d]+)nm'

    for item in arr:
        s = str(item)
        match = re.search(pattern, s)
        if match:
            return list(map(int, re.split(r'[\/\-_]', match.group(1))))

    return []


# Test
data = (
90732, 242358, 11, 'SAA-04; +/-2g; WL: 1573/1577nm; LCP-03: 2x1m; 2x FC/APC', 'FOS', '10 Startup Studio LLC ', 'SAA-01')
print(extract_wavelengths(data))
