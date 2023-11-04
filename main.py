import re

import praw
from ebooklib import epub

# BOOK PROPERTIES
TITLE = "Behold: Humanity - reddit version ch 461"
AUTHOR = "Ralts Bloodthorne"
LANGUAGE = "en"
IDENTIFIER = "test01"
FILENAME = "test.epub"

# SCAN PROPERTIES
STARTING_CHAPTER_BASE36 = "mizhcb"  # get that from reddit link, i.e. https://www.reddit.com/r/HFY/comments/mizhcb/first_contact_fourth_wave_chapter_461/
NUMBER_OF_CHAPTERS_TO_SCAN = 7

# APP PROPERTIES - SEE https://medium.com/geekculture/how-to-extract-reddit-posts-for-an-nlp-project-56d121b260b4
REDDIT_USERNAME = ""
REDDIT_PASSWORD = ""
APP_CLIENT_ID = ""
APP_SECRET = ""


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


def get_submission(reddit, base36):
    submission = reddit.submission(base36)

    title = submission.title
    selftext = submission.selftext
    link = re.search("next].*\/\)", selftext).group(0)[6:-1]
    next_base36 = re.search("comments\/.{6}", link).group(0)[9:]

    first_line_index = selftext.find('\n')
    last_line_index = selftext.rfind('\n')
    content = selftext[first_line_index + 2:last_line_index]

    return {"title": title, "content": content, "next_base36": next_base36}


#
# MAIN SCRIPT
#


reddit = praw.Reddit(username=REDDIT_USERNAME,
                     password=REDDIT_PASSWORD,
                     client_id=APP_CLIENT_ID,
                     client_secret=APP_SECRET,
                     user_agent="praw_scraper_1.0"
                     )

submission_base36 = STARTING_CHAPTER_BASE36
result = get_submission(reddit, submission_base36)
book = create_epub()
chapters = []

for i in range(NUMBER_OF_CHAPTERS_TO_SCAN):
    submission = get_submission(reddit, submission_base36)
    submission_base36 = submission["next_base36"]

    print("Title: " + submission["title"])

    chapter = create_chapter(i, submission["title"], submission["content"])
    chapters.append(chapter)
    book.add_item(chapter)

book.toc = chapters
book.spine = ["nav"] + chapters
epub.write_epub(FILENAME, book, {})  # https://www.amazon.com/gp/sendtokindle
