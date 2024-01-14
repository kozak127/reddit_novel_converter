import re

import praw
from ebooklib import epub

# BOOK PROPERTIES
TITLE = "Behold: Humanity - reddit ch 461-561"
AUTHOR = "Ralts Bloodthorne"
LANGUAGE = "en"
IDENTIFIER = "test01"
FILENAME = "test.epub"  # https://www.amazon.com/gp/sendtokindle

# SCAN PROPERTIES
STARTING_CHAPTER_BASE36 = "mizhcb"  # get that from reddit link, i.e. https://www.reddit.com/r/HFY/comments/mizhcb/first_contact_fourth_wave_chapter_461/
NUMBER_OF_CHAPTERS_TO_SCAN = 100
MISSING_LINKS = ["mpr25p", # Example values, remove before use. Used when author forgot to add "next" link. Add the BASE36 of the next chapter here. Order matters
                 "oc2mxr",
                 "ocnsg5"]

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


def create_chapter(number, title, content):
    chapter = epub.EpubHtml(title=title, file_name="chapter_" + str(number) + ".xhtml", lang="en")
    heading = "<h1>" + title + "</h1>"
    content_xhtml = convert_content_to_xhtml(content)
    chapter.content = (
            heading +
            content_xhtml
    )
    return chapter


def convert_content_to_xhtml(content):
    converted_paragraphs = []
    paragraphs = content.split("\n")
    for paragraph in paragraphs:
        if len(paragraph) > 0:
            paragraph = "<p>" + paragraph + "</p>\n"
            converted_paragraphs.append(paragraph)
    return "".join(converted_paragraphs)


def get_submission(reddit, base36, missing_link_count):
    submission = reddit.submission(base36)

    title = submission.title
    selftext = submission.selftext
    print(title + " -- " + base36)

    matched = re.search("next.*\/\)", selftext, re.IGNORECASE)
    if matched is not None:
        link = matched.group(0)[6:-1]
        next_base36 = re.search("comments\/.{7}", link).group(0)[9:]  # {6} for old reddit posts. {7} for new ones
        next_base36 = next_base36.strip("/")  # if old reddit post, remove trailing "/"
    else:
        try:
            print("### MISSING NEXT CHAPTER LINK IN " + submission.title + " -- " + base36)
            next_base36 = MISSING_LINKS[missing_link_count]
            print("### SUBSTITUTION TABLE INDEX: " + str(missing_link_count) + "; SUBSTITUTED WITH " + next_base36)
            missing_link_count = missing_link_count + 1
        except IndexError:
            print("### ADD MISSING BASE36 AT THE END OF THE TABLE")
            raise ValueError("Missing substitute BASE36 at the end of the MISSING_LINKS list")

    first_line_index = selftext.find('\n')
    last_line_index = selftext.rfind('\n')
    content = selftext[first_line_index + 2:last_line_index]

    return {"title": title, "content": content, "next_base36": next_base36, "missing_link_count": missing_link_count}


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
        submission = get_submission(reddit, submission_base36, missing_link_count)

        submission_base36 = submission["next_base36"]
        missing_link_count = submission["missing_link_count"]

        chapter = create_chapter(i, submission["title"], submission["content"])
        chapters.append(chapter)
        book.add_item(chapter)

    print("### SCAN FINISHED")

    print("### CREATING FILE")
    book.toc = chapters
    book.spine = ["nav"] + chapters
    epub.write_epub(FILENAME, book, {})  # https://www.amazon.com/gp/sendtokindle
    print("### FILE " + FILENAME + " CREATED")


main()
