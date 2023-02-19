#!/usr/bin/env python3

import re
import subprocess
import urllib.request
from bs4 import BeautifulSoup


def clean_name(name):
    name = name.replace("Fairphone FP", "Fairphone ")
    name = name.replace("Fairphone 3 and 3+", "Fairphone 3/3+")
    name = re.sub(r"^asus ", "ASUS ", name, flags=re.IGNORECASE)
    name = re.sub(r"^ZUK Z2 Plus", "ZUK Z2 Plus", name, flags=re.IGNORECASE)
    name = name.replace("Zenfone", "ZenFone")
    name = re.sub(r"^Pixel ", "Google Pixel ", name)
    name = re.sub(r"^Galaxy ", "Samsung Galaxy ", name)
    name = re.sub(r"^Yu ", "YU ", name)
    name = re.sub(r"^Bq ", "BQ ", name)
    name.replace("F(x)tec Pro1", "F(x)tec Pro¹")

    if name.count('"') == 1:
        name = name.replace('"', "")

    parts = name.split()
    if len(parts) > 1 and parts[0] == parts[1]:
        name = " ".join(parts[1:])

    return re.sub(r"\s+", " ", name).strip()


def get_lineageos():
    support = dict()
    temp_file = "/tmp/lineageos_devices.html"
    # using wget as lineageos.org blocks my request otherwise
    subprocess.run(["wget", "-O", temp_file, "https://wiki.lineageos.org/devices/"])

    with open(temp_file, "r") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    for vendor in soup.find_all("h2"):
        devices = vendor.find_next_sibling("div", class_="devices")
        for item in devices.find_all("div", class_="item"):
            if "discontinued" not in item.get("class"):
                span = item.find("span", class_="devicename")
                device_name = clean_name(vendor.text + " " + span.text)
                support[device_name] = "supported"

    return {"LineageOS": support}


def get_postmarketos():
    support = dict()

    with urllib.request.urlopen("https://wiki.postmarketos.org/wiki/Devices") as u:
        soup = BeautifulSoup(u.read(), "html.parser")

    for i, element in enumerate(soup.find_all("span", class_="mw-headline")):
        if i > 1:
            break

        status = element.text

        table = element.parent.find_next_sibling("table")
        tbody = table.find("tbody")
        tr_list = tbody.find_all("tr")
        for element in tr_list:
            device_name = clean_name(element.find("td").text)
            support[device_name] = status

    return {"postmarketOS": support}


def get_eos():
    support = dict()

    with urllib.request.urlopen("https://doc.e.foundation/devices") as u:
        soup = BeautifulSoup(u.read(), "html.parser")

    table = soup.find("table", class_="smartphone-table")
    tbody = table.find("tbody")
    tr_list = tbody.find_all("tr")
    for tr in tr_list:
        td_list = tr.find_all("td")
        vendor = td_list[0].text
        model = td_list[1].find("a").text
        device_name = clean_name(f"{vendor} {model}")
        li = td_list[2].find("li")
        status = re.sub(r"\s+", " ", li.text.strip())
        support[device_name] = status

    return {"/e/OS": support}


def get_ubuntutouch():
    support = dict()

    with urllib.request.urlopen("https://devices.ubuntu-touch.io/") as u:
        soup = BeautifulSoup(u.read(), "html.parser")

    li_list = soup.find_all("li", class_="device-name")
    for li in li_list:
        title = li.find("a").attrs.get("title")
        m = re.match(r"(.+) - Progress: ([0-9\.]+%)", title)
        if m:
            device_name = clean_name(m.group(1))
            status = m.group(2)
            support[device_name] = status

    return {"Ubuntu Touch": support}


def get_grapheneos():
    support = dict()

    with urllib.request.urlopen("https://grapheneos.org/faq") as u:
        soup = BeautifulSoup(u.read(), "html.parser")

    for article in soup.find_all("article"):
        if article.attrs.get("id") == "supported-devices":
            ul = article.find("ul")
            for li in ul.find_all("li"):
                device_name = clean_name(" ".join(li.text.split()[:-1]))
                support[device_name] = "supported"

            break

    return {"GrapheneOS": support}


def get_replicant():
    support = dict()

    with urllib.request.urlopen("https://replicant.us/supported-devices.php") as u:
        soup = BeautifulSoup(u.read(), "html.parser")

    for element in soup.find_all("h3"):
        status = element.text.split()[0]
        while True:
            element = element.find_next_sibling()
            if element.name != "div":
                break

            for img in element.find_all("img"):
                device_name = clean_name(img.attrs.get("alt", ""))
                support[device_name] = status

    return {"Replicant": support}


def get_calyxos():
    support = dict()

    with urllib.request.urlopen("https://calyxos.org/install/") as u:
        soup = BeautifulSoup(u.read(), "html.parser")

    for tr in soup.find("table").find_all("tr"):
        td = tr.find("td")
        if td:
            device_name = clean_name(td.text)
            support[device_name] = "supported"

    return {"CalyxOS": support}


def make_table_md(data):
    devices = set()
    for x in data.values():
        devices |= set(x.keys())

    devices = sorted(devices)

    distros = sorted(data.keys())
    md = "| | " + " | ".join(distros) + " |\n"
    md += "|-|" + "-|"*len(distros)

    for device in devices:
        md += "\n| " + device + " |"
        for distro in distros:
            if device in data[distro]:
                md += " " + data[distro][device] + " |"
            else:
                md += " |"

    md += "\n"
    return md


if __name__ == "__main__":
    support = dict()
    support |= get_calyxos()
    support |= get_eos()
    support |= get_grapheneos()
    support |= get_lineageos()
    support |= get_postmarketos()
    support |= get_replicant()
    support |= get_ubuntutouch()

    with open("markdown_start.md", "r") as f:
        md_start = f.read()

    with open("markdown_end.md", "r") as f:
        md_end = f.read()

    with open("README.md", "w") as f:
        f.write(md_start + "\n")
        f.write(make_table_md(support))
        f.write("\n" + md_end)
