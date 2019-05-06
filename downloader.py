import sys
import requests
import os
import time
from multiprocessing.pool import ThreadPool
from lxml import html

username = "nottheonion"
password = "Password1"

s = requests.Session()


def replace_uris(base_resp: str, uri) -> str:
    name = uri.split("/")[::-1][0]
    base_uri = uri.replace("map/" + name, "map/")
    split_resp = base_resp.split("\"")

    temp = [x for x in split_resp if base_uri in x]

    temp = [x.replace(base_uri, "") for x in temp]

    for x in temp:
        return base_resp.replace(base_uri + x + "\"", "chapters/" + x + ".html\"")


def download_and_check(uri: str):
    downloaded = False

    response = "0"

    name = uri.split("/")[::-1][0]

    path = "%s/chapters/%s.html" % (base, name)
    while not downloaded:

        if os.path.isfile(path):
            return

        try:
            response = s.get(uri).text

        except Exception as e:
            with open(base + "/log.txt", "a") as l_out:
                l_out.write(str(e) + "\n")

            response = "resource limitations"

        if "resource limitations" in response:
            print(name + " temporarily unavailable, trying again in 60 seconds..")
            time.sleep(60)
        else:
            downloaded = True

    print("got: ", name)

    base_uri = uri.replace("map/" + name, "map/")

    split_resp = response.split("\"")

    temp = [x.replace(base_uri, "") for x in split_resp if base_uri in x]

    for x in temp:
        response = response.replace(base_uri + x + "\"", x + ".html\"")

    response = response.replace(outline_link, "../outline.html")

    with open(path, "w") as f_out:
        f_out.write(response)


def sleep_timer(duration):
    for x in range(duration, 0, -1):
        time.sleep(1)
        print("== Sleeping ==", x, end="\r")


def convert_html(delimiter, html_file, filter_str):
    t = html.fromstring(html_file)

    ls = t.xpath(delimiter)

    matches = [x for x in set(ls) if filter_str in x]
    if len(matches) == 0:
        print("empty response, retrying..")
        sleep_timer(duration=60)
        convert_html(delimiter, html_file, filter_str)
    else:
        return matches


def validate_uri(uri: str):
    if "writing.com/main/interact/item_id/" not in uri:
        sys.exit("ERROR: not a valid writing.com interactive story")


def login():
    print("logging in to writing.com")
    s.post("https://www.writing.com/main/login.php",
           data={"login_username": username, "login_password": password, "send_to": "/"})


def fetch_story(uri: str):
    global base
    base = uri.split("/")[::-1][0]
    print(base)

    if not os.path.exists(base):
        os.makedirs(base + "/chapters")

    with open(base + "/log.txt", "w") as l_out:
        l_out.write(base + " start\n")

    begin = s.get(uri).text
    entry = convert_html("//a/@href", begin, "/map/")[0]

    temp = s.get(entry).text

    global outline_link
    outline_link = convert_html("//a/@href", temp, "/outline")[0]

    with open(base + "/begin.html", "w") as begin_out:
        begin_out.write(replace_uris(begin, entry))

    outline = s.get(outline_link).text

    list_str = convert_html("//a/@href", outline, "/map/")

    for x in list_str:
        outline = replace_uris(outline, x)

    with open(base + "/outline.html", "w") as outline_out:
        outline_out.write(outline)

    pool = ThreadPool()

    pool.map(download_and_check, list_str)


def main():
    uris = sys.argv[1:]
    for uri in uris:
        validate_uri(uri)

    login()

    story_num = 0

    for uri in uris:
        story_num += 1

        print("Fetching story %s of %s" % (story_num, len(uris)))

        fetch_story(uri)


if __name__ == '__main__':
    main()
