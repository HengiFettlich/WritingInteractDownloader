import sys
import requests
import os
import time
from multiprocessing.pool import ThreadPool
from lxml import html

username = "nottheonion"
password = "Password1"

# Session to store login cookies
s = requests.Session()


# replaces the given uri in a html response. turns these into relative paths
# there could be better ways to do that
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

    # chapter name
    name = uri.split("/")[::-1][0]

    # save dir, inside chapters
    path = "%s/chapters/%s.html" % (base, name)
    while not downloaded:
        # don't redownload files, if running the script twice
        if os.path.isfile(path):
            return

        try:
            response = s.get(uri).text
        # in case of SSL exceptions or something else, log these
        except Exception as e:
            with open(base + "/log.txt", "a") as l_out:
                l_out.write(str(e) + "\n")

            response = "resource limitations"
        # either happens if an Exception is thrown or if writing.com goofs up
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
        print("== Sleeping ==", str(x).zfill(2), end="\r")


def convert_html(delimiter, html_file, filter_str):
    t = html.fromstring(html_file)

    ls = t.xpath(delimiter)

    matches = [x for x in set(ls) if filter_str in x]

    # failsafe if writing.com throws resource errors. chapter list will be empty if that happens
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
    # login is needed to view the outline
    # default login uses generic username from bugmenot.com
    print("logging in to writing.com")
    s.post("https://www.writing.com/main/login.php",
           data={"login_username": username, "login_password": password, "send_to": "/"})


def fetch_story(uri: str):
    # remove last slash if present
    if uri[::-1][0] == "/":
        uri = uri[:-1]

    if "/map/1" in uri:
        uri = uri.replace("/map/1", "")

    # base is used throughout the whole project as the base directory
    global base
    # this should correspond to the Id and name of the story.
    base = uri.split("/")[::-1][0]
    print(base)

    # creates base dir and chapter directory.
    if not os.path.exists(base):
        os.makedirs(base + "/chapters")
    # TODO implement basic logging mechanics
    with open(base + "/log.txt", "w") as l_out:
        l_out.write(base + " start\n")

    begin = s.get(uri).text
    entry = convert_html("//a/@href", begin, "/map/")[0]

    temp = s.get(entry).text

    # outline link will be replaced in the chapters to make the story browsable
    global outline_link
    outline_link = convert_html("//a/@href", temp, "/outline")[0]

    with open(base + "/begin.html", "w") as begin_out:
        begin_out.write(replace_uris(begin, entry))

    outline = s.get(outline_link).text

    # chapter list
    chapter_list = convert_html("//a/@href", outline, "/map/")

    # makes the outline browsable by replacing all chapter links with their relative path
    for chapter in chapter_list:
        outline = replace_uris(outline, chapter)

    with open(base + "/outline.html", "w") as outline_out:
        outline_out.write(outline)

    # multiprocess it because why not
    pool = ThreadPool()

    pool.map(download_and_check, chapter_list)


# main loop
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
