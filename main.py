import re

import praw
from ebooklib import epub

# BOOK PROPERTIES
TITLE = "The Human Artificial Hivemind 51-100"
AUTHOR = "Storms_Wrath"
LANGUAGE = "en"
IDENTIFIER = "test01"
FILENAME = "The Human Artificial Hivemind 51-100.epub"  # https://www.amazon.com/gp/sendtokindle

# SCAN PROPERTIES
STARTING_CHAPTER_BASE36 = "spmz6j"  # get that from reddit link, i.e. https://www.reddit.com/r/HFY/comments/  -->spmz6j<--  /the_human_artificial_hivemind_part_51_alien/
NUMBER_OF_CHAPTERS_TO_SCAN = 50  # do not use more than 999
# Example values, remove before use. Used when author forgot to add "next" link. Add the BASE36 of the next chapter here. Order matters
MISSING_LINKS = [
]

# CHAPTER NAMES
CHAPTER_CUT_OUT_PREFIX = True  # True/False
CHAPTER_PREFIX_REGEX = "The Human Artificial Hivemind Part [0-9]*: "

# APP PROPERTIES - SEE https://medium.com/geekculture/how-to-extract-reddit-posts-for-an-nlp-project-56d121b260b4
REDDIT_USERNAME = ""
REDDIT_PASSWORD = ""
APP_CLIENT_ID = ""
APP_SECRET = ""

################################
# DO NOT TOUCH THE STUFF BELOW #
################################


def create_epub():
    book = epub.EpubBook()
    book.set_identifier(IDENTIFIER)
    book.set_title(TITLE)
    book.set_language(LANGUAGE)
    book.add_author(AUTHOR)

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    style = "BODY {color: white;}"
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style,
    )
    book.add_item(nav_css)

    return book


def create_chapter(number, raw_title, content):
    title = clean_title(raw_title)
    chapter = epub.EpubHtml(title=title, file_name="chapter_" + str(number) + ".xhtml", lang="en")
    heading = "<h1>" + title + "</h1>"
    content_xhtml = convert_content_to_xhtml(content)
    chapter.content = (
            heading +
            content_xhtml
    )
    return chapter


def clean_title(raw_title):
    if not CHAPTER_CUT_OUT_PREFIX:
        return raw_title
    return re.sub(CHAPTER_PREFIX_REGEX, "", raw_title)


def convert_content_to_xhtml(content):
    converted_paragraphs = []
    paragraphs = content.split("\n")
    for paragraph in paragraphs:
        if len(paragraph) > 0:
            paragraph = "<p>" + paragraph + "</p>\n"
            converted_paragraphs.append(paragraph)
    return "".join(converted_paragraphs)


def get_submission(number, reddit, base36):
    submission = reddit.submission(base36)

    title = submission.title
    raw = submission.selftext
    print("{:03d}".format(number) + "/" + "{:03d}".format(NUMBER_OF_CHAPTERS_TO_SCAN) + " -- " + base36 + " -- " + title)

    first_line_index = raw.find('\n')
    last_line_index = raw.rfind('\n')
    content = raw[first_line_index + 2:last_line_index]

    return {"base36": base36, "title": title, "content": content, "raw": raw}


def get_next_submission_pointer(submission, missing_link_count):
    raw_submission = submission["raw"]
    matched = re.search("\[next\]\(https:\/\/www\.reddit\.com\/r\/.{3}\/comments\/.{7}", raw_submission, re.IGNORECASE)
    if matched is None:
        return get_missing_link(missing_link_count, submission)

    link = matched.group(0)
    next_base36 = link[-7:]  # extract the base36 from the link. old ones have length of 6, new ones have 7
    next_base36 = next_base36.strip("/")  # if old reddit post, remove trailing "/"
    return {"next_base36": next_base36, "missing_link_count": missing_link_count}


def get_missing_link(missing_link_count, submission):
    try:
        print("### MISSING NEXT CHAPTER LINK IN " + submission["title"] + " -- " + submission["base36"])
        next_base36 = MISSING_LINKS[missing_link_count]
        print("### MISSING LINK TABLE INDEX: " + str(missing_link_count) + "; SUBSTITUTED WITH " + next_base36)
        missing_link_count = missing_link_count + 1
        return {"next_base36": next_base36, "missing_link_count": missing_link_count}
    except IndexError:
        print("### ERROR - ADD APPROPRIATE BASE36 AT THE END OF THE MISSING_LINKS TABLE")
        print("### ERROR - CLOSING THE APPLICATION")
        sys.exit()


def main():
    reddit = praw.Reddit(username=REDDIT_USERNAME,
                         password=REDDIT_PASSWORD,
                         client_id=APP_CLIENT_ID,
                         client_secret=APP_SECRET,
                         user_agent="praw_scraper_1.0"
                         )

    submission_base36 = STARTING_CHAPTER_BASE36
    missing_link_count = 0
    book = create_epub()
    chapters = []

    print("### START SCAN")

    # MAIN SCAN LOOP
    for i in range(1, NUMBER_OF_CHAPTERS_TO_SCAN + 1):
        submission = get_submission(i, reddit, submission_base36)

        chapter = create_chapter(i, submission["title"], submission["content"])
        chapters.append(chapter)
        book.add_item(chapter)

        if i != NUMBER_OF_CHAPTERS_TO_SCAN:
            pointer = get_next_submission_pointer(submission, missing_link_count)
            submission_base36 = pointer["next_base36"]
            missing_link_count = pointer["missing_link_count"]

    print("### SCAN FINISHED")

    print("### CREATING FILE")
    book.toc = chapters
    book.spine = ["nav"] + chapters
    epub.write_epub(FILENAME, book, {})
    print("### FILE " + FILENAME + " CREATED")


main()
